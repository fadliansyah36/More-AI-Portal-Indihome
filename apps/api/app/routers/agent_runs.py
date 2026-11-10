from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.dependencies import current_user
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/agent-runs", tags=["agent-runs"])


async def _event_with_checkpoint_state(repo, run_id: UUID, row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") or {}
    checkpoint_key = payload.get("checkpoint_key") if isinstance(payload, dict) else None
    if isinstance(checkpoint_key, str):
        checkpoints = await repo.select("agent_run_checkpoints", {
            "run_id": f"eq.{run_id}", "checkpoint_key": f"eq.{checkpoint_key}",
            "select": "checkpoint_key,state,created_at", "limit": "1",
        })
        if checkpoints:
            row = {**row, "checkpoint": checkpoints[0].get("state")}
    return row


@router.get("")
async def list_runs(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await repository(request).select("agent_runs", {
        "user_id": f"eq.{user['id']}",
        "select": "id,conversation_id,status,input,output,error,attempt,max_attempts,created_at,started_at,finished_at",
        "order": "created_at.desc", "limit": "100",
    })


@router.get("/{run_id}")
async def get_run(run_id: UUID, request: Request, user: dict[str, Any] = Depends(current_user)):
    return await repository(request).owned_record("agent_runs", run_id, user["id"])


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: UUID, request: Request, user: dict[str, Any] = Depends(current_user)):
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])
    return await repo.rpc("moreai_worker_request_cancel", {"p_run_id": str(run_id), "p_user_id": user["id"]})


@router.get("/{run_id}/events")
async def get_events(run_id: UUID, request: Request, after: int = 0, user: dict[str, Any] = Depends(current_user)):
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])
    rows = await repo.select("agent_run_events", {
        "run_id": f"eq.{run_id}", "sequence": f"gt.{max(after, 0)}",
        "select": "id,event_type,sequence,payload,created_at", "order": "sequence.asc", "limit": "500",
    })
    return [await _event_with_checkpoint_state(repo, run_id, row) for row in rows]


@router.get("/{run_id}/stream")
async def stream_events(run_id: UUID, request: Request, after: int = 0, user: dict[str, Any] = Depends(current_user)):
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])

    async def events():
        cursor = max(after, 0)
        idle_rounds = 0
        while idle_rounds < 120:
            if await request.is_disconnected():
                break
            rows = await repo.select("agent_run_events", {
                "run_id": f"eq.{run_id}", "sequence": f"gt.{cursor}",
                "select": "id,event_type,sequence,payload,created_at", "order": "sequence.asc", "limit": "100",
            })
            if rows:
                idle_rounds = 0
                for raw in rows:
                    row = await _event_with_checkpoint_state(repo, run_id, raw)
                    cursor = max(cursor, int(row["sequence"]))
                    payload = json.dumps(row, separators=(",", ":"))
                    yield f"id: {cursor}\nevent: {row['event_type']}\ndata: {payload}\n\n"
            else:
                idle_rounds += 1
                run = await repo.owned_record("agent_runs", run_id, user["id"])
                status = run.get("status")
                if status in {"succeeded", "failed", "cancelled", "expired"}:
                    terminal_event = "run.completed" if status == "succeeded" else "run.cancelled" if status == "cancelled" else "run.failed"
                    payload = json.dumps({"run_id": str(run_id), "status": status, "output": run.get("output"), "error": run.get("error")}, separators=(",", ":"))
                    yield f"id: {cursor}\nevent: {terminal_event}\ndata: {payload}\n\n"
                    return
                yield ": keep-alive\n\n"
            await asyncio.sleep(1)
        yield "event: stream.timeout\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })
