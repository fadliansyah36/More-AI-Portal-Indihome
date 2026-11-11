from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.runtime import AgentDispatcher, Checkpoint
from engine.agents.protocol import AgentRunContext
from engine.orchestration.registry import AgentRegistry


CheckpointLoader = Callable[[str], Awaitable[dict[str, dict[str, Any]]]]


class RegisteredAgentDispatcher(AgentDispatcher):
    """Dispatches durable Supabase runs and restores their checkpoint state before execution."""

    def __init__(self, registry: AgentRegistry, checkpoint_loader: CheckpointLoader | None = None):
        self.registry = registry
        self.checkpoint_loader = checkpoint_loader

    async def dispatch(self, run: dict[str, Any], checkpoint: Checkpoint, cancelled: asyncio.Event) -> dict[str, Any]:
        run_id = str(run.get("id") or "")
        user_id = str(run.get("user_id") or "")
        payload = run.get("input") or {}
        if not run_id or not user_id or not isinstance(payload, dict):
            raise ValueError("invalid_durable_run_payload")
        agent_key = payload.get("agent_key", "manus")
        if not isinstance(agent_key, str):
            raise ValueError("invalid_agent_key")
        runtime = self.registry.resolve(agent_key)
        restored = await self.checkpoint_loader(run_id) if self.checkpoint_loader else {}
        if not isinstance(restored, dict):
            raise RuntimeError("run_checkpoint_restore_failed")
        context = AgentRunContext(
            run_id=run_id,
            user_id=user_id,
            workspace_id=str(run["workspace_id"]) if run.get("workspace_id") else None,
            conversation_id=str(run["conversation_id"]) if run.get("conversation_id") else None,
            agent_definition_id=str(run["agent_definition_id"]) if run.get("agent_definition_id") else None,
            attempt=int(run.get("attempt") or 0),
            max_attempts=int(run.get("max_attempts") or 3),
            recovery_checkpoints=restored,
        )
        result = await runtime.execute(context, payload, checkpoint, cancelled)
        return result.output
