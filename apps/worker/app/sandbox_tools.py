from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from apps.sandbox.app.runner import DockerSandbox, SandboxLimits


ApprovalCheck = Callable[[str, str, str, dict[str, Any]], Awaitable[bool]]


class IsolatedSandboxToolAdapter:
    """Worker-to-Docker adapter; execution requires an external, run-scoped approval."""

    def __init__(
        self, sandbox: DockerSandbox,
        approval_check: ApprovalCheck | None = None,
    ):
        self.sandbox = sandbox
        self.approval_check = approval_check

    async def _execute(
        self, *, tool_key: str, source: str, language: str,
        run_id: str, user_id: str, arguments: dict[str, Any], timeout_seconds: int = 30,
    ) -> str:
        if self.approval_check is None or not await self.approval_check(run_id, user_id, tool_key, arguments):
            raise PermissionError("sandbox_execution_approval_required")
        result = await self.sandbox.execute(
            source, language=language,
            limits=SandboxLimits(timeout_seconds=timeout_seconds),
        )
        return json.dumps({
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
            "isolated": True,
        }, ensure_ascii=False, separators=(",", ":"))

    async def python_execute(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        return await self._execute(
            tool_key="python_execute", source=arguments["code"], language="python",
            run_id=run_id, user_id=user_id, arguments=arguments,
            timeout_seconds=int(arguments.get("timeout_seconds", 30)),
        )

    async def bash(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        return await self._execute(
            tool_key="bash", source=arguments["command"], language="bash",
            run_id=run_id, user_id=user_id, arguments=arguments, timeout_seconds=30,
        )
