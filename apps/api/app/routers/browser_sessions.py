from __future__ import annotations

import json
import os
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
    action_key: str = Field(pattern=r"^[0-9a-f]{64}$")
    request_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    action_type: Literal["navigate", "extract", "input", "screenshot", "close", "downloads"]
    target_host: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")


class BrowserActionReceiptFinish(BaseModel):
    run_id: UUID
    user_id: UUID
    status: Literal["succeeded", "failed", "unknown"]
    session_id: UUID | None = None
    result: dict[str, Any] | None = None
    error_code: str | None = Field(default=None, max_length=100)


class SessionAcquire(BaseModel):
    run_id: UUID
    user_id: UUID
    session_id: UUID | None = None
    origin_host: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")


class SessionWorkerClose(BaseModel):
    run_id: UUID
    user_id: UUID


class SessionWorkerOwner(BaseModel):
    user_id: UUID


class SessionStateUpdate(BaseModel):
    run_id: UUID
    user_id: UUID
    storage_state: dict[str, Any]


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
    """Turn TTL/idle expiry into durable close work; the isolated worker owns Chromium cleanup."""
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
        changed = await repo.update("moreai_browser_sessions", {
            "id": f"eq.{row['id']}", "user_id": f"eq.{row['user_id']}", "status": "eq.active",
        }, {"status": "close_requested"})
        if not changed:
            continue
        await repo.insert("moreai_browser_session_events", {
            "session_id": str(row["id"]), "user_id": str(row["user_id"]),
            "event_type": "close_requested", "metadata": {"source": "ttl_reconciler", "reason": reason},
        })
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
    total = await repo.count("moreai_browser_sessions", {})
    # Bound the response and explicitly signal incompleteness. The worker must
    # never run destructive reconciliation from a partial ownership inventory.
    if total > 10000:
        return {"items": [], "complete": False, "total": total}
    page_size = 500
    rows: list[dict[str, Any]] = []
    for offset in range(0, total, page_size):
        page = await repo.select("moreai_browser_sessions", {
            "select": "id", "order": "id.asc",
            "limit": str(page_size), "offset": str(offset),
        })
        if len(page) != min(page_size, total - offset):
            raise HTTPException(503, "browser_profile_ownership_inventory_incomplete")
        rows.extend(page)
    if len(rows) != total:
        raise HTTPException(503, "browser_profile_ownership_inventory_incomplete")
    return {"items": [str(row["id"]) for row in rows if row.get("id")], "complete": True, "total": total}


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
    repo = repository(request)
    rows = await repo.update("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}",
        "status": "eq.close_requested",
    }, {
        "status": "closed", "encrypted_state": None,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    })
    if rows:
        await repo.insert("moreai_browser_session_events", {
            "session_id": str(session_id), "user_id": str(body.user_id),
            "event_type": "closed", "metadata": {"source": "worker_reconciler"},
        })
        return {"session_id": str(session_id), "status": "closed"}
    current = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}",
        "select": "id,status", "limit": "1",
    })
    if current and current[0].get("status") == "closed":
        return {"session_id": str(session_id), "status": "closed", "replayed": True}
    raise HTTPException(404, "browser_session_close_request_not_found")


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
        "status": "eq.running", "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "browser_action_run_owner_or_status_mismatch")
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
        "status": "in.(running,succeeded,failed,cancelled,expired)",
        "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "browser_action_run_owner_or_status_mismatch")
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
        "select": "id,run_id,last_run_id,origin_host,status,created_at,last_used_at,expires_at,closed_at",
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
        "user_id": f"eq.{user['id']}", "status": "in.(active,close_requested)",
        "select": "id,run_id,last_run_id,origin_host,status,created_at,last_used_at,expires_at",
        "order": "last_used_at.desc", "limit": "50",
    })
    return {"items": rows}


@router.post("/{session_id}/close")
async def close_browser_session(session_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    repo = repository(request)
    rows = await repo.update("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}", "status": "eq.active",
    }, {"status": "close_requested"})
    if rows:
        await repo.insert("moreai_browser_session_events", {
            "session_id": str(session_id), "user_id": user["id"],
            "event_type": "close_requested", "metadata": {"source": "customer"},
        })
        return {"session_id": str(session_id), "status": "close_requested"}
    current = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}",
        "select": "id,status", "limit": "1",
    })
    if current and current[0].get("status") in {"close_requested", "closed"}:
        return {"session_id": str(session_id), "status": current[0]["status"], "replayed": True}
    raise HTTPException(404, "browser_session_not_found")


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
            changed = await repo.update("moreai_browser_sessions", {
                "id": f"eq.{body.session_id}", "user_id": f"eq.{body.user_id}", "status": "eq.active",
            }, {"status": "close_requested"})
            if changed:
                await repo.insert("moreai_browser_session_events", {
                    "session_id": str(body.session_id), "user_id": str(body.user_id),
                    "event_type": "close_requested",
                    "metadata": {"source": "acquire_guard", "reason": "ttl_or_idle"},
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
        state = {}
        event = "created"
    await repo.update("moreai_browser_sessions", {"id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}", "status": "eq.active"}, {
        "origin_host": body.origin_host, "last_used_at": now.isoformat(), "last_run_id": str(body.run_id),
    })
    await repo.insert("moreai_browser_session_events", {
        "session_id": session_id, "user_id": str(body.user_id), "event_type": event,
        "metadata": {"run_id": str(body.run_id), "origin_host": body.origin_host},
    })
    return {"session_id": session_id, "storage_state": state, "expires_at": expiry.isoformat()}


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
    rows = await repo.update("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}",
        "status": "in.(active,close_requested)",
    }, {
        "status": "closed", "encrypted_state": None,
        "closed_at": datetime.now(timezone.utc).isoformat(),
    })
    if rows:
        await repo.insert("moreai_browser_session_events", {
            "session_id": str(session_id), "user_id": str(body.user_id),
            "event_type": "closed", "metadata": {"source": "worker", "run_id": str(body.run_id)},
        })
        return {"session_id": str(session_id), "status": "closed"}
    current = await repo.select("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{body.user_id}",
        "select": "id,status", "limit": "1",
    })
    if current and current[0].get("status") == "closed":
        return {"session_id": str(session_id), "status": "closed", "replayed": True}
    raise HTTPException(404, "browser_session_not_active")


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
