from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
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


class SessionAcquire(BaseModel):
    run_id: UUID
    user_id: UUID
    session_id: UUID | None = None
    origin_host: str = Field(min_length=1, max_length=253, pattern=r"^[A-Za-z0-9.-]+$")


class SessionStateUpdate(BaseModel):
    run_id: UUID
    user_id: UUID
    storage_state: dict[str, Any]


@router.get("")
async def list_browser_sessions(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    rows = await repository(request).select("moreai_browser_sessions", {
        "user_id": f"eq.{user['id']}", "status": "eq.active",
        "select": "id,run_id,last_run_id,origin_host,status,created_at,last_used_at,expires_at",
        "order": "last_used_at.desc", "limit": "50",
    })
    return {"items": rows}


@router.post("/{session_id}/close")
async def close_browser_session(session_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    rows = await repository(request).update("moreai_browser_sessions", {
        "id": f"eq.{session_id}", "user_id": f"eq.{user['id']}", "status": "eq.active",
    }, {"status": "closed", "encrypted_state": None, "closed_at": datetime.now(timezone.utc).isoformat()})
    if not rows:
        raise HTTPException(404, "browser_session_not_found")
    await repository(request).insert("moreai_browser_session_events", {
        "session_id": str(session_id), "user_id": user["id"], "event_type": "closed", "metadata": {"source": "customer"},
    })
    return {"session_id": str(session_id), "status": "closed"}


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
            await repo.update("moreai_browser_sessions", {"id": f"eq.{body.session_id}", "user_id": f"eq.{body.user_id}"}, {
                "status": "expired", "encrypted_state": None,
            })
            await repo.insert("moreai_browser_session_events", {
                "session_id": str(body.session_id), "user_id": str(body.user_id), "event_type": "expired", "metadata": {"reason": "ttl"},
            })
            raise HTTPException(410, "browser_session_expired")
        if row["origin_host"] != body.origin_host:
            raise HTTPException(409, "browser_session_origin_mismatch")
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
        "last_used_at": now.isoformat(), "last_run_id": str(body.run_id),
    })
    await repo.insert("moreai_browser_session_events", {
        "session_id": session_id, "user_id": str(body.user_id), "event_type": event,
        "metadata": {"run_id": str(body.run_id), "origin_host": body.origin_host},
    })
    return {"session_id": session_id, "storage_state": state, "expires_at": expiry.isoformat()}


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
