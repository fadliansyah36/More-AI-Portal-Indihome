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
# Live cancellation handles only; durable receipts and workspace state remain in FastAPI/Supabase.
_active: dict[tuple[str, str, str], asyncio.Task] = {}
_active_lock = asyncio.Lock()


def _capacity_limits() -> tuple[int, int]:
    try:
        per_customer = int(os.getenv("MOREAI_SANDBOX_MAX_ACTIVE_PER_CUSTOMER", "2"))
        global_limit = int(os.getenv("MOREAI_SANDBOX_MAX_ACTIVE_GLOBAL", "16"))
    except ValueError as exc:
        raise HTTPException(503, "sandbox_capacity_configuration_invalid") from exc
    if not 1 <= per_customer <= 8 or not per_customer <= global_limit <= 64:
        raise HTTPException(503, "sandbox_capacity_configuration_invalid")
    return per_customer, global_limit


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
    per_customer_limit, global_limit = _capacity_limits()
    active_key = (body.user_id, body.run_id, body.request_id)
    async with _active_lock:
        if active_key in _active:
            raise HTTPException(409, "sandbox_request_already_active")
        customer_active = sum(1 for user_id, _, _ in _active if user_id == body.user_id)
        if customer_active >= per_customer_limit or len(_active) >= global_limit:
            raise HTTPException(429, "sandbox_execution_capacity_exceeded")
    if len(body.workspace_files) > 200:
        raise HTTPException(413, "sandbox_workspace_file_count_exceeded")
    snapshot = {}
    snapshot_bytes = 0
    for path, encoded in body.workspace_files.items():
        if not isinstance(path, str) or not isinstance(encoded, str):
            raise HTTPException(422, "sandbox_workspace_snapshot_invalid")
        if len(encoded) > 2_666_668:
            raise HTTPException(413, "sandbox_workspace_file_too_large")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, "sandbox_workspace_snapshot_invalid") from exc
        snapshot_bytes += len(raw)
        if snapshot_bytes > 2_000_000:
            raise HTTPException(413, "sandbox_workspace_snapshot_too_large")
        snapshot[path] = raw
    sandbox = _sandbox()
    task = asyncio.current_task()
    if task is None:
        raise HTTPException(503, "sandbox_task_context_unavailable")
    async with _active_lock:
        customer_active = sum(1 for user_id, _, _ in _active if user_id == body.user_id)
        if active_key in _active:
            raise HTTPException(409, "sandbox_request_already_active")
        if customer_active >= per_customer_limit or len(_active) >= global_limit:
            raise HTTPException(429, "sandbox_execution_capacity_exceeded")
        _active[active_key] = task
    try:
        result = await sandbox.execute(
            body.source,
            language=body.language,
            workspace_files=snapshot,
            limits=SandboxLimits(timeout_seconds=body.timeout_seconds),
            tenant_id=body.user_id,
            run_id=body.run_id,
            request_id=body.request_id,
        )
        return {
            "request_id": body.request_id,
            "run_id": body.run_id,
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
            "isolated": True,
            "workspace_files": {
                path: base64.b64encode(raw).decode("ascii")
                for path, raw in result.workspace_files.items()
            },
        }
    except asyncio.CancelledError:
        raise
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(503, "sandbox_execution_unavailable") from exc
    finally:
        async with _active_lock:
            _active.pop(active_key, None)


@app.post("/v1/cancel")
async def cancel(
    body: CancellationRequest,
    authorization: str | None = Header(default=None),
):
    _authorize(authorization)
    active_key = (body.user_id, body.run_id, body.request_id)
    async with _active_lock:
        task = _active.get(active_key)
        if task is None:
            return {"cancelled": False, "status": "not_active"}
        task.cancel()
    return {"cancelled": True, "status": "cancellation_requested"}
