from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from email.message import EmailMessage
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from urllib.parse import urlencode
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/connections", tags=["customer-connections"])

GOOGLE_SCOPE_MAP = {
    "gmail.read": "https://www.googleapis.com/auth/gmail.readonly",
    "gmail.send": "https://www.googleapis.com/auth/gmail.send",
    "calendar.read": "https://www.googleapis.com/auth/calendar.readonly",
    "calendar.write": "https://www.googleapis.com/auth/calendar.events",
}
GOOGLE_ALLOWED_SCOPES = set(GOOGLE_SCOPE_MAP.values())
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


class GoogleAuthorizeRequest(BaseModel):
    permissions: list[Literal["gmail.read", "gmail.send", "calendar.read", "calendar.write"]] = Field(min_length=1, max_length=4)



class GmailSendRequest(BaseModel):
    to: list[str] = Field(min_length=1, max_length=5)
    subject: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1, max_length=20000)
    confirmed: bool = False


class CalendarCreateRequest(BaseModel):
    summary: str = Field(min_length=1, max_length=240)
    description: str = Field(default="", max_length=4000)
    start: datetime
    end: datetime
    timezone: str = Field(default="Asia/Jakarta", max_length=64)
    confirmed: bool = False


class ConnectionSummary(BaseModel):
    id: UUID
    provider: str
    display_name: str | None = None
    scopes: list[str]
    status: str
    access_token_expires_at: datetime | None = None
    token_updated_at: datetime


def _crypto_key(version: int) -> bytes:
    raw_keyring = os.getenv("MOREAI_CONNECTIONS_ENCRYPTION_KEYS", "")
    keyring: dict[str, str] = {}
    if raw_keyring:
        try:
            parsed = json.loads(raw_keyring)
            if isinstance(parsed, dict):
                keyring = {str(key): value for key, value in parsed.items() if isinstance(value, str)}
        except Exception as exc:
            raise HTTPException(503, "connections_encryption_keyring_invalid") from exc
    if not keyring and os.getenv("MOREAI_CONNECTIONS_ENCRYPTION_KEY"):
        keyring["1"] = os.environ["MOREAI_CONNECTIONS_ENCRYPTION_KEY"]
    encoded = keyring.get(str(version))
    if not encoded:
        raise HTTPException(503, "connections_encryption_key_version_unavailable")
    try:
        key = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except Exception as exc:
        raise HTTPException(503, "connections_encryption_key_invalid") from exc
    if len(key) != 32:
        raise HTTPException(503, "connections_encryption_key_must_be_32_bytes")
    return key


def _active_key_version() -> int:
    try:
        version = int(os.getenv("MOREAI_CONNECTIONS_ACTIVE_KEY_VERSION", "1"))
    except ValueError as exc:
        raise HTTPException(503, "connections_active_key_version_invalid") from exc
    if version < 1:
        raise HTTPException(503, "connections_active_key_version_invalid")
    return version


def _encrypt(value: dict[str, Any], aad: str) -> str:
    version = _active_key_version()
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(_crypto_key(version)).encrypt(nonce, json.dumps(value, separators=(",", ":")).encode(), aad.encode())
    return f"v{version}." + base64.urlsafe_b64encode(nonce + ciphertext).decode().rstrip("=")


def _decrypt(value: str, aad: str) -> dict[str, Any]:
    match = re.fullmatch(r"v(\d+)\.([A-Za-z0-9_-]+)", value)
    if not match:
        raise HTTPException(409, "connection_credential_version_unsupported")
    version = int(match.group(1))
    try:
        encoded = match.group(2)
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        plaintext = AESGCM(_crypto_key(version)).decrypt(raw[:12], raw[12:], aad.encode())
        decoded = json.loads(plaintext)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(503, "connection_credential_decryption_failed") from exc
    if not isinstance(decoded, dict):
        raise HTTPException(503, "connection_credential_payload_invalid")
    return decoded


def _google_config() -> tuple[str, str, str]:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")
    if not client_id or not client_secret or not redirect_uri.startswith("https://"):
        raise HTTPException(503, "google_oauth_not_configured")
    return client_id, client_secret, redirect_uri


def _safe_connection(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"], "provider": row["provider"], "display_name": row.get("display_name"),
        "scopes": row.get("scopes") or [], "status": row.get("status"),
        "access_token_expires_at": row.get("access_token_expires_at"),
        "token_updated_at": row.get("token_updated_at"),
    }


@router.get("", response_model=list[ConnectionSummary])
async def list_connections(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    rows = await repository(request).select("moreai_connections", {
        "user_id": f"eq.{user['id']}", "select": "id,provider,display_name,scopes,status,access_token_expires_at,token_updated_at",
        "order": "updated_at.desc", "limit": "100",
    })
    return [_safe_connection(row) for row in rows]


@router.post("/google/authorize")
async def begin_google_oauth(body: GoogleAuthorizeRequest, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    client_id, _, redirect_uri = _google_config()
    scopes = sorted({GOOGLE_SCOPE_MAP[key] for key in body.permissions})
    state = secrets.token_urlsafe(32)
    state_hash = hashlib.sha256(state.encode()).hexdigest()
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    repo = repository(request)
    await repo.insert("moreai_oauth_states", {
        "state_hash": state_hash, "user_id": user["id"], "provider": "google",
        "scopes": scopes, "pkce_verifier_ciphertext": _encrypt({"verifier": verifier}, "oauth-state:" + str(user["id"])),
        "redirect_uri": redirect_uri, "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    })
    await repo.insert("moreai_connection_audit", {
        "user_id": user["id"], "provider": "google", "event_type": "oauth_started",
        "scopes": scopes, "detail": {"pkce": "S256", "state_ttl_seconds": 600},
    })
    params = {
        "client_id": client_id, "redirect_uri": redirect_uri, "response_type": "code",
        "scope": " ".join(["openid", "email", "profile", *scopes]),
        "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true",
        "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
    }
    return {"authorization_url": GOOGLE_AUTHORIZE_URL + "?" + urlencode(params), "expires_in": 600, "permissions": body.permissions}


@router.get("/google/callback")
async def google_oauth_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    frontend = os.getenv("MOREAI_CUSTOMER_APP_URL", "").rstrip("/")
    target = frontend + "/?view=connections" if frontend else "/?view=connections"
    if error or not code or not state:
        return RedirectResponse(target + "&connection_status=cancelled", status_code=303)
    client_id, client_secret, redirect_uri = _google_config()
    repo = repository(request)
    state_hash = hashlib.sha256(state.encode()).hexdigest()
    try:
        state_record = await repo.rpc("moreai_consume_google_oauth_state", {"p_state_hash": state_hash})
        if not isinstance(state_record, dict):
            raise HTTPException(400, "oauth_state_invalid")
        user_id = str(state_record["user_id"])
        if state_record.get("redirect_uri") != redirect_uri:
            raise HTTPException(400, "oauth_redirect_uri_mismatch")
        verifier_record = _decrypt(state_record["pkce_verifier_ciphertext"], "oauth-state:" + user_id)
        verifier = verifier_record.get("verifier")
        if not isinstance(verifier, str):
            raise HTTPException(400, "oauth_pkce_verifier_missing")
        token_response = await request.app.state.http.post(GOOGLE_TOKEN_URL, data={
            "client_id": client_id, "client_secret": client_secret, "code": code,
            "code_verifier": verifier, "redirect_uri": redirect_uri, "grant_type": "authorization_code",
        }, timeout=20.0, follow_redirects=False)
        if token_response.status_code != 200:
            raise HTTPException(502, "google_token_exchange_failed")
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise HTTPException(502, "google_access_token_missing")
        profile_response = await request.app.state.http.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": "Bearer " + access_token}, timeout=15.0, follow_redirects=False,
        )
        if profile_response.status_code != 200:
            raise HTTPException(502, "google_identity_verification_failed")
        profile = profile_response.json()
        if profile.get("verified_email") is not True or not isinstance(profile.get("id"), str):
            raise HTTPException(403, "google_identity_not_verified")
        scopes = token_data.get("scope", "")
        granted_scopes = sorted(set(scopes.split()) if isinstance(scopes, str) else set(state_record.get("scopes") or []))
        if not set(granted_scopes).issubset(GOOGLE_ALLOWED_SCOPES | {"openid", "email", "profile"}):
            raise HTTPException(403, "google_scope_not_allowlisted")
        prior = await repo.select("moreai_connections", {
            "user_id": f"eq.{user_id}", "provider": "eq.google",
            "external_account_id": f"eq.{profile['id']}",
            "select": "credential_ciphertext", "limit": "1",
        })
        previous_refresh = None
        if prior and isinstance(prior[0].get("credential_ciphertext"), str) and prior[0]["credential_ciphertext"].startswith("v1."):
            previous_refresh = _decrypt(prior[0]["credential_ciphertext"], "connection:google:" + user_id).get("refresh_token")
        credential = {
            "access_token": access_token, "refresh_token": token_data.get("refresh_token") or previous_refresh,
            "token_type": token_data.get("token_type", "Bearer"), "scope": granted_scopes,
        }
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(60, int(token_data.get("expires_in") or 3600)))
        stored = await repo.rpc("moreai_store_google_connection", {
            "p_user_id": user_id, "p_external_account_id": profile["id"],
            "p_display_name": profile.get("email") or profile.get("name"),
            "p_scopes": granted_scopes,
            "p_credential_ciphertext": _encrypt(credential, "connection:google:" + user_id),
            "p_expires_at": expires_at.isoformat(),
        })
        if not isinstance(stored, dict) or not stored.get("id"):
            raise HTTPException(502, "google_connection_persistence_failed")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "google_oauth_callback_failed") from exc
    return RedirectResponse(target + "&connection_status=connected", status_code=303)


async def _owned_google_connection(request: Request, user_id: str, connection_id: UUID) -> dict[str, Any]:
    rows = await repository(request).select("moreai_connections", {
        "id": f"eq.{connection_id}", "user_id": f"eq.{user_id}", "provider": "eq.google",
        "select": "id,user_id,external_account_id,display_name,scopes,status,credential_ciphertext,credential_key_version,access_token_expires_at",
        "limit": "1",
    })
    if not rows or rows[0].get("status") != "connected":
        raise HTTPException(404, "google_connection_not_found")
    return rows[0]


async def _google_access_token(request: Request, connection: dict[str, Any]) -> str:
    user_id = str(connection["user_id"])
    credential = _decrypt(connection["credential_ciphertext"], "connection:google:" + user_id)
    expires = connection.get("access_token_expires_at")
    expires_at = datetime.fromisoformat(expires.replace("Z", "+00:00")) if isinstance(expires, str) else datetime.now(timezone.utc)
    if expires_at > datetime.now(timezone.utc) + timedelta(minutes=2) and isinstance(credential.get("access_token"), str):
        stored_version = int(connection.get("credential_key_version") or 1)
        active_version = _active_key_version()
        if stored_version != active_version:
            await repository(request).update("moreai_connections", {
                "id": f"eq.{connection['id']}", "user_id": f"eq.{user_id}",
            }, {
                "credential_ciphertext": _encrypt(credential, "connection:google:" + user_id),
                "credential_key_version": active_version,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
        return credential["access_token"]
    refresh_token = credential.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        raise HTTPException(409, "google_refresh_token_unavailable_reconnect_required")
    client_id, client_secret, _ = _google_config()
    response = await request.app.state.http.post(GOOGLE_TOKEN_URL, data={
        "client_id": client_id, "client_secret": client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }, timeout=20.0, follow_redirects=False)
    if response.status_code != 200:
        await repository(request).update("moreai_connections", {"id": f"eq.{connection['id']}", "user_id": f"eq.{user_id}"}, {
            "status": "expired", "last_error_code": "google_refresh_failed", "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        raise HTTPException(409, "google_refresh_failed_reconnect_required")
    refreshed = response.json()
    credential["access_token"] = refreshed["access_token"]
    credential["refresh_token"] = refreshed.get("refresh_token") or refresh_token
    new_expiry = datetime.now(timezone.utc) + timedelta(seconds=max(60, int(refreshed.get("expires_in") or 3600)))
    await repository(request).update("moreai_connections", {"id": f"eq.{connection['id']}", "user_id": f"eq.{user_id}"}, {
        "credential_ciphertext": _encrypt(credential, "connection:google:" + user_id),
        "credential_key_version": _active_key_version(),
        "access_token_expires_at": new_expiry.isoformat(), "token_updated_at": datetime.now(timezone.utc).isoformat(),
        "status": "connected", "last_error_code": None, "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    await repository(request).insert("moreai_connection_audit", {
        "connection_id": connection["id"], "user_id": user_id, "provider": "google",
        "event_type": "refreshed", "scopes": connection.get("scopes") or [],
        "detail": {"credential_key_version": 1},
    })
    return credential["access_token"]


@router.get("/{connection_id}/gmail/messages")
async def list_gmail_messages(
    connection_id: UUID, request: Request, query: str = Query(default="newer_than:30d", max_length=500),
    limit: int = Query(default=20, ge=1, le=50), user: dict[str, Any] = Depends(customer_principal),
):
    connection = await _owned_google_connection(request, user["id"], connection_id)
    if GOOGLE_SCOPE_MAP["gmail.read"] not in (connection.get("scopes") or []):
        raise HTTPException(403, "gmail_read_permission_not_granted")
    token = await _google_access_token(request, connection)
    response = await request.app.state.http.get("https://gmail.googleapis.com/gmail/v1/users/me/messages",
        params={"q": query, "maxResults": limit}, headers={"Authorization": "Bearer " + token}, timeout=20.0, follow_redirects=False)
    if response.status_code != 200:
        raise HTTPException(502, "gmail_messages_fetch_failed")
    rows = response.json().get("messages") or []
    messages = []
    for item in rows[:limit]:
        detail = await request.app.state.http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/" + str(item["id"]),
            params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
            headers={"Authorization": "Bearer " + token}, timeout=15.0, follow_redirects=False,
        )
        if detail.status_code != 200:
            continue
        payload = detail.json()
        headers = {str(header.get("name","")).lower(): header.get("value") for header in payload.get("payload", {}).get("headers", [])}
        messages.append({"id": payload.get("id"), "thread_id": payload.get("threadId"), "snippet": payload.get("snippet"),
            "subject": headers.get("subject"), "from": headers.get("from"), "date": headers.get("date"), "unread": "UNREAD" in payload.get("labelIds", [])})
    return {"items": messages, "count": len(messages)}


@router.get("/{connection_id}/calendar/events")
async def list_calendar_events(
    connection_id: UUID, request: Request, time_min: datetime = Query(...), time_max: datetime = Query(...),
    limit: int = Query(default=50, ge=1, le=100), user: dict[str, Any] = Depends(customer_principal),
):
    if time_max <= time_min or (time_max - time_min).days > 90:
        raise HTTPException(422, "calendar_range_invalid")
    connection = await _owned_google_connection(request, user["id"], connection_id)
    if GOOGLE_SCOPE_MAP["calendar.read"] not in (connection.get("scopes") or []) and GOOGLE_SCOPE_MAP["calendar.write"] not in (connection.get("scopes") or []):
        raise HTTPException(403, "calendar_read_permission_not_granted")
    token = await _google_access_token(request, connection)
    response = await request.app.state.http.get("https://www.googleapis.com/calendar/v3/calendars/primary/events",
        params={"timeMin": time_min.isoformat(), "timeMax": time_max.isoformat(), "maxResults": limit, "singleEvents": "true", "orderBy": "startTime"},
        headers={"Authorization": "Bearer " + token}, timeout=20.0, follow_redirects=False)
    if response.status_code != 200:
        raise HTTPException(502, "calendar_events_fetch_failed")
    items = []
    for event in response.json().get("items", [])[:limit]:
        items.append({"id": event.get("id"), "summary": event.get("summary"), "status": event.get("status"),
            "start": event.get("start"), "end": event.get("end"), "html_link": event.get("htmlLink")})
    return {"items": items, "count": len(items)}


@router.delete("/{connection_id}")
async def disconnect_google(connection_id: UUID, request: Request, user: dict[str, Any] = Depends(customer_principal)):
    connection = await _owned_google_connection(request, user["id"], connection_id)
    credential = _decrypt(connection["credential_ciphertext"], "connection:google:" + str(user["id"]))
    token = credential.get("refresh_token") or credential.get("access_token")
    if isinstance(token, str) and token:
        await request.app.state.http.post(GOOGLE_REVOKE_URL, data={"token": token}, timeout=15.0, follow_redirects=False)
    return await repository(request).rpc("moreai_disconnect_connection", {
        "p_connection_id": str(connection_id), "p_user_id": str(user["id"]),
    })


@router.post("/{connection_id}/gmail/send")
async def send_gmail_message(
    connection_id: UUID, body: GmailSendRequest, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(customer_principal),
):
    if body.confirmed is not True:
        raise HTTPException(409, "explicit_confirmation_required")
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "idempotency_key_required")
    if any(not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address) for address in body.to):
        raise HTTPException(422, "recipient_email_invalid")
    connection = await _owned_google_connection(request, user["id"], connection_id)
    if GOOGLE_SCOPE_MAP["gmail.send"] not in (connection.get("scopes") or []):
        raise HTTPException(403, "gmail_send_permission_not_granted")
    message = EmailMessage()
    message["To"] = ", ".join(body.to)
    message["Subject"] = body.subject
    message.set_content(body.body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
    payload_hash = hashlib.sha256(json.dumps({"to":body.to,"subject":body.subject,"body":body.body},sort_keys=True).encode()).hexdigest()
    token = await _google_access_token(request, connection)
    repo = repository(request)
    claim = await repo.rpc("moreai_begin_connection_action", {
        "p_user_id": str(user["id"]), "p_connection_id": str(connection_id),
        "p_action_type": "gmail.send", "p_idempotency_key": idempotency_key,
        "p_payload_sha256": payload_hash,
    })
    if not isinstance(claim, dict):
        raise HTTPException(409, "gmail_action_claim_failed")
    if claim.get("replay"):
        if claim.get("status") == "completed":
            return {"status": "completed", "replayed": True, "message_id": claim.get("provider_resource_id")}
        raise HTTPException(409, "gmail_action_already_started_or_outcome_unknown")
    try:
        response = await request.app.state.http.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization":"Bearer "+token}, json={"raw":raw}, timeout=30.0, follow_redirects=False,
        )
        if response.status_code not in {200, 202}:
            await repo.rpc("moreai_finish_connection_action", {
                "p_action_id": claim["action_id"], "p_user_id": str(user["id"]),
                "p_status": "unknown" if response.status_code >= 500 else "failed",
                "p_provider_resource_id": "", "p_result_metadata": {"http_status": response.status_code},
            })
            raise HTTPException(502, "gmail_send_provider_rejected")
        result = response.json()
        receipt = await repo.rpc("moreai_finish_connection_action", {
            "p_action_id": claim["action_id"], "p_user_id": str(user["id"]),
            "p_status": "completed", "p_provider_resource_id": str(result.get("id") or ""),
            "p_result_metadata": {"thread_id": result.get("threadId")},
        })
        return {"status":"completed","replayed":False,"receipt":receipt}
    except HTTPException:
        raise
    except Exception as exc:
        await repo.rpc("moreai_finish_connection_action", {
            "p_action_id": claim["action_id"], "p_user_id": str(user["id"]),
            "p_status": "unknown", "p_provider_resource_id": "",
            "p_result_metadata": {"outcome":"provider_response_unavailable"},
        })
        raise HTTPException(502, "gmail_send_outcome_unknown_do_not_retry") from exc


@router.post("/{connection_id}/calendar/events")
async def create_calendar_event(
    connection_id: UUID, body: CalendarCreateRequest, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(customer_principal),
):
    if body.confirmed is not True:
        raise HTTPException(409, "explicit_confirmation_required")
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "idempotency_key_required")
    if body.start.tzinfo is None or body.end.tzinfo is None or body.end <= body.start:
        raise HTTPException(422, "calendar_event_time_invalid")
    if body.end - body.start > timedelta(days=7):
        raise HTTPException(422, "calendar_event_duration_exceeded")
    connection = await _owned_google_connection(request, user["id"], connection_id)
    if GOOGLE_SCOPE_MAP["calendar.write"] not in (connection.get("scopes") or []):
        raise HTTPException(403, "calendar_write_permission_not_granted")
    event_payload = {
        "summary": body.summary, "description": body.description,
        "start": {"dateTime": body.start.isoformat(), "timeZone": body.timezone},
        "end": {"dateTime": body.end.isoformat(), "timeZone": body.timezone},
    }
    payload_hash = hashlib.sha256(json.dumps(event_payload,sort_keys=True).encode()).hexdigest()
    token = await _google_access_token(request, connection)
    repo = repository(request)
    claim = await repo.rpc("moreai_begin_connection_action", {
        "p_user_id": str(user["id"]), "p_connection_id": str(connection_id),
        "p_action_type": "calendar.create", "p_idempotency_key": idempotency_key,
        "p_payload_sha256": payload_hash,
    })
    if not isinstance(claim, dict):
        raise HTTPException(409, "calendar_action_claim_failed")
    if claim.get("replay"):
        if claim.get("status") == "completed":
            return {"status":"completed","replayed":True,"event_id":claim.get("provider_resource_id")}
        raise HTTPException(409, "calendar_action_already_started_or_outcome_unknown")
    try:
        response = await request.app.state.http.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization":"Bearer "+token}, json=event_payload, timeout=30.0, follow_redirects=False,
        )
        if response.status_code not in {200, 201}:
            await repo.rpc("moreai_finish_connection_action", {
                "p_action_id": claim["action_id"], "p_user_id": str(user["id"]),
                "p_status": "unknown" if response.status_code >= 500 else "failed",
                "p_provider_resource_id": "", "p_result_metadata": {"http_status": response.status_code},
            })
            raise HTTPException(502, "calendar_event_provider_rejected")
        result = response.json()
        receipt = await repo.rpc("moreai_finish_connection_action", {
            "p_action_id": claim["action_id"], "p_user_id": str(user["id"]),
            "p_status": "completed", "p_provider_resource_id": str(result.get("id") or ""),
            "p_result_metadata": {"html_link": result.get("htmlLink")},
        })
        return {"status":"completed","replayed":False,"receipt":receipt}
    except HTTPException:
        raise
    except Exception as exc:
        await repo.rpc("moreai_finish_connection_action", {
            "p_action_id": claim["action_id"], "p_user_id": str(user["id"]),
            "p_status": "unknown", "p_provider_resource_id": "",
            "p_result_metadata": {"outcome":"provider_response_unavailable"},
        })
        raise HTTPException(502, "calendar_event_outcome_unknown_do_not_retry") from exc


class InternalGoogleReadRequest(BaseModel):
    user_id: UUID
    run_id: UUID
    query: str = Field(default="newer_than:30d", max_length=500)
    limit: int = Field(default=20, ge=1, le=30)
    time_min: datetime | None = None
    time_max: datetime | None = None


def _require_worker_internal(request: Request) -> None:
    expected = os.getenv("MOREAI_WORKER_INTERNAL_TOKEN", "")
    supplied = request.headers.get("X-MoreAI-Worker-Token", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        raise HTTPException(401, "worker_internal_authentication_failed")


async def _internal_google_connection(request: Request, user_id: str, run_id: str, scope: str) -> dict[str, Any]:
    _require_worker_internal(request)
    repo = repository(request)
    runs = await repo.select("agent_runs", {
        "id": f"eq.{run_id}", "user_id": f"eq.{user_id}",
        "status": "eq.running", "select": "id", "limit": "1",
    })
    if not runs:
        raise HTTPException(403, "worker_run_owner_or_status_mismatch")
    rows = await repo.select("moreai_connections", {
        "user_id": f"eq.{user_id}", "provider": "eq.google", "status": "eq.connected",
        "select": "id,user_id,scopes,credential_ciphertext,credential_key_version,access_token_expires_at",
        "order": "updated_at.desc", "limit": "20",
    })
    connection = next((row for row in rows if scope in (row.get("scopes") or [])), None)
    if not connection:
        raise HTTPException(403, "google_connection_scope_not_available")
    return connection


@router.post("/internal/google/gmail/search")
async def internal_gmail_search(body: InternalGoogleReadRequest, request: Request):
    connection = await _internal_google_connection(request, str(body.user_id), str(body.run_id), GOOGLE_SCOPE_MAP["gmail.read"])
    token = await _google_access_token(request, connection)
    response = await request.app.state.http.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        params={"q": body.query, "maxResults": body.limit},
        headers={"Authorization": "Bearer " + token}, timeout=20.0, follow_redirects=False,
    )
    if response.status_code != 200:
        raise HTTPException(502, "gmail_search_failed")
    items = []
    for row in response.json().get("messages", [])[:body.limit]:
        detail = await request.app.state.http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/" + str(row["id"]),
            params={"format":"metadata","metadataHeaders":["Subject","From","Date"]},
            headers={"Authorization":"Bearer "+token}, timeout=15.0, follow_redirects=False,
        )
        if detail.status_code != 200:
            continue
        data = detail.json()
        headers = {str(x.get("name","")).lower():x.get("value") for x in data.get("payload",{}).get("headers",[])}
        items.append({"id":data.get("id"),"thread_id":data.get("threadId"),"subject":headers.get("subject"),
            "from":headers.get("from"),"date":headers.get("date"),"snippet":data.get("snippet")})
    return {"items":items,"count":len(items),"source":"google_gmail"}


@router.post("/internal/google/calendar/list")
async def internal_calendar_list(body: InternalGoogleReadRequest, request: Request):
    if body.time_min is None or body.time_max is None or body.time_max <= body.time_min or (body.time_max-body.time_min).days > 90:
        raise HTTPException(422, "calendar_range_invalid")
    connection = await _internal_google_connection(request, str(body.user_id), str(body.run_id), GOOGLE_SCOPE_MAP["calendar.read"])
    token = await _google_access_token(request, connection)
    response = await request.app.state.http.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        params={"timeMin":body.time_min.isoformat(),"timeMax":body.time_max.isoformat(),
            "maxResults":body.limit,"singleEvents":"true","orderBy":"startTime"},
        headers={"Authorization":"Bearer "+token}, timeout=20.0, follow_redirects=False,
    )
    if response.status_code != 200:
        raise HTTPException(502, "calendar_list_failed")
    items = [{"id":event.get("id"),"summary":event.get("summary"),"start":event.get("start"),"end":event.get("end")}
        for event in response.json().get("items",[])[:body.limit]]
    return {"items":items,"count":len(items),"source":"google_calendar"}


class InternalGoogleWriteRequest(BaseModel):
    user_id: UUID
    run_id: UUID
    to: list[str] = Field(default_factory=list, max_length=5)
    subject: str = Field(default="", max_length=240)
    body: str = Field(default="", max_length=20000)
    summary: str = Field(default="", max_length=240)
    description: str = Field(default="", max_length=4000)
    start: str | None = None
    end: str | None = None
    timezone: str = Field(default="Asia/Jakarta", max_length=64)


async def _finish_internal_action(repo: Any, action_id: str, user_id: str, status: str, resource_id: str, metadata: dict[str, Any]) -> Any:
    return await repo.rpc("moreai_finish_connection_action", {
        "p_action_id": action_id, "p_user_id": user_id, "p_status": status,
        "p_provider_resource_id": resource_id, "p_result_metadata": metadata,
    })


@router.post("/internal/google/gmail/send")
async def internal_gmail_send(
    body: InternalGoogleWriteRequest, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "idempotency_key_required")
    if not body.to or any(not re.fullmatch(r"[^\\s@]+@[^\\s@]+\\.[^\\s@]+", address) for address in body.to):
        raise HTTPException(422, "recipient_email_invalid")
    if not body.subject.strip() or not body.body.strip():
        raise HTTPException(422, "gmail_message_content_required")
    connection = await _internal_google_connection(request, str(body.user_id), str(body.run_id), GOOGLE_SCOPE_MAP["gmail.send"])
    message = EmailMessage()
    message["To"] = ", ".join(body.to)
    message["Subject"] = body.subject
    message.set_content(body.body)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip("=")
    payload_hash = hashlib.sha256(json.dumps({"to":body.to,"subject":body.subject,"body":body.body},sort_keys=True).encode()).hexdigest()
    token = await _google_access_token(request, connection)
    repo = repository(request)
    claim = await repo.rpc("moreai_begin_connection_action", {
        "p_user_id": str(body.user_id), "p_connection_id": str(connection["id"]),
        "p_action_type": "gmail.send", "p_idempotency_key": idempotency_key,
        "p_payload_sha256": payload_hash,
    })
    if not isinstance(claim, dict):
        raise HTTPException(409, "gmail_action_claim_failed")
    if claim.get("replay"):
        if claim.get("status") == "completed":
            return {"status":"completed","replayed":True,"message_id":claim.get("provider_resource_id")}
        raise HTTPException(409, "gmail_action_already_started_or_outcome_unknown")
    try:
        response = await request.app.state.http.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization":"Bearer "+token}, json={"raw":raw}, timeout=30.0, follow_redirects=False,
        )
        if response.status_code != 200:
            await _finish_internal_action(repo, claim["action_id"], str(body.user_id),
                "unknown" if response.status_code >= 500 else "failed", "", {"http_status":response.status_code})
            raise HTTPException(502, "gmail_send_provider_rejected")
        result = response.json()
        receipt = await _finish_internal_action(repo, claim["action_id"], str(body.user_id),
            "completed", str(result.get("id") or ""), {"thread_id":result.get("threadId"),"source":"openmanus"})
        return {"status":"completed","replayed":False,"receipt":receipt}
    except HTTPException:
        raise
    except Exception as exc:
        await _finish_internal_action(repo, claim["action_id"], str(body.user_id),
            "unknown", "", {"outcome":"provider_response_unavailable","source":"openmanus"})
        raise HTTPException(502, "gmail_send_outcome_unknown_do_not_retry") from exc


@router.post("/internal/google/calendar/create")
async def internal_calendar_create(
    body: InternalGoogleWriteRequest, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "idempotency_key_required")
    if not body.summary.strip() or not body.start or not body.end:
        raise HTTPException(422, "calendar_event_fields_required")
    try:
        start = datetime.fromisoformat(body.start.replace("Z","+00:00"))
        end = datetime.fromisoformat(body.end.replace("Z","+00:00"))
    except ValueError as exc:
        raise HTTPException(422, "calendar_event_datetime_invalid") from exc
    if start.tzinfo is None or end.tzinfo is None or end <= start or end-start > timedelta(days=7):
        raise HTTPException(422, "calendar_event_time_invalid")
    connection = await _internal_google_connection(request, str(body.user_id), str(body.run_id), GOOGLE_SCOPE_MAP["calendar.write"])
    event_payload = {"summary":body.summary,"description":body.description,
        "start":{"dateTime":start.isoformat(),"timeZone":body.timezone},
        "end":{"dateTime":end.isoformat(),"timeZone":body.timezone}}
    payload_hash = hashlib.sha256(json.dumps(event_payload,sort_keys=True).encode()).hexdigest()
    token = await _google_access_token(request, connection)
    repo = repository(request)
    claim = await repo.rpc("moreai_begin_connection_action", {
        "p_user_id":str(body.user_id),"p_connection_id":str(connection["id"]),
        "p_action_type":"calendar.create","p_idempotency_key":idempotency_key,
        "p_payload_sha256":payload_hash,
    })
    if not isinstance(claim,dict):
        raise HTTPException(409,"calendar_action_claim_failed")
    if claim.get("replay"):
        if claim.get("status")=="completed":
            return {"status":"completed","replayed":True,"event_id":claim.get("provider_resource_id")}
        raise HTTPException(409,"calendar_action_already_started_or_outcome_unknown")
    try:
        response = await request.app.state.http.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            headers={"Authorization":"Bearer "+token},json=event_payload,timeout=30.0,follow_redirects=False,
        )
        if response.status_code not in {200,201}:
            await _finish_internal_action(repo,claim["action_id"],str(body.user_id),
                "unknown" if response.status_code>=500 else "failed","",{"http_status":response.status_code})
            raise HTTPException(502,"calendar_event_provider_rejected")
        result=response.json()
        receipt=await _finish_internal_action(repo,claim["action_id"],str(body.user_id),
            "completed",str(result.get("id") or ""),{"html_link":result.get("htmlLink"),"source":"openmanus"})
        return {"status":"completed","replayed":False,"receipt":receipt}
    except HTTPException:
        raise
    except Exception as exc:
        await _finish_internal_action(repo,claim["action_id"],str(body.user_id),
            "unknown","",{"outcome":"provider_response_unavailable","source":"openmanus"})
        raise HTTPException(502,"calendar_event_outcome_unknown_do_not_retry") from exc
