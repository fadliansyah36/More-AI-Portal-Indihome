from __future__ import annotations

import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/computer", tags=["customer-computer"])


def _worker_auth(supplied: str | None) -> None:
    expected = os.getenv("MOREAI_WORKER_INTERNAL_TOKEN", "")
    if len(expected) < 32 or not supplied or not hmac.compare_digest(expected, supplied):
        raise HTTPException(401, "worker_internal_authentication_failed")


class ComputerActionClaim(BaseModel):
    run_id: UUID
    user_id: UUID
    workspace_id: UUID
    action_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    action_type: Literal["bash", "python"]


class ComputerActionFinish(BaseModel):
    run_id: UUID
    user_id: UUID
    status: Literal["succeeded", "failed", "unknown"]
    result: dict[str, Any] | None = None
    error_code: str | None = Field(default=None, max_length=100)


@router.get("/actions")
async def list_computer_action_receipts(
    request: Request,
    limit: int = 50,
    user: dict[str, Any] = Depends(customer_principal),
):
    if not 1 <= limit <= 100:
        raise HTTPException(422, "computer_action_receipt_limit_invalid")
    rows = await repository(request).select("moreai_computer_action_receipts", {
        "user_id": f"eq.{user['id']}",
        "select": "id,run_id,workspace_id,action_type,status,error_code,requested_at,finished_at",
        "order": "requested_at.desc,id.desc",
        "limit": str(limit),
    })
    stale_before = datetime.now(timezone.utc) - timedelta(minutes=5)
    for row in rows:
        if row.get("status") == "executing":
            try:
                requested_at = datetime.fromisoformat(str(row.get("requested_at", "")).replace("Z", "+00:00"))
            except ValueError:
                requested_at = stale_before - timedelta(seconds=1)
            if requested_at <= stale_before:
                row["status"] = "unknown"
                row["error_code"] = "worker_receipt_stale"
    return {"items": rows}


@router.post("/internal/actions/claim")
async def claim_computer_action_receipt(
    body: ComputerActionClaim,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "eq.running", "select": "id,workspace_id", "limit": "1",
    })
    if not runs or str(runs[0].get("workspace_id") or "") != str(body.workspace_id):
        raise HTTPException(403, "computer_action_run_workspace_owner_mismatch")
    existing = await repo.select("moreai_computer_action_receipts", {
        "run_id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "action_key": f"eq.{body.action_key}",
        "select": "id,status,result,error_code,request_hash", "limit": "1",
    })
    if existing:
        row = existing[0]
        if row.get("request_hash") != body.request_hash:
            raise HTTPException(409, "computer_action_idempotency_key_conflict")
        return {
            "receipt_id": row["id"], "status": row["status"],
            "can_execute": False, "result": row.get("result"),
            "error_code": row.get("error_code"),
        }
    try:
        row = await repo.insert("moreai_computer_action_receipts", {
            "run_id": str(body.run_id), "user_id": str(body.user_id),
            "workspace_id": str(body.workspace_id), "action_key": body.action_key,
            "request_hash": body.request_hash, "action_type": body.action_type,
            "status": "executing",
        })
        return {
            "receipt_id": row["id"], "status": "executing",
            "can_execute": True, "result": None, "error_code": None,
        }
    except HTTPException:
        existing = await repo.select("moreai_computer_action_receipts", {
            "run_id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
            "action_key": f"eq.{body.action_key}",
            "select": "id,status,result,error_code,request_hash", "limit": "1",
        })
        if not existing:
            raise
        row = existing[0]
        if row.get("request_hash") != body.request_hash:
            raise HTTPException(409, "computer_action_idempotency_key_conflict")
        return {
            "receipt_id": row["id"], "status": row["status"],
            "can_execute": False, "result": row.get("result"),
            "error_code": row.get("error_code"),
        }


@router.post("/internal/actions/{receipt_id}/finish")
async def finish_computer_action_receipt(
    receipt_id: UUID,
    body: ComputerActionFinish,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "in.(running,succeeded,failed,cancelled,expired)",
        "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "computer_action_run_owner_mismatch")
    result = body.result or {}
    import json
    if len(json.dumps(result, separators=(",", ":"), ensure_ascii=True).encode()) > 160_000:
        raise HTTPException(413, "computer_action_result_too_large")
    rows = await repo.update("moreai_computer_action_receipts", {
        "id": f"eq.{receipt_id}", "run_id": f"eq.{body.run_id}",
        "user_id": f"eq.{body.user_id}", "status": "eq.executing",
    }, {
        "status": body.status,
        "result": result if body.status in {"succeeded", "failed"} else None,
        "error_code": body.error_code,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    })
    if rows:
        return {"receipt_id": str(receipt_id), "status": body.status}
    current = await repo.select("moreai_computer_action_receipts", {
        "id": f"eq.{receipt_id}", "run_id": f"eq.{body.run_id}",
        "user_id": f"eq.{body.user_id}", "select": "id,status", "limit": "1",
    })
    if not current:
        raise HTTPException(404, "computer_action_receipt_not_found")
    if current[0].get("status") == body.status:
        return {"receipt_id": str(receipt_id), "status": body.status, "replayed": True}
    raise HTTPException(409, "computer_action_receipt_already_finalized")
