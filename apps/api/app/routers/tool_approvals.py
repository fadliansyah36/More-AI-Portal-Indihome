from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/tool-approvals", tags=["customer-tool-approvals"])


class ToolApprovalResponse(BaseModel):
    id: UUID
    run_id: UUID
    tool_key: str
    summary: str
    status: Literal["pending", "approved", "denied", "expired", "consumed"]
    requested_at: datetime
    expires_at: datetime
    decided_at: datetime | None
    consumed_at: datetime | None


class ToolApprovalMutationResponse(BaseModel):
    id: UUID
    status: Literal["pending", "approved", "denied", "expired", "consumed"]


class ApprovalRequest(BaseModel):
    run_id: UUID
    tool_key: Literal["bash", "python_execute", "browser_use", "planning_step", "browser", "file_read", "file_write", "file_edit", "workspace_restore_version"]
    arguments_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary: str = Field(min_length=1, max_length=1000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "denied"]


@router.get("", response_model=list[ToolApprovalResponse])
async def list_tool_approvals(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    return await repository(request).select("agent_tool_approvals", {
        "user_id": f"eq.{user['id']}",
        "status": "in.(pending,approved,denied,expired,consumed)",
        "select": "id,run_id,tool_key,summary,status,requested_at,expires_at,decided_at,consumed_at",
        "order": "requested_at.desc",
        "limit": "100",
    })


@router.post("", status_code=201, response_model=ToolApprovalMutationResponse)
async def request_tool_approval(
    body: ApprovalRequest, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await repo.owned_record("agent_runs", body.run_id, user["id"])
    try:
        approval_id = await repo.rpc("moreai_request_tool_approval", {
            "p_run_id": str(body.run_id),
            "p_user_id": user["id"],
            "p_tool_key": body.tool_key,
            "p_arguments_hash": body.arguments_hash,
            "p_summary": body.summary,
            "p_expires_in_seconds": 900,
        })
    except HTTPException:
        raise
    if not approval_id:
        raise HTTPException(502, "Approval request was not persisted")
    return {"id": approval_id, "status": "pending"}


@router.post("/{approval_id}/decision", response_model=dict[str, Any])
async def decide_tool_approval(
    approval_id: UUID, body: ApprovalDecision, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    return await repository(request).rpc("moreai_decide_tool_approval", {
        "p_approval_id": str(approval_id),
        "p_user_id": user["id"],
        "p_decision": body.decision,
    })
