import pytest

from engine.orchestration.registry import AgentRegistry
from engine.tools.policy import ToolPolicy


def test_registry_fails_closed_for_unregistered_agents():
    registry = AgentRegistry()
    with pytest.raises(LookupError):
        registry.resolve("manus")


def test_registry_rejects_duplicate_agent_keys():
    registry = AgentRegistry()
    marker = object()
    registry.register("manus", marker)
    with pytest.raises(ValueError):
        registry.register("MANUS", marker)


def test_high_risk_upstream_tools_require_explicit_approval():
    policy = ToolPolicy(enabled_tools={
        "bash", "python_execute", "browser_use",
        "workspace_restore_version", "str_replace_editor",
    })
    for tool in (
        "bash", "python_execute", "browser_use",
        "workspace_restore_version", "str_replace_editor",
    ):
        decision = policy.evaluate(tool)
        assert decision.allowed is True
        assert decision.requires_approval is True


def test_unregistered_tools_are_denied():
    assert ToolPolicy().evaluate("google_search").allowed is False


@pytest.mark.asyncio
async def test_tool_dispatch_validates_catalog_schema_before_handler():
    from engine.tools.registry import PolicyEnforcedToolRegistry

    registry = PolicyEnforcedToolRegistry(ToolPolicy(enabled_tools={"planning"}, approved_tools={"planning"}))
    called = []

    async def handler(arguments, *, run_id, user_id):
        called.append(arguments)
        return "ok"

    registry.register("planning", handler)
    with pytest.raises(ValueError, match="missing_command"):
        await registry.execute("planning", {}, run_id="run-1", user_id="user-1")
    assert called == []


@pytest.mark.asyncio
async def test_tool_dispatch_executes_only_after_policy_and_schema_pass():
    from engine.tools.registry import PolicyEnforcedToolRegistry

    registry = PolicyEnforcedToolRegistry(ToolPolicy(enabled_tools={"planning"}, approved_tools={"planning"}))

    async def handler(arguments, *, run_id, user_id):
        assert run_id == "run-2"
        assert user_id == "user-2"
        return arguments["command"]

    registry.register("planning", handler)
    assert await registry.execute("planning", {"command": "get"}, run_id="run-2", user_id="user-2") == "get"


@pytest.mark.asyncio
async def test_tool_dispatch_rejects_unapproved_tool_before_handler():
    from engine.tools.registry import PolicyEnforcedToolRegistry

    registry = PolicyEnforcedToolRegistry(ToolPolicy(enabled_tools={"python_execute"}))

    async def handler(arguments, *, run_id, user_id):
        raise AssertionError("must not execute")

    registry.register("python_execute", handler)
    with pytest.raises(PermissionError, match="approval_gate_not_configured"):
        await registry.execute("python_execute", {"code": "print(1)"}, run_id="run-3", user_id="user-3")


def test_high_risk_tool_is_allowed_only_when_enabled_and_explicitly_approved():
    pending = ToolPolicy(enabled_tools={"python_execute"}).evaluate("python_execute")
    assert pending.allowed is True
    assert pending.requires_approval is True
    decision = ToolPolicy(
        enabled_tools={"python_execute"}, approved_tools={"python_execute"},
    ).evaluate("python_execute")
    assert decision.allowed is True
    assert decision.requires_approval is False


@pytest.mark.asyncio
async def test_workspace_editor_requires_owner_approval_before_handler():
    from engine.tools.registry import PolicyEnforcedToolRegistry

    registry = PolicyEnforcedToolRegistry(
        ToolPolicy(enabled_tools={"str_replace_editor"}),
        approval_gate=lambda *_: _deny_approval(),
    )
    called = []

    async def handler(arguments, *, run_id, user_id, workspace_id=None):
        called.append(arguments)
        return "saved"

    registry.register("str_replace_editor", handler)
    with pytest.raises(PermissionError, match="approval_denied_expired_or_already_consumed"):
        await registry.execute(
            "str_replace_editor",
            {"path": "src/main.py", "old_str": "old", "new_str": "new"},
            run_id="run-4", user_id="user-4", workspace_id="workspace-4",
        )
    assert called == []


async def _deny_approval():
    return False

def test_workspace_reader_is_enabled_only_by_workspace_runtime_and_needs_no_write_approval():
    disabled = ToolPolicy().evaluate("workspace_read_file")
    assert disabled.allowed is False

    enabled = ToolPolicy(enabled_tools={"workspace_read_file"}).evaluate("workspace_read_file")
    assert enabled.allowed is True
    assert enabled.requires_approval is False

