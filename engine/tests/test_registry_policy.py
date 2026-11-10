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
