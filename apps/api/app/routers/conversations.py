from __future__ import annotations

from typing import Any, Literal
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query, WebSocket, Response
from pydantic import BaseModel, Field

from app.authorization import customer_principal, require_customer_context
from app.dependencies import current_user
from app.repositories.supabase import SupabaseRepository
from app.pagination import decode_created_at_id_cursor, encode_created_at_id_cursor, created_at_id_filter

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=180)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)
    agent_key: Literal["manus", "planning", "toolcall"] = "manus"
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class ConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    model_key: str | None = None
    run_id: UUID | None = None
    created_at: datetime
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class ConversationDetailResponse(BaseModel):
    conversation: ConversationResponse
    messages: list[ConversationMessageResponse]


class ConversationSessionResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    status: str
    attempt: int
    max_attempts: int
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    available_at: datetime | None = None
    heartbeat_at: datetime | None = None
    cancel_requested_at: datetime | None = None
    last_checkpoint_key: str | None = None


class ConversationSessionEventResponse(BaseModel):
    id: UUID
    event_type: str
    sequence: int
    created_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class ConversationSessionEventPageResponse(BaseModel):
    items: list[ConversationSessionEventResponse]
    count: int
    next_after: int


class ConversationSessionPageResponse(BaseModel):
    items: list[ConversationSessionResponse]
    count: int


class ConversationSessionCancellationResponse(BaseModel):
    run_id: UUID
    status: Literal["cancel_requested", "cancelled", "succeeded", "failed", "timed_out", "expired"]


class ConversationEnqueuedRunResponse(BaseModel):
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


class ConversationMessageEnqueueResponse(BaseModel):
    run: ConversationEnqueuedRunResponse
    message: ConversationMessageResponse | None
    replayed: bool


class ConversationArchiveResponse(BaseModel):
    id: UUID
    status: Literal["archived"]


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=180)
    status: Literal["active", "archived"] | None = None


def repository(request: Request) -> SupabaseRepository:
    settings = request.app.state.settings
    if not settings.supabase_data_ready:
        raise HTTPException(503, "Backend database credentials are not configured")
    return SupabaseRepository(url=settings.supabase_url, service_role_key=settings.supabase_service_role_key, http=request.app.state.http)


@router.post("", status_code=201, response_model=ConversationResponse)
async def create_conversation(body: ConversationCreate, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    return await repository(request).insert("conversations", {"user_id": user["id"], "title": body.title, "status": "active", "metadata": {}})


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    request: Request,
    response: Response,
    limit: int = Query(default=100, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """List conversations with backwards-compatible array payload and opaque keyset cursor header."""
    decoded = decode_created_at_id_cursor(cursor)
    params = {
        "user_id": f"eq.{user['id']}",
        "select": "id,title,status,created_at,updated_at",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        params["or"] = cursor_filter
    rows = await repository(request).select("conversations", params)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    conversation = await repo.owned_record("conversations", conversation_id, user["id"])
    messages = await repo.select("conversation_messages", {"conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{user['id']}", "select": "id,role,content,model_key,run_id,created_at", "order": "created_at.asc", "limit": "500"})
    return {"conversation": conversation, "messages": messages}


@router.post("/{conversation_id}/messages", status_code=202, response_model=ConversationMessageEnqueueResponse)
async def send_message(
    conversation_id: UUID,
    body: MessageCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(customer_principal),
):
    if not request.app.state.settings.agent_execution_enabled:
        raise HTTPException(503, "Agent execution is disabled until a provider route, credit policy and worker runtime are configured")
    if not idempotency_key or len(idempotency_key) < 12 or len(idempotency_key) > 128:
        raise HTTPException(400, "A 12–128 character Idempotency-Key header is required")

    repo = repository(request)
    # The SECURITY DEFINER RPC performs ownership validation and atomically inserts
    # the user message, queued run, and message.run_id relationship in one transaction.
    return await repo.rpc("moreai_enqueue_chat_run", {
        "p_user_id": user["id"],
        "p_conversation_id": str(conversation_id),
        "p_content": body.content,
        "p_agent_key": body.agent_key,
        "p_idempotency_key": idempotency_key,
    })


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    body: ConversationUpdate,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    changes: dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if body.title is not None:
        normalized_title = body.title.strip()
        if not normalized_title:
            raise HTTPException(422, "conversation_title_cannot_be_empty")
        changes["title"] = normalized_title
    if body.status is not None:
        changes["status"] = body.status
    if len(changes) == 1:
        raise HTTPException(422, "conversation_update_requires_title_or_status")
    rows = await repo.update("conversations", {"id": f"eq.{conversation_id}", "user_id": f"eq.{user['id']}"}, changes)
    if not rows:
        raise HTTPException(404, "conversation_not_found")
    return rows[0]


@router.delete("/{conversation_id}", response_model=ConversationArchiveResponse)
async def archive_conversation(
    conversation_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    rows = await repo.update("conversations", {
        "id": f"eq.{conversation_id}", "user_id": f"eq.{user['id']}",
    }, {"status": "archived", "updated_at": datetime.now(timezone.utc).isoformat()})
    if not rows:
        raise HTTPException(404, "conversation_not_found")
    return {"id": str(conversation_id), "status": "archived"}


@router.get("/{conversation_id}/sessions/{run_id}", response_model=ConversationSessionResponse)
async def get_conversation_session(
    conversation_id: UUID,
    run_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    run = await repo.owned_record("agent_runs", run_id, user["id"])
    if str(run.get("conversation_id")) != str(conversation_id):
        raise HTTPException(404, "session_not_found")
    return {
        "id": run.get("id"),
        "conversation_id": run.get("conversation_id"),
        "status": run.get("status"),
        "attempt": run.get("attempt"),
        "max_attempts": run.get("max_attempts"),
        "created_at": run.get("created_at"),
        "started_at": run.get("started_at"),
        "finished_at": run.get("finished_at"),
        "last_checkpoint_key": run.get("last_checkpoint_key"),
    }


@router.post("/{conversation_id}/sessions/{run_id}/cancel", response_model=ConversationSessionCancellationResponse)
async def cancel_conversation_session(
    conversation_id: UUID,
    run_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Cancel a durable OpenManus session only after verifying both conversation and run ownership."""
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    run = await repo.owned_record("agent_runs", run_id, user["id"])
    if str(run.get("conversation_id")) != str(conversation_id):
        raise HTTPException(404, "session_not_found")
    status = str(run.get("status") or "")
    if status in {"succeeded", "failed", "cancelled", "timed_out", "expired"}:
        return {"run_id": str(run_id), "status": status}
    return await repo.rpc("moreai_worker_request_cancel", {
        "p_run_id": str(run_id),
        "p_user_id": user["id"],
    })


@router.get("/{conversation_id}/sessions/{run_id}/events", response_model=ConversationSessionEventPageResponse)
async def get_conversation_session_events(
    conversation_id: UUID,
    run_id: UUID,
    request: Request,
    after: int = Query(default=0, ge=0, le=9_223_372_036_854_775_807),
    limit: int = Query(default=200, ge=1, le=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    run = await repo.owned_record("agent_runs", run_id, user["id"])
    if str(run.get("conversation_id")) != str(conversation_id):
        raise HTTPException(404, "session_not_found")
    rows = await repo.select("agent_run_events", {
        "run_id": f"eq.{run_id}", "sequence": f"gt.{after}",
        "select": "id,event_type,sequence,payload,created_at",
        "order": "sequence.asc", "limit": str(limit),
    })
    safe_items = []
    for row in rows:
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        safe_payload = {
            key: value for key, value in payload.items()
            if key in {"tool", "round", "index", "status", "phase", "progress", "checkpoint_key"}
            and isinstance(value, (str, int, float, bool))
            and (not isinstance(value, str) or len(value) <= 100)
        }
        safe_items.append({
            "id": row.get("id"), "event_type": row.get("event_type"),
            "sequence": row.get("sequence"), "created_at": row.get("created_at"),
            "payload": safe_payload,
        })
    return {"items": safe_items, "count": len(safe_items), "next_after": rows[-1]["sequence"] if rows else after}


@router.websocket("/{conversation_id}/sessions/{run_id}/ws")
async def stream_conversation_session(websocket: WebSocket, conversation_id: UUID, run_id: UUID):
    try:
        user = await current_user(websocket, websocket.headers.get("authorization"))
        principal = await require_customer_context(websocket, user)
        repo = repository(websocket)
        await repo.owned_record("conversations", conversation_id, principal["id"])
        run = await repo.owned_record("agent_runs", run_id, principal["id"])
        if str(run.get("conversation_id")) != str(conversation_id):
            await websocket.close(code=4404)
            return
        from app.routers.agent_runs import stream_run_websocket
        await stream_run_websocket(websocket, run_id)
    except HTTPException as exc:
        await websocket.close(code=4401 if exc.status_code == 401 else 4403)
    except Exception:
        await websocket.close(code=1011)


@router.get("/{conversation_id}/sessions", response_model=ConversationSessionPageResponse)
async def list_conversation_sessions(
    conversation_id: UUID,
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Return owner-scoped durable sessions with stable keyset pagination."""
    decoded = decode_created_at_id_cursor(cursor)
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    params = {
        "conversation_id": f"eq.{conversation_id}",
        "user_id": f"eq.{user['id']}",
        "select": "id,conversation_id,status,attempt,max_attempts,created_at,started_at,finished_at,available_at,heartbeat_at,cancel_requested_at,last_checkpoint_key",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        params["or"] = cursor_filter
    rows = await repo.select("agent_runs", params)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": rows, "count": len(rows)}
