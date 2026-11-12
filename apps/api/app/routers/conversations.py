from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.repositories.supabase import SupabaseRepository

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=180)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)
    agent_key: Literal["manus", "planning"] = "manus"


def repository(request: Request) -> SupabaseRepository:
    settings = request.app.state.settings
    if not settings.supabase_data_ready:
        raise HTTPException(503, "Backend database credentials are not configured")
    return SupabaseRepository(url=settings.supabase_url, service_role_key=settings.supabase_service_role_key, http=request.app.state.http)


@router.post("", status_code=201)
async def create_conversation(body: ConversationCreate, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    return await repository(request).insert("conversations", {"user_id": user["id"], "title": body.title, "status": "active", "metadata": {}})


@router.get("")
async def list_conversations(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    return await repository(request).select("conversations", {"user_id": f"eq.{user['id']}", "select": "id,title,status,created_at,updated_at", "order": "updated_at.desc", "limit": "100"})


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    conversation = await repo.owned_record("conversations", conversation_id, user["id"])
    messages = await repo.select("conversation_messages", {"conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{user['id']}", "select": "id,role,content,model_key,run_id,created_at", "order": "created_at.asc", "limit": "500"})
    return {"conversation": conversation, "messages": messages}


@router.post("/{conversation_id}/messages", status_code=202)
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


@router.get("/{conversation_id}/sessions")
async def list_conversation_sessions(
    conversation_id: UUID,
    request: Request,
    limit: int = 50,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Return durable OpenManus run sessions for a conversation without exposing private execution payloads."""
    if limit < 1 or limit > 100:
        raise HTTPException(422, "limit must be between 1 and 100")
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    rows = await repo.select("agent_runs", {
        "conversation_id": f"eq.{conversation_id}",
        "user_id": f"eq.{user['id']}",
        "select": "id,conversation_id,status,attempt,max_attempts,created_at,started_at,finished_at,available_at,heartbeat_at,cancel_requested_at,last_checkpoint_key",
        "order": "created_at.desc",
        "limit": str(limit),
    })
    return {"items": rows, "count": len(rows)}
