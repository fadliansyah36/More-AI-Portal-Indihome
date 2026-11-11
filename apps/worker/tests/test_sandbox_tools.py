import asyncio

import pytest

from app.sandbox_tools import IsolatedSandboxToolAdapter
from apps.sandbox.app.runner import SandboxResult


class FakeSandbox:
    def __init__(self):
        self.calls = []

    async def execute(self, source, *, language, limits):
        self.calls.append((source, language, limits))
        return SandboxResult(0, "isolated-output", "", False)


@pytest.mark.asyncio
async def test_sandbox_adapter_requires_run_scoped_approval_before_execution():
    sandbox = FakeSandbox()
    adapter = IsolatedSandboxToolAdapter(sandbox)
    with pytest.raises(PermissionError, match="approval_required"):
        await adapter.python_execute({"code": "print(1)"}, run_id="run-1", user_id="user-1")
    assert sandbox.calls == []


@pytest.mark.asyncio
async def test_sandbox_adapter_executes_python_only_after_approval():
    sandbox = FakeSandbox()

    async def approved(run_id, user_id, tool_key):
        return (run_id, user_id, tool_key) == ("run-1", "user-1", "python_execute")

    adapter = IsolatedSandboxToolAdapter(sandbox, approval_check=approved)
    result = await adapter.python_execute(
        {"code": "print(1)", "timeout_seconds": 7}, run_id="run-1", user_id="user-1",
    )
    assert sandbox.calls[0][1] == "python"
    assert sandbox.calls[0][2].timeout_seconds == 7
    assert '"isolated":true' in result
