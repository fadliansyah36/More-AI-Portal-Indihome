from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import ConversationCreate, MessageCreate, repository
from app.pagination import decode_created_at_id_cursor, encode_created_at_id_cursor, created_at_id_filter, decode_updated_at_id_cursor, encode_updated_at_id_cursor, updated_at_id_filter, decode_timestamp_id_cursor, encode_timestamp_id_cursor, timestamp_id_filter


router = APIRouter(prefix="/api/v1/customer", tags=["customer"])


class CustomerContextResponse(BaseModel):
    principal: dict[str, str]
    tenant: None = None


class CustomerNetworkLocationResponse(BaseModel):
    id: UUID
    name: str
    address: dict[str, Any]


class CustomerNetworkDetailsResponse(BaseModel):
    id: UUID
    name: str
    ssid_label: str | None = None
    gateway_type: str
    status: str
    location: CustomerNetworkLocationResponse | None = None


class CustomerNetworkSessionResponse(BaseModel):
    id: UUID
    network_id: UUID
    status: str
    started_at: datetime
    last_heartbeat_at: datetime | None = None
    expires_at: datetime
    ended_at: datetime | None = None
    end_reason: str | None = None
    network: CustomerNetworkDetailsResponse | None = None


class CustomerSpeedtestPingResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["moreai-api"]
    timestamp: datetime


class CustomerSpeedtestUploadResponse(BaseModel):
    status: Literal["ok"]
    received_bytes: int
    server_receive_ms: Decimal


class CustomerConversationResponse(BaseModel):
    id: UUID
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerConversationMessageAttachmentResponse(BaseModel):
    id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int | None


class CustomerConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    model_key: str | None
    run_id: UUID | None
    created_at: datetime
    attachments: list[CustomerConversationMessageAttachmentResponse] = Field(default_factory=list)


class CustomerConversationMessagePageResponse(BaseModel):
    items: list[CustomerConversationMessageResponse]
    count: int


class CustomerConversationDetailResponse(BaseModel):
    conversation: CustomerConversationResponse
    messages: list[CustomerConversationMessageResponse]


class CustomerAgentRunStepResponse(BaseModel):
    id: UUID
    sequence: int
    step_key: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime


class CustomerAgentRunResponse(BaseModel):
    id: UUID
    conversation_id: UUID | None
    status: str
    input: dict[str, Any] | None = None
    output: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    attempt: int | None = None
    max_attempts: int | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CustomerAgentRunCancellationResponse(BaseModel):
    run_id: UUID
    status: Literal["cancel_requested", "cancelled", "succeeded", "failed", "timed_out", "expired"]


class CustomerMessageEnqueueResponse(BaseModel):
    run: CustomerAgentRunResponse
    message: CustomerConversationMessageResponse | None = None
    replayed: bool


class CustomerWalletResponse(BaseModel):
    id: UUID
    currency: str
    balance: Decimal
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerWalletListResponse(BaseModel):
    wallets: list[CustomerWalletResponse]


class CustomerLedgerEntryResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    entry_type: str
    amount: Decimal
    balance_after: Decimal
    reference_type: str | None
    reference_id: str | None
    description: str | None
    created_at: datetime


class CustomerUsageRecordResponse(BaseModel):
    id: UUID
    run_id: UUID | None
    provider_key: str
    model_key: str
    input_tokens: int
    output_tokens: int
    estimated_cost: Decimal
    actual_cost: Decimal | None
    status: str
    latency_ms: int | None
    created_at: datetime


class CustomerAccessCodeRedeemResponse(BaseModel):
    redemption_id: UUID
    replayed: bool
    redeemed_at: datetime
    reward_id: UUID | None = None
    partner_entitlement_activated: bool | None = None
    message: str | None = None


class CustomerUsageAnalyticsSummaryResponse(BaseModel):
    total_requests: int
    total_tokens: int
    successful_requests: int
    failed_requests: int
    total_cost: Decimal
    average_latency_ms: int


class CustomerUsageAnalyticsModelResponse(BaseModel):
    model_key: str
    provider_key: str
    requests: int
    tokens: int
    successful_requests: int
    cost: Decimal


class CustomerUsageAnalyticsDayResponse(BaseModel):
    day: date
    requests: int
    tokens: int
    cost: Decimal


class CustomerUsageAnalyticsPeriodResponse(BaseModel):
    since: datetime
    until: datetime


class CustomerUsageAnalyticsResponse(BaseModel):
    summary: CustomerUsageAnalyticsSummaryResponse
    by_model: list[CustomerUsageAnalyticsModelResponse]
    by_day: list[CustomerUsageAnalyticsDayResponse]
    period: CustomerUsageAnalyticsPeriodResponse


class CustomerEntitlementResponse(BaseModel):
    id: UUID
    entitlement_key: str
    source_type: str
    status: str
    starts_at: datetime
    expires_at: datetime | None
    metadata: dict[str, Any]


class CustomerQuotaUsageResponse(BaseModel):
    used_value: Decimal
    window_start: datetime
    updated_at: datetime


class CustomerQuotaResponse(BaseModel):
    id: UUID
    scope_type: Literal["platform", "global", "user"]
    scope_id: UUID | None
    metric_key: str
    limit_value: Decimal
    window_seconds: int
    usage: CustomerQuotaUsageResponse | None = None


@router.get("/context", response_model=CustomerContextResponse)
async def customer_context(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    return {
        "principal": {"user_id": principal["id"], "role": principal["principal_role"]},
        "tenant": None,
    }


@router.post("/conversations", status_code=201, response_model=CustomerConversationResponse)
async def create_customer_conversation(
    body: ConversationCreate, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).insert("conversations", {
        "user_id": principal["id"], "title": body.title,
        "status": "active", "metadata": {},
    })


@router.get("/conversations", response_model=list[CustomerConversationResponse])
async def customer_conversations(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    if cursor and before:
        raise HTTPException(422, "Use either cursor or before, not both")
    decoded = decode_updated_at_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,title,status,created_at,updated_at",
        "order": "updated_at.desc,id.desc", "limit": str(limit + 1),
    }
    cursor_filter = updated_at_id_filter(decoded)
    if cursor_filter:
        filters["or"] = cursor_filter
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["updated_at"] = f"lt.{before.astimezone(timezone.utc).isoformat()}"
    rows = await repository(request).select("conversations", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_updated_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


async def _customer_conversation_message_attachments(
    repo: Any, user_id: str, conversation_id: UUID, messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    message_ids = [str(row["id"]) for row in messages if row.get("id")]
    if not message_ids:
        return [{**message, "attachments": []} for message in messages]
    links = await repo.select("conversation_message_attachments", {
        "conversation_id": f"eq.{conversation_id}",
        "user_id": f"eq.{user_id}",
        "message_id": f"in.({','.join(message_ids)})",
        "select": "message_id,artifact_id",
        "order": "created_at.asc",
        "limit": str(max(1, len(message_ids) * 10)),
    })
    artifact_ids = sorted({str(row["artifact_id"]) for row in links if row.get("artifact_id")})
    artifact_by_id: dict[str, dict[str, Any]] = {}
    if artifact_ids:
        artifacts = await repo.select("artifacts", {
            "id": f"in.({','.join(artifact_ids)})",
            "user_id": f"eq.{user_id}",
            "select": "id,mime_type,size_bytes,metadata,created_at",
            "limit": str(len(artifact_ids)),
        })
        artifact_by_id = {str(row["id"]): row for row in artifacts if row.get("id")}
    attachments_by_message: dict[str, list[dict[str, Any]]] = {}
    for link in links:
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
    return [
        {**message, "attachments": attachments_by_message.get(str(message["id"]), [])}
        for message in messages
    ]


@router.get("/conversations/{conversation_id}", response_model=CustomerConversationDetailResponse)
async def customer_conversation(
    conversation_id: UUID, request: Request, response: Response,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    conversation = await repo.owned_record("conversations", conversation_id, principal["id"])
    messages = await repo.select("conversation_messages", {
        "conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{principal['id']}",
        "select": "id,role,content,model_key,run_id,created_at",
        "order": "created_at.desc,id.desc", "limit": "51",
    })
    has_more = len(messages) > 50
    messages = messages[:50]
    if has_more and messages:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(messages[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    messages.reverse()
    messages = await _customer_conversation_message_attachments(repo, principal["id"], conversation_id, messages)
    return {"conversation": conversation, "messages": messages}


@router.get("/conversations/{conversation_id}/messages", response_model=CustomerConversationMessagePageResponse)
async def customer_conversation_messages(
    conversation_id: UUID,
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(current_user),
):
    """Return a chronological page of owner-scoped messages, with cursor moving toward older history."""
    decoded = decode_created_at_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    repo = repository(request)
    await repo.owned_record("conversations", conversation_id, principal["id"])
    filters = {
        "conversation_id": f"eq.{conversation_id}",
        "user_id": f"eq.{principal['id']}",
        "select": "id,role,content,model_key,run_id,created_at",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        filters["or"] = cursor_filter
    rows = await repo.select("conversation_messages", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    rows.reverse()
    items = await _customer_conversation_message_attachments(repo, principal["id"], conversation_id, rows)
    return {"items": items, "count": len(items)}


@router.post("/conversations/{conversation_id}/messages", status_code=202, response_model=CustomerMessageEnqueueResponse)
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


@router.get("/agent-runs", response_model=list[CustomerAgentRunResponse])
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


@router.get("/agent-runs/{run_id}", response_model=CustomerAgentRunResponse)
async def customer_agent_run(
    run_id: UUID, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).owned_record("agent_runs", run_id, principal["id"])



@router.post("/agent-runs/{run_id}/cancel", response_model=CustomerAgentRunCancellationResponse)
async def customer_cancel_agent_run(
    run_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    run = await repo.owned_record("agent_runs", run_id, principal["id"])
    if str(run.get("status") or "") in {"succeeded", "failed", "cancelled", "timed_out", "expired"}:
        return {"run_id": str(run_id), "status": str(run["status"])}
    return await repo.rpc("moreai_worker_request_cancel", {
        "p_run_id": str(run_id),
        "p_user_id": principal["id"],
    })


@router.get("/agent-runs/{run_id}/steps", response_model=list[CustomerAgentRunStepResponse])
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
    after: int = Query(default=0, ge=0, le=9_223_372_036_854_775_807),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
    wait_seconds: int = Query(default=60, ge=1, le=120),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, principal["id"])

    async def events():
        from app.routers.agent_runs import _event_cursor, _event_with_checkpoint_state

        cursor = _event_cursor(after, last_event_id)
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
                    if row["event_type"] in {"run.completed", "run.failed", "run.cancelled", "run.timed_out", "run.expired"}:
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
                        else "run.expired" if status == "expired"
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


@router.get("/network/speedtest/ping", response_model=CustomerSpeedtestPingResponse)
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


@router.post("/network/speedtest/upload", response_model=CustomerSpeedtestUploadResponse)
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


@router.get("/network-sessions", response_model=list[CustomerNetworkSessionResponse])
async def customer_network_sessions(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(current_user),
):
    """Return owner-scoped network session history without private device evidence."""
    decoded = decode_timestamp_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": (
            "id,network_id,status,started_at,last_heartbeat_at,expires_at,ended_at,end_reason,"
            "network:partner_networks(id,name,ssid_label,gateway_type,status,"
            "location:partner_locations(id,name,address))"
        ),
        "order": "started_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = timestamp_id_filter(decoded, "started_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    rows = await repository(request).select("network_sessions", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "started_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.get("/wallet", response_model=CustomerWalletListResponse)
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


@router.get("/wallet/ledger", response_model=list[CustomerLedgerEntryResponse])
async def customer_wallet_ledger(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    before: datetime | None = Query(default=None),
    wallet_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    if cursor and before:
        raise HTTPException(422, "Use either cursor or before, not both")
    decoded = decode_created_at_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    repo = repository(request)
    wallets = await repo.select("wallet_accounts", {
        "owner_type": "eq.user", "owner_id": f"eq.{principal['id']}",
        "select": "id", "limit": "20",
    })
    ids = [str(row["id"]) for row in wallets if row.get("id")]
    if wallet_id is not None:
        if str(wallet_id) not in ids:
            raise HTTPException(404, "wallet_not_found")
        ids = [str(wallet_id)]
    if not ids:
        response.headers["X-Pagination-Mode"] = "keyset"
        return []
    filters = {
        "wallet_id": f"in.({','.join(ids)})",
        "select": "id,wallet_id,entry_type,amount,balance_after,reference_type,reference_id,description,created_at",
        "order": "created_at.desc,id.desc", "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        filters["or"] = cursor_filter
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["created_at"] = f"lt.{before.astimezone(timezone.utc).isoformat()}"
    rows = await repo.select("credit_ledger", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.get("/usage", response_model=list[CustomerUsageRecordResponse])
async def customer_usage(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    if cursor and before:
        raise HTTPException(422, "Use either cursor or before, not both")
    decoded = decode_created_at_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,run_id,provider_key,model_key,input_tokens,output_tokens,estimated_cost,actual_cost,status,latency_ms,created_at",
        "order": "created_at.desc,id.desc", "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        filters["or"] = cursor_filter
    if before:
        if before.tzinfo is None:
            raise HTTPException(422, "before must include a timezone")
        filters["created_at"] = f"lt.{before.astimezone(timezone.utc).isoformat()}"
    rows = await repository(request).select("llm_usage", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    return rows


@router.get("/usage/analytics", response_model=CustomerUsageAnalyticsResponse)
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


@router.get("/entitlements", response_model=list[CustomerEntitlementResponse])
async def customer_entitlements(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("user_entitlements", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,entitlement_key,source_type,status,starts_at,expires_at,metadata",
        "order": "created_at.desc", "limit": "200",
    })


@router.get("/quotas", response_model=list[CustomerQuotaResponse])
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
    # Resolve the exact active window for every policy. This preserves global and
    # platform-scoped usage and avoids selecting a stale window from long history.
    now = datetime.now(timezone.utc)
    usage_conditions = []
    for policy in policies:
        try:
            window_seconds = int(policy.get("window_seconds") or 0)
        except (TypeError, ValueError):
            continue
        if window_seconds <= 0:
            continue
        window_epoch = (int(now.timestamp()) // window_seconds) * window_seconds
        window_start = datetime.fromtimestamp(window_epoch, timezone.utc).isoformat()
        usage_conditions.append(
            f"and(policy_id.eq.{policy['id']},window_start.eq.{window_start})"
        )
    usage_rows = []
    if usage_conditions:
        usage_rows = await repo.select("quota_usage", {
            "or": "(" + ",".join(usage_conditions) + ")",
            "select": "policy_id,used_value,window_start,updated_at",
            "limit": "200",
        })
    usage_by_policy = {str(row["policy_id"]): row for row in usage_rows if row.get("policy_id")}
    return [{**policy, "usage": usage_by_policy.get(str(policy["id"]))} for policy in policies]


class AccessCodeRedeem(BaseModel):
    code: str = Field(min_length=8, max_length=128)
    network_id: UUID
    verification_session_id: UUID


@router.post("/access-codes/redeem", response_model=CustomerAccessCodeRedeemResponse)
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
        if "ACCESS_CODE_INVALID" in message:
            raise HTTPException(422, "Access code is invalid")
        if "REWARD_QUOTA_EXHAUSTED" in message:
            raise HTTPException(409, "The reward redemption quota has been reached")
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
