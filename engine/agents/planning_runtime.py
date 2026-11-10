from __future__ import annotations

import json
from typing import Any, Protocol

from engine.agents.protocol import AgentRunContext, AgentRunResult, AgentRuntime, CheckpointWriter


class PlanningGateway(Protocol):
    async def complete(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "planning", workspace_id: str | None = None, partner_id: str | None = None) -> dict[str, Any]: ...


class PlanningStore(Protocol):
    async def create(self, *, run_id: str, title: str, steps: list[str]) -> dict[str, Any]: ...
    async def mark_step(self, *, run_id: str, step_index: int, status: str, notes: str | None = None) -> dict[str, Any]: ...


class PlanningAgentRuntime(AgentRuntime):
    """OpenManus planning agent with durable plan steps and an injected safe executor."""

    def __init__(self, *, gateway: PlanningGateway, store: PlanningStore, step_executor: AgentRuntime):
        self.gateway = gateway
        self.store = store
        self.step_executor = step_executor

    async def execute(self, context: AgentRunContext, payload: dict[str, Any], checkpoint: CheckpointWriter, cancelled: Any) -> AgentRunResult:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("planning_prompt_required")
        plan_response = await self.gateway.complete(
            user_id=context.user_id,
            run_id=context.run_id,
            request_key=f"{context.run_id}:planning",
            task_type="planning",
            messages=[
                {"role": "system", "content": "Create a concise execution plan. Return only valid JSON with keys title and steps; steps must be an array of actionable strings. Do not execute the task."},
                {"role": "user", "content": prompt[:50_000]},
            ],
        )
        try:
            plan = json.loads(plan_response["text"])
            title = str(plan["title"]).strip()[:500]
            steps = plan["steps"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("planning_model_returned_invalid_schema") from exc
        if not title or not isinstance(steps, list) or not 1 <= len(steps) <= 100 or any(not isinstance(step, str) or not step.strip() for step in steps):
            raise RuntimeError("planning_model_returned_invalid_steps")
        steps = [step.strip()[:10_000] for step in steps]
        await self.store.create(run_id=context.run_id, title=title, steps=steps)
        results: list[dict[str, Any]] = []
        for index, step in enumerate(steps):
            if cancelled.is_set():
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="cancelled")
                break
            await self.store.mark_step(run_id=context.run_id, step_index=index, status="running")
            await checkpoint("planning.step.started", {"step_index": index, "title": step[:500]})
            try:
                result = await self.step_executor.execute(
                    context, {"prompt": step, "planning_step": index}, checkpoint, cancelled,
                )
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="succeeded", notes="Step execution confirmed")
                results.append({"step": index, "status": "succeeded", "output": result.output})
            except Exception as exc:
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="failed", notes=type(exc).__name__)
                raise
        return AgentRunResult({"title": title, "steps": results, "completed_steps": len(results)})
