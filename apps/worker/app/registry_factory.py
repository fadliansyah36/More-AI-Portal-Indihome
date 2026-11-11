from app.client import WorkerRpcClient
from app.llm_gateway import create_metered_gateway
from app.memory_store import SupabaseConversationMemoryStore
from app.plan_store import SupabasePlanStore
from engine.agents.gateway_runtime import GatewayManusRuntime
from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.orchestration.registry import AgentRegistry


def build_agent_registry(client: WorkerRpcClient, http_client) -> AgentRegistry:
    gateway = create_metered_gateway(client, http_client)
    plan_store = SupabasePlanStore(client)
    memory_store = SupabaseConversationMemoryStore(client)
    manus = GatewayManusRuntime(gateway, memory_store=memory_store)
    planning = PlanningAgentRuntime(gateway=gateway, store=plan_store, step_executor=manus)

    registry = AgentRegistry()
    registry.register("manus", manus)
    registry.register("planning", planning)
    # SWE, Bash, Python, browser, editor and process tools remain disabled until
    # their isolated supervisors, approvals and durable audit adapters are wired.
    return registry
