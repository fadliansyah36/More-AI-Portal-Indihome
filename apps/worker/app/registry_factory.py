import os

from app.client import WorkerRpcClient
from app.sandbox_tools import IsolatedSandboxToolAdapter
from apps.sandbox.app.runner import DockerSandbox
from app.llm_gateway import create_metered_gateway
from app.memory_store import SupabaseConversationMemoryStore
from app.plan_store import SupabasePlanStore
from engine.agents.durable_tool_runtime import DurableOpenManusRuntime
from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.orchestration.registry import AgentRegistry


def build_agent_registry(client: WorkerRpcClient, http_client) -> AgentRegistry:
    gateway = create_metered_gateway(client, http_client)
    plan_store = SupabasePlanStore(client)
    memory_store = SupabaseConversationMemoryStore(client)
    sandbox_tools = None
    sandbox_enabled = os.getenv("MOREAI_SANDBOX_ENABLED", "false").lower() == "true"
    sandbox_gate_passed = os.getenv("MOREAI_SANDBOX_RELEASE_GATE_PASSED", "false").lower() == "true"
    if sandbox_enabled and sandbox_gate_passed:
        image = os.getenv("MOREAI_SANDBOX_IMAGE", "")
        if "@sha256:" not in image:
            raise RuntimeError("sandbox_enabled_requires_digest_pinned_MOREAI_SANDBOX_IMAGE")
        sandbox_tools = IsolatedSandboxToolAdapter(DockerSandbox(image=image))
    manus = DurableOpenManusRuntime(
        gateway,
        memory_store=memory_store,
        plan_store=plan_store,
        sandbox_tools=sandbox_tools,
        approval_gate=client.wait_for_tool_approval if sandbox_tools is not None else None,
    )
    planning = PlanningAgentRuntime(gateway=gateway, store=plan_store, step_executor=manus)

    registry = AgentRegistry()
    registry.register("manus", manus)
    registry.register("planning", planning)
    # Bash/Python are registered only when both explicit sandbox activation and the
    # independent release-gate flag are true; the dispatcher then requires a consumed approval.
    return registry
