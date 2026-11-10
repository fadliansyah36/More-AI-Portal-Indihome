from app.client import WorkerRpcClient
from app.llm_gateway import create_metered_gateway
from app.plan_store import SupabasePlanStore
from engine.agents.gateway_runtime import GatewayManusRuntime
from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.orchestration.registry import AgentRegistry


def build_agent_registry(client: WorkerRpcClient, http_client) -> AgentRegistry:
    gateway = create_metered_gateway(client, http_client)
    plan_store = SupabasePlanStore(client)
    manus = GatewayManusRuntime(gateway)
    planning = PlanningAgentRuntime(gateway=gateway, store=plan_store, step_executor=manus)

    registry = AgentRegistry()
    registry.register("manus", manus)
    registry.register("planning", planning)
    # SWE, Bash, Python, browser, editor and process tools are intentionally not registered.
    return registry
