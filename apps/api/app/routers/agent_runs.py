from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from fastapi import Response

from app.authorization import customer_principal, require_customer_context
from app.dependencies import current_user
from app.routers.conversations import repository
from app.pagination import decode_created_at_id_cursor, encode_created_at_id_cursor, created_at_id_filter

router = APIRouter(prefix="/api/v1/agent-runs", tags=["agent-runs"])


class AgentRunCancellationResponse(BaseModel):
    run_id: UUID
    status: Literal["cancel_requested", "cancelled", "succeeded", "failed", "timed_out", "expired"]


class AgentRunResponse(BaseModel):
    id: UUID
    conversation_id: UUID | None = None
    status: str
    input: Any = None
    output: Any = None
    error: Any = None
    attempt: int | None = None
    max_attempts: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class AgentRunStepResponse(BaseModel):
    id: UUID
    sequence: int
    step_key: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class AgentRunActivityResponse(BaseModel):
    id: UUID
    sequence: int
    timestamp: datetime
    event_type: str
    tool: str | None = None
    round: int | None = None
    index: int | None = None
    status: str | None = None
    phase: str | None = None
    progress: int | float | None = None
    tool_count: int | None = None
    next_round: int | None = None
    timeout_seconds: int | None = None
    checkpoint_key: str | None = None
    level: str | None = None
    message: str | None = None


class AgentRunActivityPageResponse(BaseModel):
    items: list[AgentRunActivityResponse]
    count: int
    next_after: int


class AgentRunThinkingStepResponse(BaseModel):
    message: str
    type: str
    timestamp: datetime | None = None
    sequence: int | None = None
    tool: str | None = None
    round: int | None = None
    index: int | None = None
    status: str | None = None
    phase: str | None = None
    progress: int | float | None = None


class AgentRunProgressResponse(BaseModel):
    current_step: str | None = None
    total_steps: int
    completed_steps: int
    percentage: int


class AgentRunThinkingResponse(BaseModel):
    status: str
    thinking_steps: list[AgentRunThinkingStepResponse]
    progress: AgentRunProgressResponse
    next_after: int


class AgentRunProgressSnapshotResponse(BaseModel):
    status: str
    current_step: str | None = None
    total_steps: int
    completed_steps: int
    percentage: int


class AgentRunEventResponse(BaseModel):
    id: UUID
    event_type: str
    sequence: int
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    checkpoint: dict[str, Any] | None = None


_MAX_EVENT_SEQUENCE = 9_223_372_036_854_775_807
_TERMINAL_RUN_STATUSES = {"succeeded", "failed", "cancelled", "timed_out", "expired"}


def _validated_event_sequence(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("event_sequence_invalid")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.isascii() and value.isdecimal() and len(value) <= 19:
        parsed = int(value, 10)
    else:
        raise ValueError("event_sequence_invalid")
    if parsed < 0 or parsed > _MAX_EVENT_SEQUENCE:
        raise ValueError("event_sequence_out_of_range")
    return parsed


def _event_cursor(after: int, last_event_id: str | None) -> int:
    """Honor EventSource reconnection cursors without accepting malformed IDs."""
    try:
        query_cursor = _validated_event_sequence(after)
        if last_event_id is None or not last_event_id.strip():
            return query_cursor
        header_cursor = _validated_event_sequence(last_event_id.strip())
    except ValueError as exc:
        raise HTTPException(400, "Event cursor must be a non-negative 64-bit integer") from exc
    return max(query_cursor, header_cursor)


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


@router.get("", response_model=list[AgentRunResponse])
async def list_runs(
    request: Request,
    response: Response,
    limit: int = Query(default=100, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """List owner-scoped durable runs using stable keyset pagination."""
    decoded = decode_created_at_id_cursor(cursor)
    params = {
        "user_id": f"eq.{user['id']}",
        "select": "id,conversation_id,status,input,output,error,attempt,max_attempts,created_at,started_at,finished_at",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        params["or"] = cursor_filter
    rows = await repository(request).select("agent_runs", params)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    return await repository(request).owned_record("agent_runs", run_id, user["id"])


@router.get("/{run_id}/steps", response_model=list[AgentRunStepResponse])
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


@router.post("/{run_id}/cancel", response_model=AgentRunCancellationResponse)
async def cancel_run(run_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    run = await repo.owned_record("agent_runs", run_id, user["id"])
    status = str(run.get("status") or "")
    if status in _TERMINAL_RUN_STATUSES:
        return {"run_id": str(run_id), "status": status}
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
    for key in ("tool", "round", "index", "status", "phase", "progress", "tool_count", "next_round", "timeout_seconds", "checkpoint_key"):
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
        "run.expired": "Agent run expired",
        "worker.checkpoint": "Execution checkpoint saved",
    }
    if event_type == "worker.checkpoint":
        checkpoint_key = activity.get("checkpoint_key")
        if checkpoint_key == "planning.manifest":
            labels[event_type] = "Execution plan persisted"
        elif isinstance(checkpoint_key, str) and checkpoint_key.startswith("planning.step."):
            parts = checkpoint_key.split(".")
            step_number = parts[2] if len(parts) > 2 else "?"
            phase = parts[3] if len(parts) > 3 else "checkpointed"
            labels[event_type] = f"Planning step {step_number} {phase}"
    return {
        "message": labels.get(event_type, "Agent activity"),
        "type": "error" if event_type in {"run.failed", "run.timed_out", "run.expired"} else (
            "conclusion" if event_type == "run.completed" else "thinking"
        ),
        "timestamp": activity.get("timestamp"),
        "sequence": activity.get("sequence"),
        **{key: activity[key] for key in ("tool", "round", "index", "status", "phase", "progress") if key in activity},
    }


@router.get("/{run_id}/logs", response_model=AgentRunActivityPageResponse)
async def get_run_logs(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0, le=9_223_372_036_854_775_807),
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
        activity["level"] = "ERROR" if activity["event_type"] in {"run.failed", "run.timed_out", "run.expired"} else (
            "WARNING" if activity.get("status") in {"failed", "timed_out", "cancelled"} else "INFO"
        )
        activity["message"] = _thinking_message(activity)["message"]
        items.append(activity)
    return {"items": items, "count": len(items), "next_after": items[-1]["sequence"] if items else after}


@router.get("/{run_id}/thinking", response_model=AgentRunThinkingResponse)
async def get_run_thinking(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0, le=9_223_372_036_854_775_807),
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
            "run.timed_out", "run.expired", "worker.checkpoint",
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


@router.get("/{run_id}/progress", response_model=AgentRunProgressSnapshotResponse)
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


@router.get("/{run_id}/events", response_model=list[AgentRunEventResponse])
async def get_events(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0, le=9_223_372_036_854_775_807),
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


@router.websocket("/{run_id}/ws")
async def stream_run_websocket(websocket: WebSocket, run_id: UUID):
    """Authenticated replayable WebSocket using the OpenManus status/log/thinking envelope."""
    try:
        authorization = websocket.headers.get("authorization")
        user = await current_user(websocket, authorization)
        principal = await require_customer_context(websocket, user)
        repo = repository(websocket)
        run = await repo.owned_record("agent_runs", run_id, principal["id"])
    except HTTPException as exc:
        await websocket.close(code=4401 if exc.status_code == 401 else 4403)
        return
    except Exception:
        await websocket.close(code=1011)
        return

    try:
        cursor_text = websocket.query_params.get("after", "0")
        try:
            cursor = _validated_event_sequence(cursor_text)
        except ValueError:
            await websocket.close(code=4400)
            return
        await websocket.accept()

        # Replay strictly after the caller cursor. Fetching the newest events first
        # and then advancing to their maximum sequence silently skipped older gaps
        # and duplicated already-acknowledged events on reconnect.
        initial_rows = await repo.select("agent_run_events", {
            "run_id": f"eq.{run_id}",
            "sequence": f"gt.{cursor}",
            "select": "id,event_type,sequence,payload,created_at",
            "order": "sequence.asc",
            "limit": "200",
        })
        initial_activities = [_safe_run_activity(row) for row in initial_rows]
        initial_thinking = [
            _thinking_message(item) for item in initial_activities
            if item["event_type"] in {
                "run.started", "run.progress", "tool.started", "tool.completed",
                "tool.cancelled", "run.completed", "run.failed", "run.cancelled",
                "run.timed_out", "run.expired", "worker.checkpoint",
            }
        ]
        initial_logs = [
            {
                **_thinking_message(item),
                "level": "ERROR" if item["event_type"] in {"run.failed", "run.timed_out", "run.expired"} else "INFO",
                "event_type": item["event_type"],
            }
            for item in initial_activities
        ]
        cursor = max(cursor, max((int(item["sequence"]) for item in initial_activities if item.get("sequence") is not None), default=0))
        steps = await repo.select("agent_run_steps", {
            "run_id": f"eq.{run_id}",
            "select": "sequence,step_key,status,started_at,finished_at",
            "order": "sequence.asc", "limit": "200",
        })
        completed = sum(1 for step in steps if step.get("status") == "succeeded")
        total = len(steps)
        progress = {
            "current_step": next((step.get("step_key") for step in reversed(steps) if step.get("status") == "running"), None),
            "total_steps": total,
            "completed_steps": completed,
            "percentage": int(completed * 100 / total) if total else (100 if run.get("status") == "succeeded" else 0),
        }
        await websocket.send_json({
            "status": run.get("status"),
            "log": initial_logs,
            "thinking_steps": initial_thinking,
            "logs": initial_logs,
            "system_logs": initial_logs,
            "progress": progress,
            "sequence": cursor,
            **({"result": run.get("output")} if run.get("status") in _TERMINAL_RUN_STATUSES else {}),
        })
        if run.get("status") in _TERMINAL_RUN_STATUSES:
            await websocket.close(code=1000)
            return

        idle_rounds = 0
        while idle_rounds < 300:
            rows = await repo.select("agent_run_events", {
                "run_id": f"eq.{run_id}", "sequence": f"gt.{cursor}",
                "select": "id,event_type,sequence,payload,created_at",
                "order": "sequence.asc", "limit": "100",
            })
            if rows:
                idle_rounds = 0
                activities = [_safe_run_activity(row) for row in rows]
                cursor = max(cursor, max(int(item["sequence"]) for item in activities))
                thinking = [
                    _thinking_message(item) for item in activities
                    if item["event_type"] in {
                        "run.started", "run.progress", "tool.started", "tool.completed",
                        "tool.cancelled", "run.completed", "run.failed", "run.cancelled",
                        "run.timed_out", "run.expired", "worker.checkpoint",
                    }
                ]
                logs = [
                    {
                        **_thinking_message(item),
                        "level": "ERROR" if item["event_type"] in {"run.failed", "run.timed_out", "run.expired"} else "INFO",
                        "event_type": item["event_type"],
                    }
                    for item in activities
                ]
                run = await repo.owned_record("agent_runs", run_id, principal["id"])
                await websocket.send_json({
                    "status": run.get("status"),
                    "log": logs,
                    "thinking_steps": thinking,
                    "logs": logs,
                    "system_logs": logs,
                    "sequence": cursor,
                })
            else:
                idle_rounds += 1
                run = await repo.owned_record("agent_runs", run_id, principal["id"])
                if run.get("status") in _TERMINAL_RUN_STATUSES:
                    await websocket.send_json({
                        "status": run.get("status"),
                        "result": run.get("output"),
                        "log": [], "thinking_steps": [], "logs": [], "system_logs": [],
                        "sequence": cursor,
                    })
                    await websocket.close(code=1000)
                    return
                await websocket.send_json({
                    "status": run.get("status"),
                    "keepalive": True,
                    "sequence": cursor,
                })
            await asyncio.sleep(1)
        await websocket.send_json({"status": run.get("status"), "stream_timeout": True, "sequence": cursor})
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@router.get("/{run_id}/stream")
async def stream_events(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0, le=9_223_372_036_854_775_807),
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
                if status in _TERMINAL_RUN_STATUSES:
                    terminal_event = {"succeeded": "run.completed", "failed": "run.failed", "cancelled": "run.cancelled", "timed_out": "run.timed_out", "expired": "run.expired"}[status]
                    payload = json.dumps({"run_id": str(run_id), "status": status, "output": run.get("output"), "error": run.get("error")}, separators=(",", ":"))
                    yield f"id: {event_cursor}\nevent: {terminal_event}\ndata: {payload}\n\n"
                    return
                yield ": keep-alive\n\n"
            await asyncio.sleep(1)
        yield "event: stream.timeout\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })
