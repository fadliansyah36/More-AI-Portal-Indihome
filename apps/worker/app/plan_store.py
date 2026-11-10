from __future__ import annotations

from typing import Any

from app.client import WorkerRpcClient


class SupabasePlanStore:
    """Durable planning state backed by agent_run_steps and worker checkpoints."""

    def __init__(self, client: WorkerRpcClient, *, user_id: str):
        self.client = client
        self.user_id = user_id

    async def create(self, *, run_id: str, title: str, steps: list[str]) -> dict[str, Any]:
        await self.client.checkpoint(run_id, "planning.manifest", {"title": title[:500], "step_count": len(steps)})
        existing = await self.client.select("agent_run_steps", {
            "run_id": f"eq.{run_id}", "select": "sequence,step_key,status", "order": "sequence.asc", "limit": "200",
        })
        existing_keys = {row["step_key"] for row in existing}
        for index, description in enumerate(steps, start=1):
            key = f"planning.step.{index}"
            if key in existing_keys:
                continue
            await self.client.insert("agent_run_steps", {
                "run_id": run_id,
                "sequence": index,
                "step_key": key,
                "status": "pending",
                "input": {"description": description[:10_000]},
            })
        return await self.get(run_id=run_id)

    async def get(self, *, run_id: str) -> dict[str, Any]:
        rows = await self.client.select("agent_run_steps", {
            "run_id": f"eq.{run_id}", "step_key": "like.planning.step.%",
            "select": "sequence,step_key,status,input,output,error,started_at,finished_at",
            "order": "sequence.asc", "limit": "200",
        })
        return {"run_id": run_id, "steps": rows}

    async def mark_step(self, *, run_id: str, step_index: int, status: str, notes: str | None = None) -> dict[str, Any]:
        allowed = {"pending", "running", "waiting_approval", "succeeded", "failed", "skipped", "cancelled"}
        if status not in allowed:
            raise ValueError("invalid_plan_step_status")
        sequence = step_index + 1
        payload: dict[str, Any] = {"status": status}
        if status == "running":
            payload["started_at"] = datetime.now(timezone.utc).isoformat()
        if status in {"succeeded", "failed", "skipped", "cancelled"}:
            payload["finished_at"] = datetime.now(timezone.utc).isoformat()
        if notes:
            payload["output" if status == "succeeded" else "error"] = {"summary": notes[:2000]}
        rows = await self.client.update("agent_run_steps", {
            "run_id": f"eq.{run_id}", "sequence": f"eq.{sequence}", "step_key": f"eq.planning.step.{sequence}",
        }, payload)
        if not rows:
            raise LookupError("planning_step_not_found")
        return rows[0]
