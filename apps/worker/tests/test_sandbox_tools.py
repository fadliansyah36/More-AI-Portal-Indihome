import pytest

from app.sandbox_tools import IsolatedSandboxToolAdapter
from apps.sandbox.app.runner import SandboxResult
from engine.tools.policy import ToolPolicy
from engine.tools.registry import PolicyEnforcedToolRegistry


class FakeSandbox:
    def __init__(self):
        self.calls = []

    async def execute(self, source, *, language, limits):
        self.calls.append((source, language, limits))
        return SandboxResult(0, "isolated-output", "", False)


@pytest.mark.asyncio
async def test_dispatcher_requires_approval_before_sandbox_execution():
    sandbox = FakeSandbox()
    adapter = IsolatedSandboxToolAdapter(sandbox)
    registry = PolicyEnforcedToolRegistry(
        ToolPolicy(enabled_tools={"python_execute"}),
        approval_gate=None,
    )
    registry.register("python_execute", adapter.python_execute)
    with pytest.raises(PermissionError, match="approval_gate_not_configured"):
        await registry.execute(
            "python_execute", {"code": "print(1)"}, run_id="run-00000001", user_id="user-0000001",
        )
    assert sandbox.calls == []


@pytest.mark.asyncio
async def test_dispatcher_consumes_approval_before_sandbox_execution():
    sandbox = FakeSandbox()
    adapter = IsolatedSandboxToolAdapter(sandbox)
    approvals = []

    async def approved(run_id, user_id, tool_key, arguments):
        approvals.append((run_id, user_id, tool_key, arguments))
        return True

    registry = PolicyEnforcedToolRegistry(
        ToolPolicy(enabled_tools={"python_execute"}),
        approval_gate=approved,
    )
    registry.register("python_execute", adapter.python_execute)
    result = await registry.execute(
        "python_execute", {"code": "print(1)", "timeout_seconds": 7},
        run_id="run-00000001", user_id="user-0000001",
    )
    assert len(approvals) == 1
    assert sandbox.calls[0][1] == "python"
    assert sandbox.calls[0][2].timeout_seconds == 7
    assert '"isolated":true' in result
