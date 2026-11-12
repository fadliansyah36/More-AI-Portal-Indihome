import os

from app.client import WorkerRpcClient
from app.sandbox_tools import IsolatedSandboxToolAdapter
from apps.sandbox.app.runner import DockerSandbox
from app.llm_gateway import create_metered_gateway
from app.memory_store import SupabaseConversationMemoryStore
from app.knowledge_tools import SupabaseKnowledgeTools
from app.plan_store import SupabasePlanStore
from engine.agents.durable_tool_runtime import DurableOpenManusRuntime
from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.tools.search_provider import TavilySearchAdapter
from engine.tools.storage import SupabaseArtifactTool
from engine.tools.workspace import SupabaseWorkspaceTool
from apps.sandbox.app.browser_supervisor import BrowserSupervisor
from engine.orchestration.registry import AgentRegistry
from engine.orchestration.flows import FlowFactory


def build_agent_registry(client: WorkerRpcClient, http_client) -> AgentRegistry:
    gateway = create_metered_gateway(client, http_client)
    plan_store = SupabasePlanStore(client)
    memory_store = SupabaseConversationMemoryStore(client)
    knowledge_tools = SupabaseKnowledgeTools(client, http_client) if os.getenv("MOREAI_EMBEDDING_BASE_URL") and os.getenv("MOREAI_EMBEDDING_MODEL") else None
    search_tools = TavilySearchAdapter(http_client) if os.getenv("TAVILY_API_KEY") else None
    # The default bucket is provisioned by the Phase 05 migration; deployments may override it.
    storage_tools = SupabaseArtifactTool(client) if os.getenv("MOREAI_ARTIFACTS_BUCKET", "moreai-artifacts") else None
    workspace_tools = SupabaseWorkspaceTool(client) if os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts") else None
    browser_tools = None
    if os.getenv("MOREAI_BROWSER_ENABLED", "false").lower() == "true":
        service_url = os.getenv("MOREAI_BROWSER_SERVICE_URL", "")
        service_token = os.getenv("MOREAI_BROWSER_SERVICE_TOKEN", "")
        egress_enforced = os.getenv("MOREAI_BROWSER_EGRESS_ENFORCED", "false").lower() == "true"
        if not service_url or not service_token or not egress_enforced:
            raise RuntimeError("browser_activation_requires_isolated_supervisor_and_network_egress_enforcement")
        browser_tools = BrowserSupervisor(service_url=service_url, service_token=service_token, egress_enforced=egress_enforced, http=http_client)
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
        knowledge_tools=knowledge_tools,
        plan_store=plan_store,
        search_tools=search_tools,
        storage_tools=storage_tools,
        workspace_tools=workspace_tools,
        browser_tools=browser_tools,
        event_publisher=client.append_run_event,
        sandbox_tools=sandbox_tools,
        # Browser and sandbox capabilities are independently high-risk. Any enabled high-risk tool\n        # must have the durable owner-approval gate, regardless of which adapter is enabled.\n        approval_gate=client.wait_for_tool_approval,
        tool_timeout_seconds=float(os.getenv("MOREAI_TOOL_TIMEOUT_SECONDS", "120")),
    )
    flow_factory = FlowFactory()
    # OpenManus PlanningFlow is adapted to the durable MoreAI plan store and
    # resumable run/checkpoint contract; upstream process-global log/plan state
    # is intentionally not carried into the worker.
    flow_factory.register(
        "planning",
        lambda **deps: PlanningAgentRuntime(**deps),
    )
    planning = flow_factory.create(
        "planning", gateway=gateway, store=plan_store, step_executor=manus,
        approval_gate=client.wait_for_tool_approval,
    )

    registry = AgentRegistry()
    registry.register("manus", manus)
    registry.register("planning", planning)
    # Bash/Python are registered only when both explicit sandbox activation and the
    # independent release-gate flag are true; the dispatcher then requires a consumed approval.
    return registry
