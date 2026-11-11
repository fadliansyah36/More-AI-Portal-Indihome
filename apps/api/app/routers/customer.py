from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.authorization import require_customer_context
from app.dependencies import current_user
from app.routers.conversations import repository


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
