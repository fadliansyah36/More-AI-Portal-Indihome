from __future__ import annotations

import asyncio
import base64
import os
import re
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .runner import DockerSandbox, SandboxLimits

app = FastAPI(title="MoreAI Isolated Execution Supervisor", version="0.1.0")
_active: dict[str, tuple[asyncio.Task, str, str]] = {}


class ExecutionRequest(BaseModel):
    request_id: str = Field(min_length=16, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    language: Literal["python", "bash"]
    source: str = Field(min_length=1, max_length=8_000_000)
    timeout_seconds: int = Field(default=30, ge=1, le=120)
    workspace_files: dict[str, str] = Field(default_factory=dict)


class CancellationRequest(BaseModel):
    request_id: str = Field(min_length=16, max_length=128)
    run_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)


def _authorize(value: str | None) -> None:
    token = os.getenv("MOREAI_SANDBOX_SERVICE_TOKEN", "")
    if len(token) < 32 or value != f"Bearer {token}":
        raise HTTPException(401, "sandbox_supervisor_unauthorized")


def _sandbox() -> DockerSandbox:
    if os.getenv("MOREAI_SANDBOX_SUPERVISOR_ENABLED", "false").lower() != "true":
        raise HTTPException(503, "sandbox_supervisor_disabled")
    image = os.getenv("MOREAI_SANDBOX_IMAGE", "")
    if not re.fullmatch(r".+@sha256:[0-9a-fA-F]{64}", image):
        raise HTTPException(503, "sandbox_image_digest_not_configured")
    return DockerSandbox(image=image)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "moreai-execution-supervisor"}


@app.get("/ready")
async def ready(authorization: str | None = Header(default=None)):
    _authorize(authorization)
    sandbox = _sandbox()
    await sandbox.check_ready()
    return {
        "status": "ready",
        "isolated_runner": True,
        "network_disabled": True,
        "digest_pinned_image": True,
    }


@app.post("/v1/execute")
async def execute(
    body: ExecutionRequest,
    authorization: str | None = Header(default=None),
):
    _authorize(authorization)
    if body.request_id in _active:
        raise HTTPException(409, "sandbox_request_already_active")
    sandbox = _sandbox()
    task = asyncio.current_task()
    if task is None:
        raise HTTPException(503, "sandbox_task_context_unavailable")
    _active[body.request_id] = (task, body.run_id, body.user_id)
    try:
        result = await sandbox.execute(
            body.source,
            language=body.language,
            limits=SandboxLimits(timeout_seconds=body.timeout_seconds),
        )
        return {
            "request_id": body.request_id,
            "run_id": body.run_id,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
            "isolated": True,
        }
    except asyncio.CancelledError:
        raise
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(503, "sandbox_execution_unavailable") from exc
    finally:
        _active.pop(body.request_id, None)


@app.post("/v1/cancel")
async def cancel(
    body: CancellationRequest,
    authorization: str | None = Header(default=None),
):
    _authorize(authorization)
    active = _active.get(body.request_id)
    if active is None:
        return {"cancelled": False, "status": "not_active"}
    task, run_id, user_id = active
    if run_id != body.run_id or user_id != body.user_id:
        raise HTTPException(404, "sandbox_execution_not_found")
    task.cancel()
    return {"cancelled": True, "status": "cancellation_requested"}
