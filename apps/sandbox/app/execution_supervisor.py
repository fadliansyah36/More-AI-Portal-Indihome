from __future__ import annotations

import os
import re
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .runner import DockerSandbox, SandboxLimits

app = FastAPI(title="MoreAI Isolated Execution Supervisor", version="0.1.0")


class ExecutionRequest(BaseModel):
    run_id: str = Field(min_length=1, max_length=128)
    user_id: str = Field(min_length=1, max_length=128)
    language: Literal["python", "bash"]
    source: str = Field(min_length=1, max_length=8_000_000)
    timeout_seconds: int = Field(default=30, ge=1, le=120)


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
    sandbox._validate()
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
    sandbox = _sandbox()
    try:
        result = await sandbox.execute(
            body.source,
            language=body.language,
            limits=SandboxLimits(timeout_seconds=body.timeout_seconds),
        )
    except (ValueError, RuntimeError) as exc:
        # Do not return runtime details, image references or host configuration.
        raise HTTPException(503, "sandbox_execution_unavailable") from exc
    return {
        "run_id": body.run_id,
        "exit_code": result.exit_code,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": result.timed_out,
        "isolated": True,
    }
