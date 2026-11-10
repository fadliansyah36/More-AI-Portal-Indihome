from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.dependencies import current_user
from app.repositories.supabase import SupabaseRepository

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=180)


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=100_000)
    agent_key: str = Field(default="manus", min_length=1, max_length=80)


def repository(request: Request) -> SupabaseRepository:
    settings = request.app.state.settings
    if not settings.supabase_data_ready:
        raise HTTPException(503, "Backend database credentials are not configured")
    return SupabaseRepository(url=settings.supabase_url, service_role_key=settings.supabase_service_role_key, http=request.app.state.http)


@router.post("", status_code=201)
async def create_conversation(body: ConversationCreate, request: Request, user: dict[str, Any] = Depends(current_user)):
    return await repository(request).insert("conversations", {"user_id": user["id"], "title": body.title, "status": "active", "metadata": {}})


@router.get("")
async def list_conversations(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await repository(request).select("conversations", {"user_id": f"eq.{user['id']}", "select": "id,title,status,created_at,updated_at", "order": "updated_at.desc", "limit": "100"})


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: UUID, request: Request, user: dict[str, Any] = Depends(current_user)):
    repo = repository(request)
    conversation = await repo.owned_record("conversations", conversation_id, user["id"])
    messages = await repo.select("conversation_messages", {"conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{user['id']}", "select": "id,role,content,model_key,run_id,created_at", "order": "created_at.asc", "limit": "500"})
    return {"conversation": conversation, "messages": messages}


@router.post("/{conversation_id}/messages", status_code=202)
async def send_message(conversation_id: UUID, body: MessageCreate, request: Request, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), user: dict[str, Any] = Depends(current_user)):
    if not idempotency_key or len(idempotency_key) < 12 or len(idempotency_key) > 128:
        raise HTTPException(400, "A 12–128 character Idempotency-Key header is required")
    if not request.app.state.settings.agent_execution_enabled:
        raise HTTPException(503, "Agent execution is disabled until a provider route, credit policy and worker runtime are configured")
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, user["id"])
    existing = await repo.select("agent_runs", {"user_id": f"eq.{user['id']}", "idempotency_key": f"eq.{idempotency_key}", "select": "id,status,input,created_at", "limit": "1"})
    if existing:
        return {"run": existing[0], "replayed": True}
    message = await repo.insert("conversation_messages", {"conversation_id": str(conversation_id), "user_id": user["id"], "role": "user", "content": body.content, "metadata": {}})
    run = await repo.insert("agent_runs", {"user_id": user["id"], "conversation_id": str(conversation_id), "status": "queued", "idempotency_key": idempotency_key, "input": {"prompt": body.content, "agent_key": body.agent_key, "conversation_id": str(conversation_id), "message_id": message["id"]}, "max_attempts": 3})
    await repo.update("conversation_messages", {"id": f"eq.{message['id']}", "user_id": f"eq.{user['id']}"}, {"run_id": run["id"]})
    return {"run": run, "message": message, "replayed": False}
