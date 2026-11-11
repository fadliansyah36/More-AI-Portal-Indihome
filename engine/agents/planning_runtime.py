from __future__ import annotations

import json
from typing import Any, Protocol

from engine.agents.protocol import AgentRunContext, AgentRunResult, AgentRuntime, CheckpointWriter


class PlanningGateway(Protocol):
    async def complete(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "planning", workspace_id: str | None = None, partner_id: str | None = None) -> dict[str, Any]: ...


class PlanningStore(Protocol):
    async def create(self, *, run_id: str, title: str, steps: list[dict[str, Any]]) -> dict[str, Any]: ...
    async def mark_step(self, *, run_id: str, step_index: int, status: str, notes: str | None = None) -> dict[str, Any]: ...


class PlanningAgentRuntime(AgentRuntime):
    """OpenManus planning agent with schema-validated, durable and auditable steps."""

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
            workspace_id=context.workspace_id,
            messages=[
                {"role": "system", "content": "Create a concise, executable plan. Return only JSON: {title:string, steps:[{objective:string, dependencies:number[], expected_output:string, tool_requirement:string, risk:low|medium|high|critical, estimated_usage:{input_tokens:number,output_tokens:number}}]}. Dependencies must reference earlier step indexes. Do not execute the task."},
                {"role": "user", "content": prompt[:50_000]},
            ],
        )
        try:
            plan = json.loads(plan_response["text"])
            title = str(plan["title"]).strip()[:500]
            steps = plan["steps"]
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("planning_model_returned_invalid_schema") from exc
        if not title or not isinstance(steps, list) or not 1 <= len(steps) <= 100:
            raise RuntimeError("planning_model_returned_invalid_steps")

        validated: list[dict[str, Any]] = []
        allowed_risks = {"low", "medium", "high", "critical"}
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise RuntimeError("planning_step_must_be_object")
            objective = step.get("objective")
            expected = step.get("expected_output")
            tool = step.get("tool_requirement")
            risk = step.get("risk")
            dependencies = step.get("dependencies", [])
            usage = step.get("estimated_usage", {})
            if not all(isinstance(value, str) and value.strip() for value in (objective, expected, tool)):
                raise RuntimeError("planning_step_required_fields_missing")
            if risk not in allowed_risks or not isinstance(dependencies, list):
                raise RuntimeError("planning_step_policy_metadata_invalid")
            if any(not isinstance(dep, int) or dep < 0 or dep >= index for dep in dependencies):
                raise RuntimeError("planning_step_dependency_must_reference_prior_step")
            if not isinstance(usage, dict) or any(not isinstance(usage.get(key, 0), int) or usage.get(key, 0) < 0 for key in ("input_tokens", "output_tokens")):
                raise RuntimeError("planning_step_usage_estimate_invalid")
            validated.append({
                "objective": objective.strip()[:10_000],
                "dependencies": dependencies,
                "expected_output": expected.strip()[:5_000],
                "tool_requirement": tool.strip()[:200],
                "risk": risk,
                "estimated_usage": {"input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)},
            })

        await self.store.create(run_id=context.run_id, title=title, steps=validated)
        results: list[dict[str, Any]] = []
        for index, step in enumerate(validated):
            if cancelled.is_set():
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="cancelled")
                break
            if step["risk"] in {"high", "critical"} or step["tool_requirement"] not in {"none", "llm", "planning"}:
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="failed", notes="approval_or_sandbox_required")
                raise PermissionError("planning_step_requires_unavailable_approval_or_sandbox")
            await self.store.mark_step(run_id=context.run_id, step_index=index, status="running")
            await checkpoint("planning.step.started", {"step_index": index, "objective": step["objective"][:500], "risk": step["risk"]})
            try:
                result = await self.step_executor.execute(
                    context, {"prompt": step["objective"] + "\nExpected output: " + step["expected_output"], "planning_step": index}, checkpoint, cancelled,
                )
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="succeeded", notes="Step execution confirmed")
                results.append({"step": index, "status": "succeeded", "output": result.output})
            except Exception as exc:
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="failed", notes=type(exc).__name__)
                raise
        return AgentRunResult({"title": title, "steps": results, "completed_steps": len(results)})
