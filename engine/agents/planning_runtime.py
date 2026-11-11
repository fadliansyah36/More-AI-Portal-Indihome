from __future__ import annotations

import json
from typing import Any, Protocol

from engine.agents.protocol import AgentRunContext, AgentRunResult, AgentRuntime, CheckpointWriter


class PlanningGateway(Protocol):
    async def complete(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "planning", workspace_id: str | None = None, partner_id: str | None = None) -> dict[str, Any]: ...


class PlanningStore(Protocol):
    async def create(self, *, run_id: str, title: str, steps: list[dict[str, Any]]) -> dict[str, Any]: ...
    async def get(self, *, run_id: str) -> dict[str, Any]: ...
    async def mark_step(self, *, run_id: str, step_index: int, status: str, notes: str | None = None, output: dict[str, Any] | None = None) -> dict[str, Any]: ...


class PlanningAgentRuntime(AgentRuntime):
    """OpenManus PlanningFlow adapted to durable, resumable per-run state."""

    def __init__(self, *, gateway: PlanningGateway, store: PlanningStore, step_executor: AgentRuntime):
        self.gateway = gateway
        self.store = store
        self.step_executor = step_executor

    @staticmethod
    def _validate_steps(steps: Any) -> list[dict[str, Any]]:
        if not isinstance(steps, list) or not 1 <= len(steps) <= 100:
            raise RuntimeError("planning_model_returned_invalid_steps")
        validated: list[dict[str, Any]] = []
        allowed_risks = {"low", "medium", "high", "critical"}
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                raise RuntimeError("planning_step_must_be_object")
            objective, expected, tool = step.get("objective"), step.get("expected_output"), step.get("tool_requirement")
            risk, dependencies, usage = step.get("risk"), step.get("dependencies", []), step.get("estimated_usage", {})
            if not all(isinstance(value, str) and value.strip() for value in (objective, expected, tool)):
                raise RuntimeError("planning_step_required_fields_missing")
            if risk not in allowed_risks or not isinstance(dependencies, list):
                raise RuntimeError("planning_step_policy_metadata_invalid")
            if any(not isinstance(dep, int) or isinstance(dep, bool) or dep < 0 or dep >= index for dep in dependencies):
                raise RuntimeError("planning_step_dependency_must_reference_prior_step")
            if len(set(dependencies)) != len(dependencies):
                raise RuntimeError("planning_step_dependency_duplicate")
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
        return validated

    async def _new_plan(self, context: AgentRunContext, prompt: str) -> tuple[str, list[dict[str, Any]]]:
        response = await self.gateway.complete(
            user_id=context.user_id, run_id=context.run_id,
            request_key=f"{context.run_id}:planning", task_type="planning",
            workspace_id=context.workspace_id,
            messages=[
                {"role": "system", "content": "Create a concise executable plan. Return only JSON: {title:string, steps:[{objective:string, dependencies:number[], expected_output:string, tool_requirement:string, risk:low|medium|high|critical, estimated_usage:{input_tokens:number,output_tokens:number}}]}. Dependencies must reference earlier step indexes. Do not execute the task."},
                {"role": "user", "content": prompt[:50_000]},
            ],
        )
        try:
            plan = json.loads(response["text"])
            title = str(plan["title"]).strip()[:500]
            steps = self._validate_steps(plan["steps"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError("planning_model_returned_invalid_schema") from exc
        if not title:
            raise RuntimeError("planning_model_returned_invalid_title")
        await self.store.create(run_id=context.run_id, title=title, steps=steps)
        return title, steps

    async def execute(self, context: AgentRunContext, payload: dict[str, Any], checkpoint: CheckpointWriter, cancelled: Any) -> AgentRunResult:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("planning_prompt_required")

        # Rehydrate a persisted plan before calling the model. A worker restart must
        # not silently create a new plan or replay already completed steps.
        persisted = await self.store.get(run_id=context.run_id)
        rows = persisted.get("steps", []) if isinstance(persisted, dict) else []
        manifest = context.recovery_checkpoints.get("planning.manifest", {})
        if rows:
            if not isinstance(manifest, dict) or not isinstance(manifest.get("title"), str):
                raise RuntimeError("planning_manifest_missing_for_persisted_steps")
            expected_count = manifest.get("step_count")
            if not isinstance(expected_count, int) or expected_count != len(rows):
                raise RuntimeError("planning_persisted_step_set_incomplete")
            rows = sorted(rows, key=lambda row: int(row.get("sequence") or 0))
            steps = self._validate_steps([row.get("input") for row in rows])
            title = manifest["title"][:500]
        else:
            if manifest:
                raise RuntimeError("planning_manifest_exists_without_persisted_steps")
            title, steps = await self._new_plan(context, prompt)
            persisted = await self.store.get(run_id=context.run_id)
            rows = sorted(persisted.get("steps", []), key=lambda row: int(row.get("sequence") or 0))
            if len(rows) != len(steps):
                raise RuntimeError("planning_step_persistence_incomplete")

        results: list[dict[str, Any]] = []
        states = {int(row["sequence"]) - 1: row for row in rows}
        for index, step in enumerate(steps):
            if cancelled.is_set():
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="cancelled")
                break

            prior = states.get(index, {})
            prior_status = prior.get("status")
            if prior_status == "succeeded":
                output = prior.get("output") if isinstance(prior.get("output"), dict) else {}
                results.append({"step": index, "status": "succeeded", "output": output})
                continue
            if prior_status in {"cancelled", "skipped"}:
                continue

            dependencies = step["dependencies"]
            if any(states.get(dep, {}).get("status") != "succeeded" for dep in dependencies):
                raise RuntimeError("planning_step_dependency_not_satisfied")

            if step["risk"] in {"high", "critical"} or step["tool_requirement"] not in {"none", "llm", "planning"}:
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="waiting_approval", notes="approval_or_sandbox_required")
                await checkpoint("planning.step.waiting_approval", {
                    "step_index": index, "risk": step["risk"], "tool_requirement": step["tool_requirement"],
                })
                raise PermissionError("planning_step_requires_approval_or_enabled_sandbox")

            await self.store.mark_step(run_id=context.run_id, step_index=index, status="running")
            await checkpoint("planning.step.started", {
                "step_index": index, "objective": step["objective"][:500], "risk": step["risk"],
            })
            try:
                result = await self.step_executor.execute(
                    context,
                    {"prompt": step["objective"] + "\nExpected output: " + step["expected_output"], "planning_step": index},
                    checkpoint, cancelled,
                )
                if cancelled.is_set():
                    await self.store.mark_step(run_id=context.run_id, step_index=index, status="cancelled")
                    break
                safe_output = result.output if isinstance(result.output, dict) else {"result": str(result.output)[:20_000]}
                await self.store.mark_step(
                    run_id=context.run_id, step_index=index, status="succeeded",
                    notes="Step execution confirmed", output=safe_output,
                )
                results.append({"step": index, "status": "succeeded", "output": safe_output})
                await checkpoint("planning.step.completed", {"step_index": index, "status": "succeeded"})
            except Exception as exc:
                await self.store.mark_step(run_id=context.run_id, step_index=index, status="failed", notes=type(exc).__name__)
                raise

        completed = sum(1 for row in results if row["status"] == "succeeded")
        return AgentRunResult({"title": title, "steps": results, "completed_steps": completed, "total_steps": len(steps)})
