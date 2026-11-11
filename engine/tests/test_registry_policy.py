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


def test_high_risk_upstream_tools_are_default_denied():
    policy = ToolPolicy(enabled_tools={"bash", "python_execute", "browser_use"})
    for tool in ("bash", "python_execute", "browser_use"):
        decision = policy.evaluate(tool)
        assert decision.allowed is False
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

    registry = PolicyEnforcedToolRegistry(ToolPolicy(enabled_tools={"planning"}))

    async def handler(arguments, *, run_id, user_id):
        raise AssertionError("must not execute")

    registry.register("planning", handler)
    with pytest.raises(PermissionError):
        await registry.execute("planning", {"command": "get"}, run_id="run-3", user_id="user-3")


def test_high_risk_tool_is_allowed_only_when_enabled_and_explicitly_approved():
    assert ToolPolicy(enabled_tools={"python_execute"}).evaluate("python_execute").allowed is False
    decision = ToolPolicy(
        enabled_tools={"python_execute"}, approved_tools={"python_execute"},
    ).evaluate("python_execute")
    assert decision.allowed is True
    assert decision.requires_approval is False
