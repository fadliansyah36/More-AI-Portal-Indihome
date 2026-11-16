from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/browser-sessions", tags=["customer-browser-sessions"])
MAX_STATE_BYTES = 1_000_000
SESSION_TTL_HOURS = 8
IDLE_TTL_MINUTES = 30


def _worker_auth(request: Request, supplied: str | None) -> None:
    expected = os.getenv("MOREAI_WORKER_INTERNAL_TOKEN", "")
    if len(expected) < 32 or not supplied or not __import__("hmac").compare_digest(expected, supplied):
        raise HTTPException(401, "worker_internal_authentication_failed")


def _cipher(request: Request) -> Fernet:
    key = request.app.state.settings.browser_session_encryption_key
    if not key:
        raise HTTPException(503, "browser_session_encryption_not_configured")
    try:
        return Fernet(key.encode("ascii"))
    except Exception as exc:
        raise HTTPException(503, "browser_session_encryption_key_invalid") from exc


def _decrypt(request: Request, value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        raw = _cipher(request).decrypt(value.encode("ascii"))
        parsed = json.loads(raw)
    except (InvalidToken, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(503, "browser_session_state_unavailable") from exc
    if not isinstance(parsed, dict):
        raise HTTPException(503, "browser_session_state_invalid")
    return parsed


def _encrypt(request: Request, state: dict[str, Any]) -> str:
    raw = json.dumps(state, separators=(",", ":"), ensure_ascii=True).encode()
    if len(raw) > MAX_STATE_BYTES:
        raise HTTPException(413, "browser_session_state_too_large")
    return _cipher(request).encrypt(raw).decode("ascii")


class BrowserActionReceiptClaim(BaseModel):
    run_id: UUID
    user_id: UUID
    worker_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    action_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    action_type: Literal["navigate", "extract", "input", "screenshot", "close", "downloads"]
    target_host: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")


class BrowserActionReceiptFinish(BaseModel):
    run_id: UUID
    user_id: UUID
    worker_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    status: Literal["succeeded", "failed", "unknown"]
    session_id: UUID | None = None
    result: dict[str, Any] | None = None
    error_code: str | None = Field(default=None, max_length=100)


class SessionAcquire(BaseModel):
    run_id: UUID
    user_id: UUID
    session_id: UUID | None = None
    origin_host: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")
    action: Literal["navigate", "extract", "input", "screenshot", "close", "downloads"] = "navigate"
    worker_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")


class SessionWorkerClose(BaseModel):
    run_id: UUID
    user_id: UUID


class SessionWorkerOwner(BaseModel):
    user_id: UUID


class SessionStateUpdate(BaseModel):
    run_id: UUID
    user_id: UUID
    storage_state: dict[str, Any]


class BrowserTakeoverGrantCreate(BaseModel):
    ttl_seconds: int = Field(default=90, ge=30, le=120)


class BrowserTakeoverGrantConsume(BaseModel):
    token: str = Field(min_length=32, max_length=256)
    worker_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")

class BrowserTakeoverCommandCreate(BaseModel):
    grant_token: str = Field(min_length=32, max_length=256)
    input: dict[str, Any]

class BrowserTakeoverCommandFinish(BaseModel):
    status: Literal["succeeded", "failed"]
    result: dict[str, Any] | None = None
    error_code: str | None = Field(default=None, max_length=100)

class BrowserTakeoverInputAudit(BaseModel):
    session_id: UUID
    user_id: UUID
    worker_id: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    status: Literal["succeeded", "failed"]
    error_code: str | None = Field(default=None, max_length=100)


@router.get("/actions")
async def list_browser_action_receipts(
    request: Request,
    limit: int = 50,
    session_id: UUID | None = None,
    user: dict[str, Any] = Depends(customer_principal),
):
    if not 1 <= limit <= 100:
        raise HTTPException(422, "browser_action_receipt_limit_invalid")
    filters: dict[str, str] = {
        "user_id": f"eq.{user['id']}",
        "select": "id,run_id,session_id,action_type,target_host,status,error_code,requested_at,finished_at",
        "order": "requested_at.desc,id.desc",
        "limit": str(limit),
    }
    if session_id:
        filters["session_id"] = f"eq.{session_id}"
    rows = await repository(request).select("moreai_browser_action_receipts", filters)
    stale_before = datetime.now(timezone.utc) - timedelta(minutes=5)
    for row in rows:
        if row.get("status") == "executing":
            try:
                requested_at = datetime.fromisoformat(str(row.get("requested_at", "")).replace("Z", "+00:00"))
            except ValueError:
                requested_at = stale_before - timedelta(seconds=1)
            if requested_at <= stale_before:
                # Projection only: preserve the durable executing row and block replay,
                # but do not tell the customer that an old worker lease is still active.
                row["status"] = "unknown"
                row["error_code"] = "worker_receipt_stale"
    return {"items": rows}


@router.get("/internal/expire-requests")
async def mark_expired_browser_sessions_for_close(
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    """Turn TTL/idle expiry into atomic, durable close work."""
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    now = datetime.now(timezone.utc)
    idle_before = now - timedelta(minutes=IDLE_TTL_MINUTES)
    rows = await repo.select("moreai_browser_sessions", {
        "status": "eq.active",
        "select": "id,user_id,expires_at,last_used_at",
        "order": "last_used_at.asc",
        "limit": "100",
    })
    queued = []
    for row in rows:
        try:
            expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
            last_used_at = datetime.fromisoformat(str(row["last_used_at"]).replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError):
            expires_at, last_used_at = now - timedelta(seconds=1), idle_before - timedelta(seconds=1)
        reason = "ttl" if expires_at <= now else "idle" if last_used_at <= idle_before else None
        if reason is None:
            continue
        result = await repo.rpc("moreai_request_browser_session_close", {
            "p_session_id": str(row["id"]), "p_user_id": str(row["user_id"]),
            "p_source": "ttl_reconciler", "p_reason": reason,
        })
        if isinstance(result, dict) and result.get("status") == "close_requested":
            queued.append({"session_id": str(row["id"]), "user_id": str(row["user_id"])})
    return {"items": queued}


@router.get("/internal/owned-profile-ids")
async def list_owned_browser_profile_ids(
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    """Return canonical profile ownership keys; worker must fail closed if this call fails."""
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    ownership_filter = {"profile_deleted_at": "is.null"}
    total = await repo.count("moreai_browser_sessions", ownership_filter)
    # Bound the response and explicitly signal incompleteness. The worker must
    # never run destructive reconciliation from a partial ownership inventory.
    if total > 10000:
        return {"items": [], "complete": False, "total": total}
    page_size = 500
    rows: list[dict[str, Any]] = []
    for offset in range(0, total, page_size):
        page = await repo.select("moreai_browser_sessions", {
            **ownership_filter, "select": "id", "order": "id.asc",
            "limit": str(page_size), "offset": str(offset),
        })
        if len(page) != min(page_size, total - offset):
            raise HTTPException(503, "browser_profile_ownership_inventory_incomplete")
        rows.extend(page)
    if len(rows) != total:
        raise HTTPException(503, "browser_profile_ownership_inventory_incomplete")
    return {"items": [str(row["id"]) for row in rows if row.get("id")], "complete": True, "total": total}


@router.get("/internal/profile-cleanup-requests")
async def list_browser_profile_cleanup_requests(
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    """Atomically claim newly eligible profile-retention events."""
    _worker_auth(request, x_moreai_worker_token)
    result = await repository(request).rpc("moreai_claim_browser_profile_retention", {"p_limit": 100})
    if not isinstance(result, dict) or not isinstance(result.get("items"), list):
        raise HTTPException(503, "browser_profile_retention_claim_contract_invalid")
    return result


@router.post("/internal/{session_id}/profile-deleted")
async def acknowledge_browser_profile_deleted(
    session_id: UUID,
    body: SessionWorkerOwner,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    result = await repository(request).rpc("moreai_ack_browser_profile_deleted", {
        "p_session_id": str(session_id), "p_user_id": str(body.user_id),
    })
    if not isinstance(result, dict) or result.get("status") != "profile_deleted":
        raise HTTPException(409, "browser_profile_deletion_acknowledgement_invalid")
    return result


@router.get("/internal/close-requests")
async def list_browser_session_close_requests(
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    rows = await repo.select("moreai_browser_sessions", {
        "status": "eq.close_requested",
        "select": "id,user_id,last_run_id,origin_host",
        "order": "last_used_at.asc",
        "limit": "50",
    })
    ready = []
    for row in rows:
        run_id = row.get("last_run_id")
        if run_id:
            active_run = await repo.select("agent_runs", {
                "id": f"eq.{run_id}", "user_id": f"eq.{row['user_id']}",
                "status": "in.(queued,running,waiting_approval)", "select": "id", "limit": "1",
            })
            if active_run:
                continue
        ready.append({"session_id": row["id"], "user_id": row["user_id"]})
    return {"items": ready}


@router.post("/internal/{session_id}/close-complete")
async def complete_browser_session_close(
    session_id: UUID,
    body: SessionWorkerOwner,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    result = await repository(request).rpc("moreai_complete_browser_session_close", {
        "p_session_id": str(session_id), "p_user_id": str(body.user_id),
    })
    if not isinstance(result, dict) or result.get("status") != "closed":
        raise HTTPException(503, "browser_session_close_completion_contract_invalid")
    return result

@router.post("/internal/actions/claim")
async def claim_browser_action_receipt(
    body: BrowserActionReceiptClaim,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "eq.running", "lease_owner": f"eq.{body.worker_id}",
        "lease_expires_at": "gt." + datetime.now(timezone.utc).isoformat(),
        "select": "id,lease_owner,lease_expires_at", "limit": "1",
    })
    if not runs:
        raise HTTPException(409, "browser_action_worker_lease_not_held")
    existing = await repo.select("moreai_browser_action_receipts", {
        "run_id": f"eq.{body.run_id}", "action_key": f"eq.{body.action_key}",
        "user_id": f"eq.{body.user_id}",
        "select": "id,status,result,error_code,session_id,request_hash", "limit": "1",
    })
    if existing:
        row = existing[0]
        if row.get("request_hash") != body.request_hash:
            raise HTTPException(409, "browser_action_idempotency_key_conflict")
        return {"receipt_id": row["id"], "status": row["status"], "can_execute": False,
                "result": row.get("result"), "error_code": row.get("error_code")}
    try:
        row = await repo.insert("moreai_browser_action_receipts", {
            "run_id": str(body.run_id), "user_id": str(body.user_id),
            "action_key": body.action_key, "request_hash": body.request_hash,
            "action_type": body.action_type, "target_host": body.target_host,
            "status": "executing",
        })
        return {"receipt_id": row["id"], "status": "executing", "can_execute": True,
                "result": None, "error_code": None}
    except HTTPException:
        # A concurrent worker may have claimed the same deterministic action key.
        # Reload canonical state; never execute when the receipt already exists.
        existing = await repo.select("moreai_browser_action_receipts", {
            "run_id": f"eq.{body.run_id}", "action_key": f"eq.{body.action_key}",
            "user_id": f"eq.{body.user_id}",
            "select": "id,status,result,error_code,session_id", "limit": "1",
        })
        if not existing:
            raise
        row = existing[0]
        if row.get("request_hash") != body.request_hash:
            raise HTTPException(409, "browser_action_idempotency_key_conflict")
        return {"receipt_id": row["id"], "status": row["status"], "can_execute": False,
                "result": row.get("result"), "error_code": row.get("error_code")}


@router.post("/internal/actions/{receipt_id}/finish")
async def finish_browser_action_receipt(
    receipt_id: UUID,
    body: BrowserActionReceiptFinish,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "eq.running", "lease_owner": f"eq.{body.worker_id}",
        "lease_expires_at": "gt." + datetime.now(timezone.utc).isoformat(),
        "select": "id,lease_owner,lease_expires_at", "limit": "1",
    })
    if not runs:
        raise HTTPException(409, "browser_action_worker_lease_not_held")
    result = body.result or {}
    if len(json.dumps(result, separators=(",", ":"), ensure_ascii=True).encode()) > 65536:
        raise HTTPException(413, "browser_action_receipt_result_too_large")
    update: dict[str, Any] = {
        "status": body.status,
        "result": result if body.status == "succeeded" else None,
        "error_code": body.error_code,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    if body.session_id:
        update["session_id"] = str(body.session_id)
    rows = await repo.update("moreai_browser_action_receipts", {
        "id": f"eq.{receipt_id}", "run_id": f"eq.{body.run_id}",
        "user_id": f"eq.{body.user_id}", "status": "eq.executing",
    }, update)
    if rows:
        return {"receipt_id": str(receipt_id), "status": body.status}
    current = await repo.select("moreai_browser_action_receipts", {
        "id": f"eq.{receipt_id}", "run_id": f"eq.{body.run_id}",
        "user_id": f"eq.{body.user_id}",
        "select": "id,status", "limit": "1",
    })
    if not current:
        raise HTTPException(404, "browser_action_receipt_not_found")
    if current[0]["status"] == body.status:
        return {"receipt_id": str(receipt_id), "status": body.status, "replayed": True}
    raise HTTPException(409, "browser_action_receipt_already_finalized")



@router.post("/internal/takeover-grants/{grant_id}/input-result")
async def audit_browser_takeover_input(
    grant_id: UUID,
    body: BrowserTakeoverInputAudit,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    grants = await repo.select("moreai_browser_takeover_grants", {
        "id": f"eq.{grant_id}", "session_id": f"eq.{body.session_id}",
        "user_id": f"eq.{body.user_id}", "consumed_by_worker": f"eq.{body.worker_id}",
        "consumed_at": "not.is.null",
        "select": "id,session_id,user_id", "limit": "1",
    })
    if not grants:
        raise HTTPException(404, "browser_takeover_grant_audit_target_not_found")
    await repo.insert("moreai_browser_session_events", {
        "session_id": str(body.session_id), "user_id": str(body.user_id),
        "event_type": "takeover_input_succeeded" if body.status == "succeeded" else "takeover_input_failed",
        "metadata": {"grant_id": str(grant_id), "worker_id": body.worker_id,
                     "error_code": body.error_code if body.status == "failed" else None},
    })
    return {"grant_id": str(grant_id), "status": body.status}


@router.post("/takeover-grants/revoke-all")
async def revoke_all_customer_browser_takeover_grants(
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Revoke all unconsumed browser takeover grants before the customer signs out."""
    result = await repository(request).rpc(
        "moreai_revoke_user_browser_takeover_grants",
        {"p_user_id": str(user["id"])},
    )
    if not isinstance(result, int) or result < 0:
        raise HTTPException(503, "browser_takeover_logout_revoke_contract_invalid")
    return {"revoked": result}


@router.get("/history")
async def list_browser_session_history(
    request: Request,
    limit: int = 50,
    user: dict[str, Any] = Depends(customer_principal),
):
    if not 1 <= limit <= 100:
        raise HTTPException(422, "browser_session_history_limit_invalid")
    repo = repository(request)
    sessions = await repo.select("moreai_browser_sessions", {
        "user_id": f"eq.{user['id']}",
        "select": "id,run_id,last_run_id,origin_host,status,created_at,last_used_at,expires_at,closed_at,profile_retention_after,profile_deleted_at",
        "order": "last_used_at.desc,id.desc",
        "limit": str(limit),
    })
    events = await repo.select("moreai_browser_session_events", {
        "user_id": f"eq.{user['id']}",
        "select": "id,session_id,event_type,metadata,created_at",
        "order": "created_at.desc,id.desc",
        "limit": str(min(limit * 10, 500)),
    })
    by_session: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        key = str(event.get("session_id") or "")
        if key:
            by_session.setdefault(key, []).append(event)
    for session in sessions:
        session["events"] = by_session.get(str(session["id"]), [])
    return {"items": sessions}


@router.get("")
async def list_browser_sessions(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    rows = await repository(request).select("moreai_browser_sessions", {
        "user_id": f"eq.{user['id']}",
        "select": "id,run_id,last_run_id,origin_host,status,created_at,last_used_at,expires_at",
        "order": "last_used_at.desc,id.desc", "limit": "50",
    })
    return {"items": rows}


@router.post("/{session_id}/takeover-grants")
async def create_browser_takeover_grant(
    session_id: UUID,
    body: BrowserTakeoverGrantCreate,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    sessions = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "status": "eq.active", "expires_at": "gt." + datetime.now(timezone.utc).isoformat(),
        "select": "id,user_id,expires_at", "limit": "1",
    })
    if not sessions:
        raise HTTPException(404, "browser_session_not_active_or_not_owned")
    token = secrets.token_urlsafe(48)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=body.ttl_seconds)
    row = await repo.insert("moreai_browser_takeover_grants", {
        "session_id": str(session_id), "user_id": str(user["id"]),
        "token_sha256": digest, "scopes": ["browser.input"],
        "expires_at": expires_at.isoformat(),
    })
    await repo.insert("moreai_browser_session_events", {
        "session_id": str(session_id), "user_id": str(user["id"]),
        "event_type": "takeover_grant_created",
        "metadata": {"grant_id": row["id"], "expires_at": expires_at.isoformat(), "scopes": ["browser.input"]},
    })
    # The bearer secret is returned once; only its SHA-256 digest is persisted.
    return {"grant_id": row["id"], "token": token, "session_id": str(session_id),
            "scopes": ["browser.input"], "expires_at": expires_at.isoformat()}


@router.delete("/{session_id}/takeover-grants")
async def revoke_browser_takeover_grants(
    session_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    sessions = await repository(request).select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "select": "id", "limit": "1",
    })
    if not sessions:
        raise HTTPException(404, "browser_session_not_found")
    count = await repository(request).rpc("moreai_revoke_browser_takeover_grants", {
        "p_session_id": str(session_id), "p_user_id": str(user["id"]),
    })
    if not isinstance(count, int):
        raise HTTPException(503, "browser_takeover_revoke_contract_invalid")
    return {"session_id": str(session_id), "revoked": count}


@router.post("/{session_id}/takeover-input", status_code=202)
async def enqueue_browser_takeover_input(
    session_id: UUID,
    body: BrowserTakeoverCommandCreate,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Persist one bounded human input command under an encrypted, one-time grant."""
    payload_bytes = json.dumps(body.input, separators=(",", ":"), ensure_ascii=True).encode()
    if not body.input or len(payload_bytes) > 16_384:
        raise HTTPException(413, "browser_takeover_input_invalid")
    now = datetime.now(timezone.utc)
    repo = repository(request)
    sessions = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "status": "eq.active", "expires_at": "gt." + now.isoformat(),
        "select": "id", "limit": "1",
    })
    if not sessions:
        raise HTTPException(404, "browser_session_not_active_or_not_owned")
    digest = hashlib.sha256(body.grant_token.encode("utf-8")).hexdigest()
    grants = await repo.select("moreai_browser_takeover_grants", {
        "session_id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "token_sha256": f"eq.{digest}", "consumed_at": "is.null", "revoked_at": "is.null",
        "expires_at": "gt." + now.isoformat(),
        "select": "id,expires_at", "limit": "1",
    })
    if not grants:
        raise HTTPException(409, "browser_takeover_grant_invalid_expired_or_consumed")
    grant = grants[0]
    encrypted = _encrypt(request, {
        "grant_token": body.grant_token,
        "input": body.input,
    })
    try:
        command = await repo.insert("moreai_browser_takeover_commands", {
            "session_id": str(session_id), "user_id": str(user["id"]),
            "grant_id": grant["id"], "encrypted_command": encrypted,
            "status": "queued",
        })
    except HTTPException as exc:
        # One grant is intentionally bound to one command; callers must request a
        # fresh grant after an ambiguous/rejected submission.
        raise HTTPException(409, "browser_takeover_grant_already_submitted") from exc
    await repo.insert("moreai_browser_session_events", {
        "session_id": str(session_id), "user_id": str(user["id"]),
        "event_type": "takeover_command_queued",
        "metadata": {"command_id": command["id"], "grant_id": grant["id"], "input_bytes": len(payload_bytes)},
    })
    return {"command_id": command["id"], "session_id": str(session_id), "status": "queued"}


@router.get("/takeover-input/{command_id}")
async def get_browser_takeover_command(
    command_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    rows = await repository(request).select("moreai_browser_takeover_commands", {
        "id": f"eq.{command_id}", "user_id": f"eq.{user['id']}",
        "select": "id,session_id,status,error_code,created_at,claimed_at,finished_at",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "browser_takeover_command_not_found")
    row = rows[0]
    # Match the enqueue response and typed Customer API contract.
    return {
        "command_id": row["id"],
        "session_id": row["session_id"],
        "status": row["status"],
        "error_code": row.get("error_code"),
        "created_at": row["created_at"],
        "claimed_at": row.get("claimed_at"),
        "finished_at": row.get("finished_at"),
    }


@router.get("/internal/takeover-commands/claim")
async def claim_browser_takeover_commands(
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
    x_moreai_worker_id: str | None = Header(default=None, alias="X-MoreAI-Worker-Id"),
):
    _worker_auth(request, x_moreai_worker_token)
    if not x_moreai_worker_id or not __import__("re").fullmatch(r"[A-Za-z0-9._:-]{8,128}", x_moreai_worker_id):
        raise HTTPException(422, "worker_id_invalid")
    rows = await repository(request).rpc("moreai_claim_browser_takeover_commands", {
        "p_worker_id": x_moreai_worker_id, "p_limit": 10,
    })
    if not isinstance(rows, list):
        raise HTTPException(503, "browser_takeover_command_claim_contract_invalid")
    items = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        command = _decrypt(request, row.get("encrypted_command"))
        token, input_payload = command.get("grant_token"), command.get("input")
        if not isinstance(token, str) or not isinstance(input_payload, dict):
            raise HTTPException(503, "browser_takeover_command_payload_invalid")
        items.append({
            "command_id": str(row["id"]), "session_id": str(row["session_id"]),
            "grant_token": token, "input": input_payload,
        })
    return {"items": items}


@router.post("/internal/takeover-commands/{command_id}/finish")
async def finish_browser_takeover_command(
    command_id: UUID,
    body: BrowserTakeoverCommandFinish,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
    x_moreai_worker_id: str | None = Header(default=None, alias="X-MoreAI-Worker-Id"),
):
    _worker_auth(request, x_moreai_worker_token)
    if not x_moreai_worker_id:
        raise HTTPException(422, "worker_id_required")
    result = await repository(request).rpc("moreai_finish_browser_takeover_command", {
        "p_command_id": str(command_id), "p_worker_id": x_moreai_worker_id,
        "p_status": body.status, "p_result": body.result,
        "p_error_code": body.error_code,
    })
    if not isinstance(result, dict) or result.get("status") != body.status:
        raise HTTPException(409, "browser_takeover_command_finish_contract_invalid")
    return result


@router.post("/internal/takeover-grants/consume")
async def consume_browser_takeover_grant(
    body: BrowserTakeoverGrantConsume,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    digest = hashlib.sha256(body.token.encode("utf-8")).hexdigest()
    result = await repository(request).rpc("moreai_consume_browser_takeover_grant", {
        "p_token_sha256": digest, "p_worker_id": body.worker_id,
    })
    if not isinstance(result, dict) or result.get("status") != "consumed":
        raise HTTPException(409, "browser_takeover_grant_invalid_expired_or_consumed")
    return result


@router.get("/{session_id}/state")
async def get_browser_session_reconnect_state(
    session_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Restore owner-scoped session, preview command and lease outcome after a page reload."""
    repo = repository(request)
    sessions = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "select": "id,run_id,last_run_id,origin_host,status,created_at,last_used_at,expires_at,closed_at,profile_retention_after,profile_deleted_at",
        "limit": "1",
    })
    if not sessions:
        raise HTTPException(404, "browser_session_not_found")
    session = sessions[0]
    now = datetime.now(timezone.utc)
    try:
        expires_at = datetime.fromisoformat(str(session["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(503, "browser_session_expiry_metadata_invalid") from exc
    effective_status = session.get("status")
    if effective_status == "active" and expires_at <= now:
        effective_status = "expired"
    requests = await repo.select("moreai_browser_preview_requests", {
        "session_id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "select": "id,scope,status,artifact_id,error_code,created_at,claimed_at,finished_at",
        "order": "created_at.desc,id.desc", "limit": "1",
    })
    latest_request = requests[0] if requests else None
    preview = None
    if (
        effective_status == "active" and latest_request
        and latest_request.get("status") == "succeeded"
        and isinstance(latest_request.get("artifact_id"), str)
    ):
        artifacts = await repo.select("artifacts", {
            "id": f"eq.{latest_request['artifact_id']}",
            "user_id": f"eq.{user['id']}",
            "metadata->>source": "eq.openfuse_browser_screenshot",
            "metadata->>session_id": f"eq.{session_id}",
            "mime_type": "eq.image/png",
            "select": "id,run_id,mime_type,size_bytes,checksum_sha256,created_at",
            "limit": "1",
        })
        if artifacts:
            artifact = artifacts[0]
            preview = {
                "artifact_id": artifact["id"], "run_id": artifact.get("run_id"),
                "mime_type": artifact["mime_type"], "size_bytes": artifact["size_bytes"],
                "checksum_sha256": artifact.get("checksum_sha256"),
                "created_at": artifact["created_at"],
            }
    events = await repo.select("moreai_browser_session_events", {
        "session_id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "select": "id,event_type,metadata,created_at",
        "order": "created_at.desc,id.desc", "limit": "50",
    })
    return {
        "session": {**session, "effective_status": effective_status},
        "preview_request": latest_request,
        "preview": preview,
        "events": events,
    }


@router.post("/{session_id}/preview-requests", status_code=202)
async def request_browser_session_preview(
    session_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Queue a screenshot refresh under the distinct browser.preview capability."""
    repo = repository(request)
    sessions = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "status": "eq.active", "expires_at": "gt." + datetime.now(timezone.utc).isoformat(),
        "select": "id,run_id,last_run_id", "limit": "1",
    })
    if not sessions:
        raise HTTPException(404, "browser_session_not_active_or_not_owned")
    session = sessions[0]
    run_id = session.get("last_run_id") or session.get("run_id")
    if not run_id:
        raise HTTPException(409, "browser_preview_run_context_missing")
    runs = await repo.select("agent_runs", {
        "id": f"eq.{run_id}", "user_id": f"eq.{user['id']}",
        "status": "in.(running,succeeded)", "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(409, "browser_preview_run_context_unavailable")
    recent = await repo.select("moreai_browser_preview_requests", {
        "session_id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "status": "in.(queued,processing)",
        "select": "id,status,created_at", "order": "created_at.desc", "limit": "1",
    })
    if recent:
        return {"request_id": recent[0]["id"], "session_id": str(session_id),
                "scope": "browser.preview", "status": recent[0]["status"], "reused": True}
    row = await repo.insert("moreai_browser_preview_requests", {
        "session_id": str(session_id), "user_id": str(user["id"]),
        "run_id": str(run_id), "scope": "browser.preview", "status": "queued",
    })
    await repo.insert("moreai_browser_session_events", {
        "session_id": str(session_id), "user_id": str(user["id"]),
        "event_type": "preview_requested",
        "metadata": {"request_id": row["id"], "scope": "browser.preview"},
    })
    return {"request_id": row["id"], "session_id": str(session_id),
            "scope": "browser.preview", "status": "queued", "reused": False}


@router.get("/preview-requests/{request_id}")
async def get_browser_preview_request(
    request_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    rows = await repository(request).select("moreai_browser_preview_requests", {
        "id": f"eq.{request_id}", "user_id": f"eq.{user['id']}",
        "select": "id,session_id,scope,status,artifact_id,error_code,created_at,claimed_at,finished_at",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "browser_preview_request_not_found")
    return rows[0]


@router.get("/internal/preview-requests/claim")
async def claim_browser_preview_requests(
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
    x_moreai_worker_id: str | None = Header(default=None, alias="X-MoreAI-Worker-Id"),
):
    _worker_auth(request, x_moreai_worker_token)
    if not x_moreai_worker_id or not __import__("re").fullmatch(r"[A-Za-z0-9._:-]{8,128}", x_moreai_worker_id):
        raise HTTPException(422, "worker_id_invalid")
    rows = await repository(request).rpc("moreai_claim_browser_preview_requests", {
        "p_worker_id": x_moreai_worker_id, "p_limit": 5,
    })
    if not isinstance(rows, list):
        raise HTTPException(503, "browser_preview_claim_contract_invalid")
    return {"items": [
        {"request_id": str(row["id"]), "session_id": str(row["session_id"]),
         "run_id": str(row["run_id"]), "user_id": str(row["user_id"]),
         "scope": row["scope"]}
        for row in rows if isinstance(row, dict)
    ]}


class BrowserPreviewRequestFinish(BaseModel):
    status: Literal["succeeded", "failed"]
    artifact_id: UUID | None = None
    error_code: str | None = Field(default=None, max_length=100)


@router.post("/internal/preview-requests/{request_id}/finish")
async def finish_browser_preview_request(
    request_id: UUID,
    body: BrowserPreviewRequestFinish,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
    x_moreai_worker_id: str | None = Header(default=None, alias="X-MoreAI-Worker-Id"),
):
    _worker_auth(request, x_moreai_worker_token)
    if not x_moreai_worker_id:
        raise HTTPException(422, "worker_id_required")
    result = await repository(request).rpc("moreai_finish_browser_preview_request", {
        "p_request_id": str(request_id), "p_worker_id": x_moreai_worker_id,
        "p_status": body.status,
        "p_artifact_id": str(body.artifact_id) if body.artifact_id else None,
        "p_error_code": body.error_code,
    })
    if not isinstance(result, dict) or result.get("status") != body.status:
        raise HTTPException(409, "browser_preview_finish_contract_invalid")
    return result


@router.post("/{session_id}/close")
async def close_browser_session(session_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    result = await repository(request).rpc("moreai_request_browser_session_close", {
        "p_session_id": str(session_id), "p_user_id": str(user["id"]),
        "p_source": "customer", "p_reason": None,
    })
    if not isinstance(result, dict) or result.get("status") not in {"close_requested", "closed"}:
        raise HTTPException(503, "browser_session_close_request_contract_invalid")
    return result


@router.post("/internal/acquire")
async def acquire_browser_session(body: SessionAcquire, request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token")):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "eq.running", "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "browser_session_run_owner_or_status_mismatch")
    now = datetime.now(timezone.utc)
    created_new = False
    if body.session_id:
        rows = await repo.select("moreai_browser_sessions", {
            "id": f"eq.{body.session_id}", "user_id": f"eq.{body.user_id}",
            "status": "eq.active", "select": "id,origin_host,encrypted_state,expires_at,last_used_at", "limit": "1",
        })
        if not rows:
            raise HTTPException(404, "browser_session_not_found")
        row = rows[0]
        expiry = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
        last = datetime.fromisoformat(str(row["last_used_at"]).replace("Z", "+00:00"))
        if expiry <= now or last + timedelta(minutes=IDLE_TTL_MINUTES) <= now:
            await repo.rpc("moreai_request_browser_session_close", {
                "p_session_id": str(body.session_id), "p_user_id": str(body.user_id),
                "p_source": "acquire_guard", "p_reason": "ttl_or_idle",
            })
            raise HTTPException(410, "browser_session_expired_close_queued")
        # OpenFuse's isolated worker applies public-destination/DNS checks per request.
        # Keep the latest host as session metadata; cross-host navigation is allowed.
        session_id = str(body.session_id)
        state = _decrypt(request, row.get("encrypted_state"))
        event = "restored"
    else:
        session_id = str(uuid4())
        expiry = now + timedelta(hours=SESSION_TTL_HOURS)
        await repo.insert("moreai_browser_sessions", {
            "id": session_id, "user_id": str(body.user_id), "run_id": str(body.run_id),
            "origin_host": body.origin_host, "status": "active", "encrypted_state": None,
            "expires_at": expiry.isoformat(), "last_used_at": now.isoformat(),
        })
        created_new = True
        state = {}
        event = "created"
    await repo.update("moreai_browser_sessions", {"id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}", "status": "eq.active"}, {
        "origin_host": body.origin_host, "last_used_at": now.isoformat(), "last_run_id": str(body.run_id),
    })
    await repo.insert("moreai_browser_session_events", {
        "session_id": session_id, "user_id": str(body.user_id), "event_type": event,
        "metadata": {"run_id": str(body.run_id), "origin_host": body.origin_host},
    })
    capacity: dict[str, Any] | None = None
    if body.action not in {"close", "downloads"}:
        capacity_result = await repo.rpc("moreai_acquire_browser_capacity_lease", {
            "p_session_id": session_id,
            "p_user_id": str(body.user_id),
            "p_worker_id": body.worker_id,
            "p_lease_seconds": 660,
        })
        if not isinstance(capacity_result, dict) or capacity_result.get("acquired") is not True:
            if created_new:
                try:
                    await repo.rpc("moreai_request_browser_session_close", {
                        "p_session_id": session_id, "p_user_id": str(body.user_id),
                        "p_source": "acquire_guard", "p_reason": None,
                    })
                except HTTPException:
                    pass
            reason = capacity_result.get("reason") if isinstance(capacity_result, dict) else "capacity_lease_unavailable"
            raise HTTPException(429, "browser_capacity_limit_reached:" + str(reason))
        capacity = capacity_result
    return {
        "session_id": session_id,
        "storage_state": state,
        "expires_at": expiry.isoformat(),
        "capacity_lease_token": capacity.get("lease_token") if capacity else None,
        "capacity_lease_expires_at": capacity.get("expires_at") if capacity else None,
    }


@router.post("/internal/{session_id}/closed")
async def mark_browser_session_closed(
    session_id: UUID,
    body: SessionWorkerClose,
    request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token"),
):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "in.(running,succeeded,failed,cancelled,expired)",
        "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "browser_session_run_owner_or_status_mismatch")
    result = await repo.rpc("moreai_mark_browser_session_closed", {
        "p_session_id": str(session_id), "p_user_id": str(body.user_id),
        "p_run_id": str(body.run_id),
    })
    if not isinstance(result, dict) or result.get("status") != "closed":
        raise HTTPException(503, "browser_session_close_contract_invalid")
    return result


@router.put("/internal/{session_id}/state")
async def save_browser_session_state(session_id: UUID, body: SessionStateUpdate, request: Request,
    x_moreai_worker_token: str | None = Header(default=None, alias="X-MoreAI-Worker-Token")):
    _worker_auth(request, x_moreai_worker_token)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{body.run_id}", "user_id": f"eq.{body.user_id}",
        "status": "in.(running,completed)", "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "browser_session_run_owner_or_status_mismatch")
    now = datetime.now(timezone.utc)
    rows = await repo.update("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}", "status": "eq.active",
        "expires_at": f"gt.{now.isoformat()}",
    }, {"encrypted_state": _encrypt(request, body.storage_state), "last_used_at": now.isoformat()})
    if not rows:
        raise HTTPException(404, "browser_session_not_active")
    await repo.insert("moreai_browser_session_events", {
        "session_id": str(session_id), "user_id": str(body.user_id), "event_type": "state_saved",
        "metadata": {"run_id": str(body.run_id), "state_bytes": len(json.dumps(body.storage_state).encode())},
    })
    return {"session_id": str(session_id), "status": "saved", "updated_at": now.isoformat()}
