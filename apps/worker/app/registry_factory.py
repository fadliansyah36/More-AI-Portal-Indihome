from __future__ import annotations

import os

from apps.sandbox.app.runner import DockerSandbox
from app.client import WorkerRpcClient
from app.llm_gateway import create_metered_gateway
from app.memory_store import SupabaseConversationMemoryStore
from app.plan_store import SupabasePlanStore
from app.sandbox_tools import IsolatedSandboxToolAdapter
from engine.agents.durable_tool_runtime import DurableOpenManusRuntime
from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.orchestration.registry import AgentRegistry


def build_agent_registry(client: WorkerRpcClient, http_client) -> AgentRegistry:
    gateway = create_metered_gateway(client, http_client)
    plan_store = SupabasePlanStore(client)
    memory_store = SupabaseConversationMemoryStore(client)
    sandbox_image = os.getenv("MOREAI_SANDBOX_IMAGE", "")
    sandbox_tools = None
    if "@sha256:" in sandbox_image:
        # Handlers are attached only to an immutable image. ToolPolicy keeps them
        # hidden/default-denied until a server-side approval adapter is supplied.
        sandbox_tools = IsolatedSandboxToolAdapter(DockerSandbox(image=sandbox_image))
    manus = DurableOpenManusRuntime(
        gateway, memory_store=memory_store, sandbox_tools=sandbox_tools,
    )
    planning = PlanningAgentRuntime(gateway=gateway, store=plan_store, step_executor=manus)

    registry = AgentRegistry()
    registry.register("manus", manus)
    registry.register("planning", planning)
    return registry
