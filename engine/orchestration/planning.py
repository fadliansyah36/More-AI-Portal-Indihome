from __future__ import annotations

from typing import Any, Protocol
import asyncio

from engine.agents.protocol import AgentRunContext, AgentRuntime


class DurablePlanningStore(Protocol):
    async def create(self, *, run_id: str, title: str, steps: list[str]) -> dict[str, Any]: ...
    async def get(self, *, run_id: str) -> dict[str, Any]: ...
    async def mark_step(self, *, run_id: str, step_index: int, status: str, notes: str | None = None) -> dict[str, Any]: ...


class PlanningFlow:
    """Durable replacement for the upstream in-memory PlanningFlow plan dictionary."""

    def __init__(self, *, planning_store: DurablePlanningStore, executors: dict[str, AgentRuntime], default_executor: str):
        if default_executor not in executors:
            raise ValueError("Default planning executor is not registered")
        self.planning_store = planning_store
        self.executors = executors
        self.default_executor = default_executor

    async def execute(self, *, context: AgentRunContext, title: str, steps: list[str], checkpoint: Any, cancelled: asyncio.Event) -> list[dict[str, Any]]:
        if not steps or len(steps) > 100:
            raise ValueError("Planning flow requires between 1 and 100 steps")
        await self.planning_store.create(run_id=context.run_id, title=title, steps=steps)
        results: list[dict[str, Any]] = []
        for index, step in enumerate(steps):
            if cancelled.is_set():
                break
            await self.planning_store.mark_step(run_id=context.run_id, step_index=index, status="in_progress")
            try:
                executor = self.executors[self.default_executor]
                result = await executor.execute(
                    context,
                    {"prompt": step, "step_index": index},
                    checkpoint,
                    cancelled,
                )
                results.append({"step": index, "status": "completed", "output": result.output})
                await self.planning_store.mark_step(run_id=context.run_id, step_index=index, status="completed")
            except Exception as exc:
                await self.planning_store.mark_step(run_id=context.run_id, step_index=index, status="blocked", notes=type(exc).__name__)
                raise
        return results
