from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository
from app.pagination import decode_timestamp_id_cursor, encode_timestamp_id_cursor, timestamp_id_filter

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


class ToolApprovalDecisionResponse(BaseModel):
    id: UUID
    run_id: UUID
    tool_key: str
    status: Literal["approved", "denied", "expired", "consumed"]
    decided_at: datetime
    expires_at: datetime


class ApprovalRequest(BaseModel):
    run_id: UUID
    tool_key: Literal["bash", "python_execute", "browser_use", "planning_step", "browser", "file_read", "file_write", "file_edit", "workspace_restore_version"]
    arguments_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    summary: str = Field(min_length=1, max_length=1000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "denied"]


@router.get("", response_model=list[ToolApprovalResponse])
async def list_tool_approvals(
    request: Request,
    response: Response,
    limit: int = Query(default=30, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    decoded = decode_timestamp_id_cursor(cursor)
    filters = {
        "user_id": f"eq.{user['id']}",
        "status": "in.(pending,approved,denied,expired,consumed)",
        "select": "id,run_id,tool_key,summary,status,requested_at,expires_at,decided_at,consumed_at",
        "order": "requested_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = timestamp_id_filter(decoded, "requested_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    rows = await repository(request).select("agent_tool_approvals", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "requested_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.post("", status_code=201, response_model=ToolApprovalResponse)
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
    rows = await repo.select("agent_tool_approvals", {
        "id": f"eq.{approval_id}",
        "user_id": f"eq.{user['id']}",
        "select": "id,run_id,tool_key,summary,status,requested_at,expires_at,decided_at,consumed_at",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(502, "Persisted approval could not be reloaded")
    return rows[0]


@router.post("/{approval_id}/decision", response_model=ToolApprovalDecisionResponse)
async def decide_tool_approval(
    approval_id: UUID, body: ApprovalDecision, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    current = await repo.owned_record("agent_tool_approvals", approval_id, user["id"])
    projection = lambda row: {
        "id": row["id"], "run_id": row["run_id"], "tool_key": row["tool_key"],
        "status": row["status"], "decided_at": row.get("decided_at"),
        "expires_at": row["expires_at"],
    }
    current_status = str(current.get("status") or "")
    if current_status in {"approved", "denied", "expired", "consumed"}:
        if current_status == body.decision or current_status in {"expired", "consumed"}:
            return projection(current)
        raise HTTPException(409, "Tool approval already has a different durable decision")
    try:
        result = await repo.rpc("moreai_decide_tool_approval", {
            "p_approval_id": str(approval_id),
            "p_user_id": user["id"],
            "p_decision": body.decision,
        })
        if isinstance(result, dict) and result.get("id"):
            return result
    except HTTPException:
        # A lost response or concurrent decision may leave the durable row
        # committed. Re-read owner-scoped state before returning a conflict.
        refreshed = await repo.owned_record("agent_tool_approvals", approval_id, user["id"])
        refreshed_status = str(refreshed.get("status") or "")
        if refreshed_status == body.decision or refreshed_status in {"expired", "consumed"}:
            return projection(refreshed)
        raise
    refreshed = await repo.owned_record("agent_tool_approvals", approval_id, user["id"])
    return projection(refreshed)
