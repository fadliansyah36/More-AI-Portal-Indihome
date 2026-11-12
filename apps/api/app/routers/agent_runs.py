from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query, Header, HTTPException
from fastapi.responses import StreamingResponse

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/agent-runs", tags=["agent-runs"])


def _event_cursor(after: int, last_event_id: str | None) -> int:
    """Honor EventSource reconnection cursors without accepting malformed IDs."""
    if last_event_id is None or not last_event_id.strip():
        return max(after, 0)
    try:
        header_cursor = int(last_event_id.strip(), 10)
    except ValueError as exc:
        raise HTTPException(400, "Last-Event-ID must be a non-negative integer") from exc
    if header_cursor < 0:
        raise HTTPException(400, "Last-Event-ID must be a non-negative integer")
    return max(after, header_cursor)


async def _event_with_checkpoint_state(repo, run_id: UUID, row: dict[str, Any]) -> dict[str, Any]:
    payload = row.get("payload") or {}
    checkpoint_key = payload.get("checkpoint_key") if isinstance(payload, dict) else None
    if isinstance(checkpoint_key, str):
        checkpoints = await repo.select("agent_run_checkpoints", {
            "run_id": f"eq.{run_id}", "checkpoint_key": f"eq.{checkpoint_key}",
            "select": "checkpoint_key,state,created_at", "limit": "1",
        })
        if checkpoints:
            state = checkpoints[0].get("state") or {}
            # Checkpoints also contain private tool arguments and tool observations.
            # Expose only UI-safe progress/text fields to the run owner.
            public_state = {
                key: state[key]
                for key in ("text", "rounds", "tool_count", "next_round", "progress", "phase", "status")
                if isinstance(state, dict) and key in state
                and isinstance(state[key], (str, int, float, bool, type(None)))
            }
            output = state.get("output") if isinstance(state, dict) else None
            if isinstance(output, dict) and isinstance(output.get("text"), str):
                public_state["output"] = {"text": output["text"]}
            row = {**row, "checkpoint": public_state}
    return row


@router.get("")
async def list_runs(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    return await repository(request).select("agent_runs", {
        "user_id": f"eq.{user['id']}",
        "select": "id,conversation_id,status,input,output,error,attempt,max_attempts,created_at,started_at,finished_at",
        "order": "created_at.desc", "limit": "100",
    })


@router.get("/{run_id}")
async def get_run(run_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    return await repository(request).owned_record("agent_runs", run_id, user["id"])


@router.get("/{run_id}/steps")
async def get_run_steps(
    run_id: UUID,
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Return safe lifecycle metadata for the run's durable workflow steps.

    Step input/output/error JSON is deliberately excluded: it may contain prompts,
    private tool arguments, provider observations or sensitive artifact references.
    """
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])
    return await repo.select("agent_run_steps", {
        "run_id": f"eq.{run_id}",
        "select": "id,sequence,step_key,status,started_at,finished_at,created_at",
        "order": "sequence.asc",
        "limit": str(limit),
    })


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])
    return await repo.rpc("moreai_worker_request_cancel", {"p_run_id": str(run_id), "p_user_id": user["id"]})


def _safe_run_activity(row: dict[str, Any]) -> dict[str, Any]:
    """Translate durable events to owner-visible activity without leaking prompts/tool payloads."""
    event_type = str(row.get("event_type") or "run.activity")
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    safe: dict[str, Any] = {
        "id": row.get("id"),
        "sequence": row.get("sequence"),
        "timestamp": row.get("created_at"),
        "event_type": event_type,
    }
    for key in ("tool", "round", "index", "status", "phase", "progress", "tool_count", "next_round", "timeout_seconds"):
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)) and not isinstance(value, str) or (
            isinstance(value, str) and len(value) <= 100
        ):
            safe[key] = value
    return safe


def _thinking_message(activity: dict[str, Any]) -> dict[str, Any]:
    event_type = activity["event_type"]
    tool = activity.get("tool")
    labels = {
        "run.started": "Agent run started",
        "run.progress": "Agent progress updated",
        "tool.started": f"Tool started: {tool}" if tool else "Tool started",
        "tool.completed": f"Tool completed: {tool}" if tool else "Tool completed",
        "tool.cancelled": f"Tool cancelled: {tool}" if tool else "Tool cancelled",
        "run.completed": "Agent run completed",
        "run.failed": "Agent run failed",
        "run.cancelled": "Agent run cancelled",
        "run.timed_out": "Agent run timed out",
        "worker.checkpoint": "Execution checkpoint saved",
    }
    return {
        "message": labels.get(event_type, "Agent activity"),
        "type": "error" if event_type in {"run.failed", "run.timed_out"} else (
            "conclusion" if event_type == "run.completed" else "thinking"
        ),
        "timestamp": activity.get("timestamp"),
        "sequence": activity.get("sequence"),
        **{key: activity[key] for key in ("tool", "round", "index", "status", "phase", "progress") if key in activity},
    }


@router.get("/{run_id}/logs")
async def get_run_logs(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])
    rows = await repo.select("agent_run_events", {
        "run_id": f"eq.{run_id}", "sequence": f"gt.{after}",
        "select": "id,event_type,sequence,payload,created_at",
        "order": "sequence.asc", "limit": str(limit),
    })
    items = []
    for row in rows:
        activity = _safe_run_activity(row)
        activity["level"] = "ERROR" if activity["event_type"] in {"run.failed", "run.timed_out"} else (
            "WARNING" if activity.get("status") in {"failed", "timed_out", "cancelled"} else "INFO"
        )
        activity["message"] = _thinking_message(activity)["message"]
        items.append(activity)
    return {"items": items, "count": len(items), "next_after": items[-1]["sequence"] if items else after}


@router.get("/{run_id}/thinking")
async def get_run_thinking(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    run = await repo.owned_record("agent_runs", run_id, user["id"])
    rows = await repo.select("agent_run_events", {
        "run_id": f"eq.{run_id}", "sequence": f"gt.{after}",
        "select": "id,event_type,sequence,payload,created_at",
        "order": "sequence.asc", "limit": str(limit),
    })
    steps = await repo.select("agent_run_steps", {
        "run_id": f"eq.{run_id}",
        "select": "sequence,step_key,status,started_at,finished_at",
        "order": "sequence.asc", "limit": "200",
    })
    items = [
        _thinking_message(_safe_run_activity(row))
        for row in rows
        if row.get("event_type") in {
            "run.started", "run.progress", "tool.started", "tool.completed",
            "tool.cancelled", "run.completed", "run.failed", "run.cancelled",
            "run.timed_out", "worker.checkpoint",
        }
    ]
    completed = sum(1 for step in steps if step.get("status") == "succeeded")
    total = len(steps)
    percentage = int(completed * 100 / total) if total else (
        100 if run.get("status") == "succeeded" else 0
    )
    return {
        "status": run.get("status"),
        "thinking_steps": items,
        "progress": {
            "current_step": next((step.get("step_key") for step in reversed(steps) if step.get("status") == "running"), None),
            "total_steps": total,
            "completed_steps": completed,
            "percentage": percentage,
        },
        "next_after": rows[-1]["sequence"] if rows else after,
    }


@router.get("/{run_id}/progress")
async def get_run_progress(
    run_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    run = await repo.owned_record("agent_runs", run_id, user["id"])
    steps = await repo.select("agent_run_steps", {
        "run_id": f"eq.{run_id}",
        "select": "sequence,step_key,status,started_at,finished_at",
        "order": "sequence.asc", "limit": "200",
    })
    completed = sum(1 for step in steps if step.get("status") == "succeeded")
    total = len(steps)
    return {
        "status": run.get("status"),
        "current_step": next((step.get("step_key") for step in reversed(steps) if step.get("status") == "running"), None),
        "total_steps": total,
        "completed_steps": completed,
        "percentage": int(completed * 100 / total) if total else (100 if run.get("status") == "succeeded" else 0),
    }


@router.get("/{run_id}/events")
async def get_events(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    limit: int = Query(default=200, ge=1, le=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    cursor = _event_cursor(after, last_event_id)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])
    rows = await repo.select("agent_run_events", {
        "run_id": f"eq.{run_id}", "sequence": f"gt.{cursor}",
        "select": "id,event_type,sequence,payload,created_at", "order": "sequence.asc", "limit": str(limit),
    })
    return [await _event_with_checkpoint_state(repo, run_id, row) for row in rows]


@router.get("/{run_id}/stream")
async def stream_events(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    wait_seconds: int = Query(default=60, ge=1, le=120),
    user: dict[str, Any] = Depends(customer_principal),
):
    cursor = _event_cursor(after, last_event_id)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, user["id"])

    async def events():
        event_cursor = cursor
        idle_rounds = 0
        while idle_rounds < max(1, min(wait_seconds, 120)):
            if await request.is_disconnected():
                break
            rows = await repo.select("agent_run_events", {
                "run_id": f"eq.{run_id}", "sequence": f"gt.{event_cursor}",
                "select": "id,event_type,sequence,payload,created_at", "order": "sequence.asc", "limit": "100",
            })
            if rows:
                idle_rounds = 0
                for raw in rows:
                    row = await _event_with_checkpoint_state(repo, run_id, raw)
                    event_cursor = max(event_cursor, int(row["sequence"]))
                    payload = json.dumps(row, separators=(",", ":"))
                    yield f"id: {event_cursor}\nevent: {row['event_type']}\ndata: {payload}\n\n"
            else:
                idle_rounds += 1
                run = await repo.owned_record("agent_runs", run_id, user["id"])
                status = run.get("status")
                if status in {"succeeded", "failed", "cancelled", "expired"}:
                    terminal_event = "run.completed" if status == "succeeded" else "run.cancelled" if status == "cancelled" else "run.failed"
                    payload = json.dumps({"run_id": str(run_id), "status": status, "output": run.get("output"), "error": run.get("error")}, separators=(",", ":"))
                    yield f"id: {event_cursor}\nevent: {terminal_event}\ndata: {payload}\n\n"
                    return
                yield ": keep-alive\n\n"
            await asyncio.sleep(1)
        yield "event: stream.timeout\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })
