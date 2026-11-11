from app.client import WorkerRpcClient
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
    manus = DurableOpenManusRuntime(gateway, memory_store=memory_store)
    planning = PlanningAgentRuntime(gateway=gateway, store=plan_store, step_executor=manus)

    registry = AgentRegistry()
    registry.register("manus", manus)
    registry.register("planning", planning)
    # Sandbox adapters are implemented separately, but are deliberately not
    # registered in production until approval, supervisor, and threat-model gates pass.
    return registry
