import json

import httpx
import pytest

from app.sandbox_tools import IsolatedSandboxToolAdapter
from engine.tools.policy import ToolPolicy
from engine.tools.registry import PolicyEnforcedToolRegistry


def _adapter():
    return IsolatedSandboxToolAdapter(
        service_url="https://sandbox.internal.example",
        service_token="s" * 40,
        http=httpx.AsyncClient(),
        api_url="https://api.example.com",
        internal_token="i" * 40,
        worker_id="worker-test-01",
        workspace_tools=object(),
    )


@pytest.mark.asyncio
async def test_dispatcher_requires_approval_before_sandbox_execution():
    adapter = _adapter()
    calls = []

    async def execute(arguments, *, run_id, user_id, workspace_id=None, tool_call_id=None):
        calls.append((arguments, run_id, user_id, workspace_id, tool_call_id))
        return "isolated"

    adapter.python_execute = execute
    registry = PolicyEnforcedToolRegistry(
        ToolPolicy(enabled_tools={"python_execute"}),
        approval_gate=None,
    )
    registry.register("python_execute", adapter.python_execute)
    with pytest.raises(PermissionError, match="approval_gate_not_configured"):
        await registry.execute(
            "python_execute", {"code": "print(1)"}, run_id="run-00000001", user_id="user-0000001",
        )
    assert calls == []


@pytest.mark.asyncio
async def test_dispatcher_consumes_approval_before_sandbox_execution():
    adapter = _adapter()
    calls = []
    approvals = []

    async def execute(arguments, *, run_id, user_id, workspace_id=None, tool_call_id=None):
        calls.append((arguments, run_id, user_id, workspace_id, tool_call_id))
        return json.dumps({"isolated": True, "exit_code": 0})

    async def approved(run_id, user_id, tool_key, arguments):
        approvals.append((run_id, user_id, tool_key, arguments))
        return True

    adapter.python_execute = execute
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
    assert approvals[0][2] == "python_execute"
    assert calls[0][0]["timeout_seconds"] == 7
    assert json.loads(result)["isolated"] is True
