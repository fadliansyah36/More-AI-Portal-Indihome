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

def test_high_risk_tool_requires_isolated_runtime_even_with_approval():
    policy = ToolPolicy(
        enabled_tools={"python_execute"},
        approved_tools={"python_execute"},
    )
    decision = policy.evaluate("python_execute")
    assert decision.allowed is False
    assert decision.requires_approval is True
    assert decision.reason == "isolated_runtime_not_ready"


def test_high_risk_tool_requires_explicit_approval_after_isolation():
    policy = ToolPolicy(
        enabled_tools={"python_execute"},
        isolated_runtime_tools={"python_execute"},
    )
    decision = policy.evaluate("python_execute")
    assert decision.allowed is False
    assert decision.reason == "explicit_approval_required"


def test_high_risk_tool_can_only_pass_both_gates():
    policy = ToolPolicy(
        enabled_tools={"python_execute"},
        approved_tools={"python_execute"},
        isolated_runtime_tools={"python_execute"},
    )
    decision = policy.evaluate("python_execute")
    assert decision.allowed is True
    assert decision.requires_approval is False
