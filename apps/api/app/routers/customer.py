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
    workspace_id: UUID | None = None
    title: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerConversationMessageAttachmentResponse(BaseModel):
    id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int | None


class CustomerConversationCitationResponse(BaseModel):
    id: UUID
    document_id: UUID
    title: str
    similarity: float | None = None
    source_page: int | None = None
    char_start: int | None = None
    char_end: int | None = None
    marker: str


class CustomerConversationMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    model_key: str | None
    run_id: UUID | None
    created_at: datetime
    attachments: list[CustomerConversationMessageAttachmentResponse] = Field(default_factory=list)
    citations: list[CustomerConversationCitationResponse] = Field(default_factory=list)


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
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    if body.workspace_id is not None:
        from app.routers.workspaces import _workspace_access
        await _workspace_access(repo, body.workspace_id, principal["id"], "agent.run.create")
    return await repo.insert("conversations", {
        "user_id": principal["id"],
        "workspace_id": str(body.workspace_id) if body.workspace_id else None,
        "title": body.title, "status": "active", "metadata": {},
    })


@router.get("/conversations", response_model=list[CustomerConversationResponse])
async def customer_conversations(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(customer_principal),
):
    if cursor and before:
        raise HTTPException(422, "Use either cursor or before, not both")
    decoded = decode_updated_at_id_cursor(cursor)
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,workspace_id,title,status,created_at,updated_at",
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


def _customer_safe_run_output(output: Any) -> dict[str, Any] | None:
    if not isinstance(output, dict):
        return None
    text_value = output.get("text")
    if not isinstance(text_value, str):
        text_value = output.get("content")
    if not isinstance(text_value, str):
        return None
    safe_citations: list[dict[str, Any]] = []
    seen: set[str] = set()
    raw_citations = output.get("citations") if isinstance(output.get("citations"), list) else []
    for item in raw_citations[:100]:
        if not isinstance(item, dict):
            continue
        try:
            chunk_id = str(UUID(str(item.get("id"))))
            document_id = str(UUID(str(item.get("document_id"))))
        except (ValueError, TypeError, AttributeError):
            continue
        title, marker = item.get("title"), item.get("marker")
        if not isinstance(title, str) or not title.strip() or len(title) > 300:
            continue
        if marker != f"[source:{chunk_id}]" or chunk_id in seen:
            continue
        citation: dict[str, Any] = {
            "id": chunk_id, "document_id": document_id,
            "title": title, "marker": marker,
        }
        similarity = item.get("similarity")
        if isinstance(similarity, (int, float)) and not isinstance(similarity, bool):
            citation["similarity"] = max(0.0, min(1.0, float(similarity)))
        for field in ("source_page", "char_start", "char_end"):
            value = item.get(field)
            if isinstance(value, int) and not isinstance(value, bool):
                if (field == "source_page" and value > 0) or (field != "source_page" and value >= 0):
                    citation[field] = value
        safe_citations.append(citation)
        seen.add(chunk_id)
    return {"text": text_value, "citations": safe_citations}


async def _customer_conversation_message_citations(
    repo: Any, user_id: str, messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    run_ids = sorted({
        str(message["run_id"]) for message in messages
        if message.get("role") == "assistant" and message.get("run_id")
    })
    if not run_ids:
        return [{**message, "citations": []} for message in messages]

    runs = await repo.select("agent_runs", {
        "id": f"in.({','.join(run_ids)})",
        "user_id": f"eq.{user_id}",
        "select": "id,output",
        "limit": str(len(run_ids)),
    })
    citations_by_run: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        output = run.get("output") if isinstance(run.get("output"), dict) else {}
        raw_citations = output.get("citations") if isinstance(output.get("citations"), list) else []
        safe: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw_citations[:100]:
            if not isinstance(item, dict):
                continue
            try:
                chunk_id = str(UUID(str(item.get("id"))))
                document_id = str(UUID(str(item.get("document_id"))))
            except (ValueError, TypeError, AttributeError):
                continue
            title = item.get("title")
            marker = item.get("marker")
            if not isinstance(title, str) or not title.strip() or len(title) > 300:
                continue
            if marker != f"[source:{chunk_id}]" or chunk_id in seen:
                continue
            citation: dict[str, Any] = {
                "id": chunk_id, "document_id": document_id,
                "title": title[:300], "marker": marker,
            }
            similarity = item.get("similarity")
            if isinstance(similarity, (int, float)) and not isinstance(similarity, bool):
                citation["similarity"] = max(0.0, min(1.0, float(similarity)))
            for field in ("source_page", "char_start", "char_end"):
                value = item.get(field)
                if isinstance(value, int) and not isinstance(value, bool):
                    if (field == "source_page" and value > 0) or (field != "source_page" and value >= 0):
                        citation[field] = value
            safe.append(citation)
            seen.add(chunk_id)
        citations_by_run[str(run.get("id"))] = safe

    return [
        {
            **message,
            "citations": citations_by_run.get(str(message.get("run_id")), [])
            if message.get("role") == "assistant" else [],
        }
        for message in messages
    ]


def _customer_conversation_message_attachments(
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
    user: dict[str, Any] = Depends(customer_principal),
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
    messages = await _customer_conversation_message_citations(repo, principal["id"], messages)
    return {"conversation": conversation, "messages": messages}


@router.get("/conversations/{conversation_id}/messages", response_model=CustomerConversationMessagePageResponse)
async def customer_conversation_messages(
    conversation_id: UUID,
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
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
    items = await _customer_conversation_message_citations(repo, principal["id"], items)
    return {"items": items, "count": len(items)}


@router.post("/conversations/{conversation_id}/messages", status_code=202, response_model=CustomerMessageEnqueueResponse)
async def send_customer_message(
    conversation_id: UUID, body: MessageCreate, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    if not request.app.state.settings.agent_execution_enabled:
        raise HTTPException(503, "Agent execution is disabled until provider, entitlement and worker gates pass")
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "A 12–128 character Idempotency-Key header is required")
    repo = repository(request)
    conversation = await repo.owned_record("conversations", conversation_id, principal["id"])
    if conversation.get("workspace_id"):
        from app.routers.workspaces import _workspace_access
        await _workspace_access(repo, UUID(str(conversation["workspace_id"])), principal["id"], "agent.run.create")
    await _require_live_customer_runtime(repo, body.agent_key)
    if body.agent_configuration_id:
        return await repo.rpc("moreai_enqueue_chat_run_with_config", {
            "p_user_id": principal["id"],
            "p_conversation_id": str(conversation_id),
            "p_content": body.content,
            "p_agent_key": body.agent_key,
            "p_idempotency_key": idempotency_key,
            "p_agent_config_id": str(body.agent_configuration_id),
            "p_attachment_ids": [str(item) for item in body.attachment_ids],
        })
    return await repo.rpc("moreai_enqueue_chat_run_with_attachments", {
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
    user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    return await repository(request).owned_record("agent_runs", run_id, principal["id"])



@router.post("/agent-runs/{run_id}/cancel", response_model=CustomerAgentRunCancellationResponse)
async def customer_cancel_agent_run(
    run_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    await repo.owned_record("agent_runs", run_id, principal["id"])

    async def events():
        from app.routers.agent_runs import _event_cursor, _event_with_checkpoint_state, _safe_run_activity

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
                    safe_activity = _safe_run_activity(row)
                    safe_payload = {
                        key: value for key, value in safe_activity.items()
                        if key not in {"id", "sequence", "timestamp", "event_type"}
                    }
                    public_row = {
                        "id": row.get("id"), "event_type": row.get("event_type"),
                        "sequence": row.get("sequence"), "created_at": row.get("created_at"),
                        "payload": safe_payload,
                    }
                    if isinstance(row.get("checkpoint"), dict):
                        public_row["checkpoint"] = row["checkpoint"]
                    payload = json.dumps(public_row, separators=(",", ":"))
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
                    raw_error = run.get("error") if isinstance(run.get("error"), dict) else {}
                    safe_error = {"code": str(raw_error.get("code") or "agent_execution_failed")[:100]}
                    payload = json.dumps({
                        "run_id": str(run_id), "status": status,
                        "output": _customer_safe_run_output(run.get("output")),
                        "error": safe_error if status in {"failed", "timed_out", "expired"} else None,
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
    user: dict[str, Any] = Depends(customer_principal),
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
    request: Request, user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
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
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("user_entitlements", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,entitlement_key,source_type,status,starts_at,expires_at,metadata",
        "order": "created_at.desc", "limit": "200",
    })


@router.get("/quotas", response_model=list[CustomerQuotaResponse])
async def customer_quotas(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
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
    user: dict[str, Any] = Depends(customer_principal),
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


# Personal Memory is explicitly user-authored and separate from conversation history.
# It is not silently populated from chats, attachments, or unrelated workspace files.
CUSTOMER_MEMORY_CONSENT_VERSION = "2026-11-14.v1"


class CustomerAgentConfigurationCreate(BaseModel):
    runtime_key: Literal["manus", "toolcall"]
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    system_prompt: str = Field(default="", max_length=12000)
    tool_keys: list[str] = Field(default_factory=list, max_length=30)


class CustomerAgentConfigurationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    system_prompt: str | None = Field(default=None, max_length=12000)
    tool_keys: list[str] | None = Field(default=None, max_length=30)
    enabled: bool | None = None


class CustomerAgentConfigurationResponse(BaseModel):
    id: UUID
    runtime_key: Literal["manus", "toolcall"]
    name: str
    description: str
    system_prompt: str
    tool_keys: list[str]
    enabled: bool
    version: int
    created_at: datetime
    updated_at: datetime


async def _require_live_customer_runtime(repo: Any, runtime_key: str) -> None:
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=90)).isoformat()
    snapshots = await repo.select("moreai_worker_capability_snapshots", {
        "last_seen_at": f"gt.{cutoff}",
        "select": "runtime_keys,status",
        "limit": "100",
    })
    if not any(
        row.get("status") == "healthy"
        and isinstance(row.get("runtime_keys"), list)
        and runtime_key in row["runtime_keys"]
        for row in snapshots
    ):
        raise HTTPException(503, "No healthy worker currently advertises this Agent runtime; the task was not queued")


def _validate_customer_agent_tool_keys(runtime_key: str, tool_keys: list[str]) -> list[str]:
    from engine.tools.catalog import tool_catalog
    available = {
        str(item["key"])
        for item in tool_catalog()
        if str(item["key"]) != "run"
        and runtime_key in item.get("available_by_default", [])
        and bool(item.get("enabled_by_default"))
    }
    normalized = sorted({key.strip() for key in tool_keys if isinstance(key, str) and key.strip()})
    if len(normalized) != len(tool_keys) or not set(normalized).issubset(available):
        raise HTTPException(422, "Agent configuration contains a tool that is not registered for this runtime")
    return normalized


@router.get("/agents/configurations", response_model=list[CustomerAgentConfigurationResponse])
async def list_customer_agent_configurations(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("moreai_customer_agent_configs", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,runtime_key,name,description,system_prompt,tool_keys,enabled,version,created_at,updated_at",
        "order": "updated_at.desc,id.desc",
        "limit": "100",
    })


@router.post("/agents/configurations", status_code=201, response_model=CustomerAgentConfigurationResponse)
async def create_customer_agent_configuration(
    body: CustomerAgentConfigurationCreate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    return await repository(request).insert("moreai_customer_agent_configs", {
        "user_id": principal["id"],
        "runtime_key": body.runtime_key,
        "name": body.name.strip(),
        "description": body.description.strip(),
        "system_prompt": body.system_prompt.strip(),
        "tool_keys": _validate_customer_agent_tool_keys(body.runtime_key, body.tool_keys),
        "enabled": True,
        "version": 1,
    })


@router.patch("/agents/configurations/{configuration_id}", response_model=CustomerAgentConfigurationResponse)
async def update_customer_agent_configuration(
    configuration_id: UUID, body: CustomerAgentConfigurationUpdate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    current = await repo.select("moreai_customer_agent_configs", {
        "id": f"eq.{configuration_id}", "user_id": f"eq.{principal['id']}",
        "select": "id,runtime_key,name,description,system_prompt,tool_keys,enabled,version",
        "limit": "1",
    })
    if not current:
        raise HTTPException(404, "Agent configuration not found")
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "At least one configuration field must be supplied")
    if any(value is None for value in changes.values()):
        raise HTTPException(422, "Agent configuration updates cannot contain null values")
    if "name" in changes:
        changes["name"] = changes["name"].strip()
    if "description" in changes:
        changes["description"] = changes["description"].strip()
    if "system_prompt" in changes:
        changes["system_prompt"] = changes["system_prompt"].strip()
    if "tool_keys" in changes:
        changes["tool_keys"] = _validate_customer_agent_tool_keys(
            str(current[0]["runtime_key"]), changes["tool_keys"],
        )
    changes["version"] = int(current[0].get("version") or 1) + 1
    changes["updated_at"] = datetime.now(timezone.utc).isoformat()
    rows = await repo.update("moreai_customer_agent_configs", {
        "id": f"eq.{configuration_id}", "user_id": f"eq.{principal['id']}",
        "select": "id,runtime_key,name,description,system_prompt,tool_keys,enabled,version,created_at,updated_at",
    }, changes)
    if not rows:
        raise HTTPException(404, "Agent configuration not found")
    return rows[0]


@router.delete("/agents/configurations/{configuration_id}", status_code=204)
async def delete_customer_agent_configuration(
    configuration_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    rows = await repository(request).delete("moreai_customer_agent_configs", {
        "id": f"eq.{configuration_id}", "user_id": f"eq.{principal['id']}",
        "select": "id",
    })
    if not rows:
        raise HTTPException(404, "Agent configuration not found")
    return Response(status_code=204)


class CustomerMemoryConsentUpdate(BaseModel):
    enabled: bool
    consent_version: Literal["2026-11-14.v1"] = CUSTOMER_MEMORY_CONSENT_VERSION


class CustomerMemoryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=4000)
    retention_days: Literal[30, 90, 180, 365] = 90


class CustomerMemoryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1, max_length=4000)
    retention_days: Literal[30, 90, 180, 365] | None = None


class CustomerMemoryItemResponse(BaseModel):
    id: UUID
    title: str
    content: str
    source_type: Literal["user_created"]
    scope: Literal["personal"]
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class CustomerMemoryResponse(BaseModel):
    enabled: bool
    consent_version: str | None = None
    consented_at: datetime | None = None
    disabled_at: datetime | None = None
    items: list[CustomerMemoryItemResponse] = Field(default_factory=list)


@router.get("/memory", response_model=CustomerMemoryResponse)
async def customer_personal_memory(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    now = datetime.now(timezone.utc)
    # Opportunistically purge expired owner records before returning the current memory view.
    await repo.delete("moreai_customer_memories", {
        "user_id": f"eq.{principal['id']}",
        "expires_at": f"lte.{now.isoformat()}",
        "select": "id",
    })
    preferences = await repo.select("moreai_customer_memory_preferences", {
        "user_id": f"eq.{principal['id']}",
        "select": "enabled,consent_version,consented_at,disabled_at",
        "limit": "1",
    })
    preference = preferences[0] if preferences else {}
    # Expired records are excluded from the usable/reviewable collection even if
    # a scheduled database cleanup has not yet physically purged them.
    items = await repo.select("moreai_customer_memories", {
        "user_id": f"eq.{principal['id']}",
        "expires_at": f"gt.{now.isoformat()}",
        "select": "id,title,content,source_type,scope,expires_at,created_at,updated_at",
        "order": "updated_at.desc,id.desc",
        "limit": "200",
    })
    return {
        "enabled": bool(preference.get("enabled", False)),
        "consent_version": preference.get("consent_version"),
        "consented_at": preference.get("consented_at"),
        "disabled_at": preference.get("disabled_at"),
        "items": items,
    }


@router.put("/memory/consent")
async def update_customer_memory_consent(
    body: CustomerMemoryConsentUpdate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    result = await repository(request).rpc("moreai_customer_set_memory_consent", {
        "p_user_id": principal["id"],
        "p_enabled": body.enabled,
        "p_consent_version": body.consent_version,
    })
    if isinstance(result, list):
        result = result[0] if result else None
    if not isinstance(result, dict):
        raise HTTPException(502, "Memory consent state was not persisted")
    return {
        "enabled": bool(result.get("enabled", False)),
        "consent_version": result.get("consent_version"),
        "consented_at": result.get("consented_at"),
        "disabled_at": result.get("disabled_at"),
        "updated_at": result.get("updated_at"),
    }


@router.post("/memory", status_code=201, response_model=CustomerMemoryItemResponse)
async def create_customer_memory(
    body: CustomerMemoryCreate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    if not body.title.strip() or not body.content.strip():
        raise HTTPException(422, "Memory title and content cannot be blank")
    repo = repository(request)
    preferences = await repo.select("moreai_customer_memory_preferences", {
        "user_id": f"eq.{principal['id']}", "select": "enabled,consent_version", "limit": "1",
    })
    if not preferences or not preferences[0].get("enabled") or preferences[0].get("consent_version") != CUSTOMER_MEMORY_CONSENT_VERSION:
        raise HTTPException(403, "Personal Memory requires current explicit consent")
    now = datetime.now(timezone.utc)
    return await repo.insert("moreai_customer_memories", {
        "user_id": principal["id"],
        "title": body.title.strip(),
        "content": body.content.strip(),
        "source_type": "user_created",
        "scope": "personal",
        "expires_at": (now + timedelta(days=body.retention_days)).isoformat(),
    })


@router.patch("/memory/{memory_id}", response_model=CustomerMemoryItemResponse)
async def update_customer_memory(
    memory_id: UUID, body: CustomerMemoryUpdate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "At least one memory field must be supplied")
    if any(changes.get(field) is None for field in ("title", "content", "retention_days") if field in changes):
        raise HTTPException(422, "Memory updates cannot contain null values")
    if any(not changes[field].strip() for field in ("title", "content") if field in changes):
        raise HTTPException(422, "Memory title and content cannot be blank")
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {"updated_at": now.isoformat()}
    if "title" in changes:
        payload["title"] = changes["title"].strip()
    if "content" in changes:
        payload["content"] = changes["content"].strip()
    if "retention_days" in changes:
        payload["expires_at"] = (
            now + timedelta(days=changes["retention_days"])
        ).isoformat()
    rows = await repository(request).update("moreai_customer_memories", {
        "id": f"eq.{memory_id}", "user_id": f"eq.{principal['id']}",
        "expires_at": f"gt.{datetime.now(timezone.utc).isoformat()}",
        "select": "id,title,content,source_type,scope,expires_at,created_at,updated_at",
    }, payload)
    if not rows:
        raise HTTPException(404, "Memory not found")
    return rows[0]


@router.delete("/memory/{memory_id}", status_code=204)
async def delete_customer_memory(
    memory_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    rows = await repository(request).delete("moreai_customer_memories", {
        "id": f"eq.{memory_id}", "user_id": f"eq.{principal['id']}",
        "select": "id",
    })
    if not rows:
        raise HTTPException(404, "Memory not found")
    return Response(status_code=204)


@router.post("/agent-runs/{run_id}/retry", status_code=202, response_model=CustomerMessageEnqueueResponse)
async def retry_customer_agent_run(
    run_id: UUID, request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Create a new durable run from a terminal failed/cancelled run using the canonical enqueue RPC."""
    principal = await require_customer_context(request, user)
    if not request.app.state.settings.agent_execution_enabled:
        raise HTTPException(503, "Agent execution is disabled until provider, entitlement and worker gates pass")
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "A 12–128 character Idempotency-Key header is required")
    repo = repository(request)
    original = await repo.owned_record("agent_runs", run_id, principal["id"])
    if original.get("status") not in {"failed", "timed_out", "expired"}:
        raise HTTPException(409, "Only failed, timed-out, or expired runs can be manually retried")
    source = original.get("input") if isinstance(original.get("input"), dict) else {}
    prompt = source.get("prompt")
    agent_key = source.get("agent_key", "manus")
    conversation_value = original.get("conversation_id") or source.get("conversation_id")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100000:
        raise HTTPException(409, "Original run does not contain a retryable prompt")
    if agent_key not in {"manus", "planning", "toolcall"}:
        raise HTTPException(409, "Original runtime is no longer supported")
    await _require_live_customer_runtime(repo, agent_key)
    try:
        conversation_id = UUID(str(conversation_value))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(409, "Original conversation is unavailable")
    await repo.owned_record("conversations", conversation_id, principal["id"])
    # A manual rerun is only safe before any non-read-only tool has started.
    # Side-effecting tools may have partially completed even when their final event failed.
    safe_replay_tools = {
        "create_chat_completion", "knowledge_search", "google_search",
        "planning", "workspace_read_file", "terminate",
    }
    events = await repo.select("agent_run_events", {
        "run_id": f"eq.{run_id}",
        "select": "event_type,payload",
        "order": "sequence.asc",
        "limit": "1000",
    })
    for event in events:
        event_type = str(event.get("event_type") or "")
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        tool_key = payload.get("tool")
        if event_type.startswith("tool.") and (not isinstance(tool_key, str) or tool_key not in safe_replay_tools):
            raise HTTPException(
                409,
                "Manual rerun blocked because this run reached a side-effecting tool. Review its durable steps/artifacts before creating a new task.",
            )
    raw_attachment_ids = source.get("attachment_ids") or []
    if not isinstance(raw_attachment_ids, list) or len(raw_attachment_ids) > 10:
        raise HTTPException(409, "Original attachment references are invalid")
    try:
        attachment_ids = [str(UUID(str(item))) for item in raw_attachment_ids]
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(409, "Original attachment references are invalid")
    saved_configuration = source.get("agent_config")
    if isinstance(saved_configuration, dict) and isinstance(saved_configuration.get("id"), str):
        return await repo.rpc("moreai_enqueue_chat_run_with_config_snapshot", {
            "p_user_id": principal["id"],
            "p_source_run_id": str(run_id),
            "p_conversation_id": str(conversation_id),
            "p_content": prompt,
            "p_agent_key": agent_key,
            "p_idempotency_key": idempotency_key,
            "p_agent_config_snapshot": saved_configuration,
            "p_attachment_ids": attachment_ids,
        })
    return await repo.rpc("moreai_enqueue_chat_run_with_attachments", {
        "p_user_id": principal["id"],
        "p_conversation_id": str(conversation_id),
        "p_content": prompt,
        "p_agent_key": agent_key,
        "p_idempotency_key": idempotency_key,
        "p_attachment_ids": attachment_ids,
    })


@router.delete("/memory", status_code=204)
async def clear_customer_personal_memory(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    principal = await require_customer_context(request, user)
    await repository(request).rpc("moreai_customer_clear_personal_memory", {
        "p_user_id": principal["id"],
    })
    return Response(status_code=204)
