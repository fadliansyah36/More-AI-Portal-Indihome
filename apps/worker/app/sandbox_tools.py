from __future__ import annotations

import json
from typing import Any

from apps.sandbox.app.runner import DockerSandbox, SandboxLimits


class IsolatedSandboxToolAdapter:
    """Worker-to-Docker adapter. Approval is enforced centrally by the tool dispatcher."""

    def __init__(self, sandbox: DockerSandbox):
        self.sandbox = sandbox

    async def _execute(
        self, *, source: str, language: str, timeout_seconds: int = 30,
    ) -> str:
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
            source=arguments["code"], language="python",
            timeout_seconds=int(arguments.get("timeout_seconds", 30)),
        )

    async def bash(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        return await self._execute(
            source=arguments["command"], language="bash", timeout_seconds=30,
        )
