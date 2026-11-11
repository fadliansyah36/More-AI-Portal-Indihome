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
    """OpenManus PlanningFlow semantics on durable, replayable MoreAI run state."""

    def __init__(self, *, gateway: PlanningGateway, store: PlanningStore, step_executor: AgentRuntime):
        self.gateway, self.store, self.step_executor = gateway, store, step_executor

    @staticmethod
    def _validate_steps(raw_steps: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_steps, list) or not 1 <= len(raw_steps) <= 100:
            raise RuntimeError("planning_model_returned_invalid_steps")
        allowed_risks = {"low", "medium", "high", "critical"}
        validated=[]
        for index, step in enumerate(raw_steps):
            if not isinstance(step, dict):
                raise RuntimeError("planning_step_must_be_object")
            objective, expected, tool, risk = (step.get(k) for k in ("objective","expected_output","tool_requirement","risk"))
            dependencies=step.get("dependencies",[])
            usage=step.get("estimated_usage",{})
            if not all(isinstance(v,str) and v.strip() for v in (objective,expected,tool)):
                raise RuntimeError("planning_step_required_fields_missing")
            if risk not in allowed_risks or not isinstance(dependencies,list):
                raise RuntimeError("planning_step_policy_metadata_invalid")
            if any(isinstance(dep,bool) or not isinstance(dep,int) or dep<0 or dep>=index for dep in dependencies) or len(set(dependencies))!=len(dependencies):
                raise RuntimeError("planning_step_dependency_must_reference_unique_prior_steps")
            if not isinstance(usage,dict) or any(isinstance(usage.get(k,0),bool) or not isinstance(usage.get(k,0),int) or usage.get(k,0)<0 for k in ("input_tokens","output_tokens")):
                raise RuntimeError("planning_step_usage_estimate_invalid")
            validated.append({
                "objective":objective.strip()[:10000],"dependencies":dependencies,
                "expected_output":expected.strip()[:5000],"tool_requirement":tool.strip()[:200],
                "risk":risk,"estimated_usage":{"input_tokens":usage.get("input_tokens",0),"output_tokens":usage.get("output_tokens",0)},
            })
        return validated

    async def _new_plan(self, context: AgentRunContext, prompt: str) -> tuple[str,list[dict[str,Any]]]:
        response=await self.gateway.complete(
            user_id=context.user_id,run_id=context.run_id,request_key=f"{context.run_id}:planning",
            task_type="planning",workspace_id=context.workspace_id,
            messages=[
                {"role":"system","content":"Create a concise executable plan. Return only JSON {title:string,steps:[{objective:string,dependencies:number[],expected_output:string,tool_requirement:string,risk:low|medium|high|critical,estimated_usage:{input_tokens:number,output_tokens:number}}]}. Dependencies must reference earlier step indexes. Do not execute the task."},
                {"role":"user","content":prompt[:50000]},
            ],
        )
        try:
            raw=json.loads(response["text"])
            title=raw["title"]
            if not isinstance(title,str) or not title.strip(): raise ValueError("title")
            steps=self._validate_steps(raw["steps"])
        except (KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
            raise RuntimeError("planning_model_returned_invalid_schema") from exc
        await self.store.create(run_id=context.run_id,title=title.strip()[:500],steps=steps)
        return title.strip()[:500],steps

    async def execute(self, context: AgentRunContext, payload: dict[str, Any], checkpoint: CheckpointWriter, cancelled: Any) -> AgentRunResult:
        prompt=payload.get("prompt")
        if not isinstance(prompt,str) or not prompt.strip(): raise ValueError("planning_prompt_required")
        states=dict(context.recovery_checkpoints or {})
        manifest=states.get("planning.manifest")
        if isinstance(manifest,dict):
            persisted=await self.store.get(run_id=context.run_id)
            rows=persisted.get("steps") if isinstance(persisted,dict) else None
            if not isinstance(rows,list) or len(rows)!=manifest.get("step_count"):
                raise RuntimeError("planning_persisted_manifest_mismatch")
            title=manifest.get("title")
            if not isinstance(title,str) or not title.strip(): raise RuntimeError("planning_manifest_invalid")
            steps=[]
            for row in rows:
                source=row.get("input") if isinstance(row,dict) else None
                if not isinstance(source,dict): raise RuntimeError("planning_persisted_step_invalid")
                steps.append(source)
            steps=self._validate_steps(steps)
        else:
            existing=await self.store.get(run_id=context.run_id)
            if existing.get("steps"):
                raise RuntimeError("planning_orphaned_steps_without_manifest")
            title,steps=await self._new_plan(context,prompt)
            manifest={"title":title,"step_count":len(steps)}

        rows_by_index={int(row["sequence"])-1:row for row in (await self.store.get(run_id=context.run_id)).get("steps",[])}
        results=[]
        completed=set()
        for index,step in enumerate(steps):
            row=rows_by_index.get(index,{})
            status=row.get("status","pending")
            if status=="succeeded":
                output=row.get("output") if isinstance(row.get("output"),dict) else {}
                results.append({"step":index,"status":"succeeded","output":output})
                completed.add(index)
                continue
            if status in {"failed","cancelled"}:
                raise RuntimeError("planning_run_contains_terminal_incomplete_step")
            if cancelled.is_set():
                await self.store.mark_step(run_id=context.run_id,step_index=index,status="cancelled")
                break
            if any(dep not in completed for dep in step["dependencies"]):
                raise RuntimeError("planning_dependency_not_satisfied")
            if step["risk"] in {"high","critical"} or step["tool_requirement"] not in {"none","llm","planning"}:
                await self.store.mark_step(run_id=context.run_id,step_index=index,status="waiting_approval",notes="approval_or_sandbox_required")
                await checkpoint("planning.step.waiting_approval",{"step_index":index,"risk":step["risk"]})
                raise PermissionError("planning_step_requires_approval_or_sandbox")
            await self.store.mark_step(run_id=context.run_id,step_index=index,status="running")
            await checkpoint(f"planning.step.{index}.started",{"step_index":index,"objective":step["objective"][:500]})
            try:
                result=await self.step_executor.execute(
                    context,{"prompt":step["objective"]+"\nExpected output: "+step["expected_output"],"planning_step":index},
                    checkpoint,cancelled,
                )
                await self.store.mark_step(run_id=context.run_id,step_index=index,status="succeeded",notes="Step execution confirmed",output=result.output)
                await checkpoint(f"planning.step.{index}.completed",{"step_index":index,"status":"succeeded"})
                results.append({"step":index,"status":"succeeded","output":result.output})
                completed.add(index)
            except Exception as exc:
                await self.store.mark_step(run_id=context.run_id,step_index=index,status="failed",notes=type(exc).__name__)
                raise
        return AgentRunResult({"title":title,"steps":results,"completed_steps":len(completed)})
