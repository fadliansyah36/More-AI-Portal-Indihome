from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

from app.authorization import customer_principal, require_customer_context
from app.dependencies import current_user
from app.routers.conversations import ConversationCreate, MessageCreate, repository
from app.pagination import decode_created_at_id_cursor, encode_created_at_id_cursor, created_at_id_filter


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
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,title,status,created_at,updated_at",
        "order": "updated_at.desc", "limit": str(limit),
    }
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["updated_at"] = f"lt.{before.isoformat()}"
    return await repository(request).select("conversations", filters)


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
    attachment_links = await repo.select("conversation_message_attachments", {
        "conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{principal['id']}",
        "select": "message_id,artifact_id", "order": "created_at.asc", "limit": "1000",
    })
    artifact_ids = sorted({str(row["artifact_id"]) for row in attachment_links if row.get("artifact_id")})
    artifact_by_id: dict[str, dict[str, Any]] = {}
    if artifact_ids:
        artifacts = await repo.select("artifacts", {
            "id": f"in.({','.join(artifact_ids)})", "user_id": f"eq.{principal['id']}",
            "select": "id,mime_type,size_bytes,metadata,created_at", "limit": "100",
        })
        artifact_by_id = {str(row["id"]): row for row in artifacts if row.get("id")}
    attachments_by_message: dict[str, list[dict[str, Any]]] = {}
    for link in attachment_links:
        artifact = artifact_by_id.get(str(link.get("artifact_id")))
        if not artifact:
            continue
        metadata = artifact.get("metadata") if isinstance(artifact.get("metadata"), dict) else {}
        attachments_by_message.setdefault(str(link["message_id"]), []).append({
            "id": str(artifact["id"]),
            "filename": str(metadata.get("filename") or "attachment"),
            "mime_type": artifact.get("mime_type"),
            "size_bytes": artifact.get("size_bytes"),
        })
    messages = [{**message, "attachments": attachments_by_message.get(str(message["id"]), [])} for message in messages]
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
    return await repository(request).rpc("moreai_enqueue_chat_run_with_attachments", {
        "p_user_id": principal["id"], "p_conversation_id": str(conversation_id),
        "p_content": body.content, "p_agent_key": body.agent_key,
        "p_idempotency_key": idempotency_key,
        "p_attachment_ids": [str(item) for item in body.attachment_ids],
    })


@router.get("/agent-runs")
async def customer_agent_runs(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    """List customer runs with stable keyset pagination and a legacy timestamp cursor."""
    if cursor and before:
        raise HTTPException(422, "Use either cursor or before, not both")
    decoded = decode_created_at_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,conversation_id,status,input,output,error,attempt,max_attempts,created_at,started_at,finished_at",
        "order": "created_at.desc,id.desc", "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        filters["or"] = cursor_filter
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["created_at"] = f"lt.{before.isoformat()}"
    rows = await repository(request).select("agent_runs", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.get("/agent-runs/{run_id}")
async def customer_agent_run(
    run_id: UUID, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).owned_record("agent_runs", run_id, principal["id"])



@router.post("/agent-runs/{run_id}/cancel")
async def customer_cancel_agent_run(
    run_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, principal["id"])
    return await repo.rpc("moreai_worker_request_cancel", {
        "p_run_id": str(run_id),
        "p_user_id": principal["id"],
    })


@router.get("/agent-runs/{run_id}/steps")
async def customer_agent_run_steps(
    run_id: UUID, request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    user: dict[str, Any] = Depends(current_user),
):
    """Return safe workflow lifecycle metadata after verifying run ownership.

    Step input/output/error payloads can contain prompts, private tool arguments,
    provider observations and sensitive artifact references. They are intentionally
    excluded from the customer-facing transport contract.
    """
    principal = await require_customer_context(request, user)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, principal["id"])
    return await repo.select("agent_run_steps", {
        "run_id": f"eq.{run_id}",
        "select": "id,sequence,step_key,status,started_at,finished_at,created_at",
        "order": "sequence.asc",
        "limit": str(limit),
    })


@router.get("/agent-runs/{run_id}/stream")
async def customer_agent_run_stream(
    run_id: UUID, request: Request,
    after: int = Query(default=0, ge=0), wait_seconds: int = Query(default=60, ge=1, le=120),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, principal["id"])

    async def events():
        from app.routers.agent_runs import _event_with_checkpoint_state

        cursor = max(after, 0)
        idle_rounds = 0
        while idle_rounds < max(1, min(wait_seconds, 120)):
            if await request.is_disconnected():
                break
            rows = await repo.select("agent_run_events", {
                "run_id": f"eq.{run_id}", "sequence": f"gt.{cursor}",
                "select": "id,event_type,sequence,payload,created_at",
                "order": "sequence.asc", "limit": "100",
            })
            if rows:
                idle_rounds = 0
                for raw in rows:
                    row = await _event_with_checkpoint_state(repo, run_id, raw)
                    cursor = max(cursor, int(row["sequence"]))
                    payload = json.dumps(row, separators=(",", ":"))
                    yield f"id: {cursor}\nevent: {row['event_type']}\ndata: {payload}\n\n"
                    if row["event_type"] in {"run.completed", "run.failed", "run.cancelled", "run.timed_out"}:
                        return
            else:
                idle_rounds += 1
                run = await repo.owned_record("agent_runs", run_id, principal["id"])
                status = run.get("status")
                if status in {"succeeded", "failed", "cancelled", "expired", "timed_out"}:
                    terminal_event = (
                        "run.completed" if status == "succeeded"
                        else "run.cancelled" if status == "cancelled"
                        else "run.timed_out" if status == "timed_out"
                        else "run.failed"
                    )
                    payload = json.dumps({
                        "run_id": str(run_id), "status": status,
                        "output": run.get("output"), "error": run.get("error"),
                    }, separators=(",", ":"))
                    yield f"id: {cursor}\nevent: {terminal_event}\ndata: {payload}\n\n"
                    return
                yield ": keep-alive\n\n"
            await asyncio.sleep(1)
        yield "event: stream.timeout\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no",
    })


@router.get("/network/speedtest/ping")
async def customer_network_speedtest_ping(
    user: dict[str, Any] = Depends(customer_principal),
):
    """Measure authenticated device-to-MoreAI-API round-trip latency."""
    return {"status": "ok", "service": "moreai-api", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/network/speedtest/download")
async def customer_network_speedtest_download(
    size_bytes: int = Query(default=4 * 1024 * 1024, ge=65536, le=8 * 1024 * 1024),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Return bounded uncompressible bytes to measure the real client-to-API path."""
    import secrets
    payload = secrets.token_bytes(size_bytes)
    return Response(
        content=payload,
        media_type="application/octet-stream",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Content-Length": str(size_bytes),
            "X-MoreAI-Speedtest-Bytes": str(size_bytes),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/network/speedtest/upload")
async def customer_network_speedtest_upload(
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Consume a bounded upload stream and report bytes accepted by this API."""
    import time
    max_bytes = 4 * 1024 * 1024
    declared = request.headers.get("content-length")
    if declared:
        try:
            if int(declared) > max_bytes:
                raise HTTPException(413, "Speed test upload is limited to 4 MiB")
        except ValueError as exc:
            raise HTTPException(400, "Invalid Content-Length") from exc
    started = time.monotonic()
    received = 0
    async for chunk in request.stream():
        received += len(chunk)
        if received > max_bytes:
            raise HTTPException(413, "Speed test upload is limited to 4 MiB")
    if received == 0:
        raise HTTPException(422, "Speed test upload body is empty")
    return {
        "status": "ok",
        "received_bytes": received,
        "server_receive_ms": round((time.monotonic() - started) * 1000, 2),
    }


@router.get("/network-sessions")
async def customer_network_sessions(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    user: dict[str, Any] = Depends(current_user),
):
    """Return the authenticated customer's own network session history.

    The response intentionally excludes gateway identifiers, IP addresses,
    device fingerprints and private verification evidence.
    """
    principal = await require_customer_context(request, user)
    return await repository(request).select("network_sessions", {
        "user_id": f"eq.{principal['id']}",
        "select": (
            "id,network_id,status,started_at,last_heartbeat_at,expires_at,ended_at,end_reason,"
            "network:partner_networks(id,name,ssid_label,gateway_type,status,"
            "location:partner_locations(id,name,address))"
        ),
        "order": "started_at.desc",
        "limit": str(limit),
    })


@router.get("/wallet")
async def customer_wallet(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    rows = await repository(request).select("wallet_accounts", {
        "owner_type": "eq.user", "owner_id": f"eq.{principal['id']}",
        "select": "id,currency,balance,status,created_at,updated_at",
        "order": "created_at.asc", "limit": "20",
    })
    return {"wallets": rows}


@router.get("/wallet/ledger")
async def customer_wallet_ledger(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    wallets = await repo.select("wallet_accounts", {
        "owner_type": "eq.user", "owner_id": f"eq.{principal['id']}",
        "select": "id", "limit": "20",
    })
    ids = [str(row["id"]) for row in wallets if row.get("id")]
    if not ids:
        return []
    filters = {
        "wallet_id": f"in.({','.join(ids)})",
        "select": "id,wallet_id,entry_type,amount,balance_after,reference_type,reference_id,description,created_at",
        "order": "created_at.desc", "limit": str(limit),
    }
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["created_at"] = f"lt.{before.isoformat()}"
    return await repo.select("credit_ledger", filters)


@router.get("/usage")
async def customer_usage(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,run_id,provider_key,model_key,input_tokens,output_tokens,estimated_cost,actual_cost,status,latency_ms,created_at",
        "order": "created_at.desc", "limit": str(limit),
    }
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["created_at"] = f"lt.{before.isoformat()}"
    return await repository(request).select("llm_usage", filters)


@router.get("/usage/analytics")
async def customer_usage_analytics(
    request: Request,
    days: int = Query(default=30, ge=1, le=365),
    user: dict[str, Any] = Depends(current_user),
):
    """Return server-aggregated historical usage for the authenticated Customer only."""
    principal = await require_customer_context(request, user)
    until = datetime.now(timezone.utc)
    since = until - timedelta(days=days)
    result = await repository(request).rpc("moreai_customer_usage_analytics", {
        "p_user_id": principal["id"],
        "p_since": since.isoformat(),
        "p_until": until.isoformat(),
    })
    if not isinstance(result, dict) or not isinstance(result.get("summary"), dict):
        raise HTTPException(502, "Customer usage analytics returned an invalid response")
    return result


@router.get("/entitlements")
async def customer_entitlements(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("user_entitlements", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,entitlement_key,source_type,status,starts_at,expires_at,metadata",
        "order": "created_at.desc", "limit": "200",
    })


@router.get("/quotas")
async def customer_quotas(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    policies = await repo.select("quota_policies", {
        "enabled": "eq.true",
        "or": f"(and(scope_type.in.(platform,global),scope_id.is.null),and(scope_type.eq.user,scope_id.eq.{principal['id']}))",
        "select": "id,scope_type,scope_id,metric_key,limit_value,window_seconds",
        "order": "metric_key.asc", "limit": "200",
    })
    if not policies:
        return []
    policy_ids = [str(row["id"]) for row in policies]
    # Usage rows inherit the policy scope. Global/platform policy usage therefore
    # has a NULL scope_id and must not be filtered to the caller's user scope.
    usage_rows = await repo.select("quota_usage", {
        "policy_id": f"in.({','.join(policy_ids)})",
        "select": "policy_id,used_value,window_start,updated_at",
        "order": "window_start.desc",
        "limit": "1000",
    })
    now = datetime.now(timezone.utc)
    policy_by_id = {str(policy["id"]): policy for policy in policies}
    usage_by_policy = {}
    for row in usage_rows:
        policy_id = str(row.get("policy_id"))
        policy = policy_by_id.get(policy_id)
        if policy is None or policy_id in usage_by_policy:
            continue
        try:
            window_start = datetime.fromisoformat(str(row["window_start"]).replace("Z", "+00:00"))
            if window_start.tzinfo is None:
                continue
            window_seconds = int(policy.get("window_seconds") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        if window_seconds > 0 and window_start <= now < window_start + timedelta(seconds=window_seconds):
            usage_by_policy[policy_id] = row
    return [{**policy, "usage": usage_by_policy.get(str(policy["id"]))} for policy in policies]


class AccessCodeRedeem(BaseModel):
    code: str = Field(min_length=8, max_length=128)
    network_id: UUID
    verification_session_id: UUID


@router.post("/access-codes/redeem")
async def redeem_partner_access_code(
    body: AccessCodeRedeem,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(current_user),
):
    import hashlib
    principal = await require_customer_context(request, user)
    if not idempotency_key or not 8 <= len(idempotency_key) <= 160:
        raise HTTPException(400, "An 8–160 character Idempotency-Key header is required")
    raw_code = body.code.strip()
    if not raw_code or len(raw_code) < 8:
        raise HTTPException(422, "Access code is invalid")
    digest = hashlib.sha256(raw_code.encode("utf-8")).hexdigest()
    try:
        return await repository(request).rpc("moreai_redeem_partner_access_code", {
            "p_code_hash": digest,
            "p_user_id": principal["id"],
            "p_network_id": str(body.network_id),
            "p_verification_session_id": str(body.verification_session_id),
            "p_idempotency_key": idempotency_key,
        })
    except Exception as exc:
        message = str(exc)
        if "NETWORK_VERIFICATION_REQUIRED" in message:
            raise HTTPException(403, "Network verification is required before redeeming this code")
        if "IDEMPOTENCY_KEY_CONFLICT" in message:
            raise HTTPException(409, "Idempotency key was already used for another access code")
        if "ACCESS_CODE_EXPIRED" in message:
            raise HTTPException(410, "Access code has expired")
        if "ACCESS_CODE_EXHAUSTED" in message:
            raise HTTPException(409, "Access code redemption limit has been reached")
        if "ACCESS_CODE_NOT_AVAILABLE" in message:
            raise HTTPException(404, "Access code is not available")
        if "ACCESS_CODE_NETWORK_MISMATCH" in message or "ACCESS_CODE_SCOPE_MISMATCH" in message:
            raise HTTPException(403, "Access code is not valid for this network")
        raise
