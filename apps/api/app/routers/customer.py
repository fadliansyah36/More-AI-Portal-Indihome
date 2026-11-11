from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.authorization import require_customer_context
from app.dependencies import current_user
from app.routers.conversations import ConversationCreate, MessageCreate, repository


router = APIRouter(prefix="/api/v1/customer", tags=["customer"])


@router.get("/context")
async def customer_context(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return {
        "principal": {"user_id": principal["id"], "role": principal["principal_role"]},
        "tenant": None,
    }


@router.post("/conversations", status_code=201)
async def create_customer_conversation(
    body: ConversationCreate, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).insert("conversations", {
        "user_id": principal["id"], "title": body.title,
        "status": "active", "metadata": {},
    })


@router.get("/conversations")
async def customer_conversations(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("conversations", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,title,status,created_at,updated_at",
        "order": "updated_at.desc", "limit": "100",
    })


@router.get("/conversations/{conversation_id}")
async def customer_conversation(
    conversation_id: UUID, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    conversation = await repo.owned_record("conversations", conversation_id, principal["id"])
    messages = await repo.select("conversation_messages", {
        "conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{principal['id']}",
        "select": "id,role,content,model_key,run_id,created_at",
        "order": "created_at.asc", "limit": "500",
    })
    return {"conversation": conversation, "messages": messages}


@router.post("/conversations/{conversation_id}/messages", status_code=202)
async def send_customer_message(
    conversation_id: UUID, body: MessageCreate, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    if not request.app.state.settings.agent_execution_enabled:
        raise HTTPException(503, "Agent execution is disabled until provider, entitlement and worker gates pass")
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "A 12–128 character Idempotency-Key header is required")
    return await repository(request).rpc("moreai_enqueue_chat_run", {
        "p_user_id": principal["id"], "p_conversation_id": str(conversation_id),
        "p_content": body.content, "p_agent_key": body.agent_key,
        "p_idempotency_key": idempotency_key,
    })


@router.get("/agent-runs")
async def customer_agent_runs(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("agent_runs", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,conversation_id,status,input,output,error,attempt,max_attempts,created_at,started_at,finished_at",
        "order": "created_at.desc", "limit": "100",
    })


@router.get("/agent-runs/{run_id}")
async def customer_agent_run(
    run_id: UUID, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).owned_record("agent_runs", run_id, principal["id"])
