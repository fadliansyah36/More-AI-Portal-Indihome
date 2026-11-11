from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.authorization import require_customer_context
from app.dependencies import current_user
from app.routers.conversations import ConversationCreate, MessageCreate, repository


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
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("conversations", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,title,status,created_at,updated_at",
        "order": "updated_at.desc", "limit": "100",
    })


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
    return await repository(request).rpc("moreai_enqueue_chat_run", {
        "p_user_id": principal["id"], "p_conversation_id": str(conversation_id),
        "p_content": body.content, "p_agent_key": body.agent_key,
        "p_idempotency_key": idempotency_key,
    })


@router.get("/agent-runs")
async def customer_agent_runs(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).select("agent_runs", {
        "user_id": f"eq.{principal['id']}",
        "select": "id,conversation_id,status,input,output,error,attempt,max_attempts,created_at,started_at,finished_at",
        "order": "created_at.desc", "limit": "100",
    })


@router.get("/agent-runs/{run_id}")
async def customer_agent_run(
    run_id: UUID, request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    return await repository(request).owned_record("agent_runs", run_id, principal["id"])



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
            else:
                idle_rounds += 1
                run = await repo.owned_record("agent_runs", run_id, principal["id"])
                status = run.get("status")
                if status in {"succeeded", "failed", "cancelled", "expired"}:
                    terminal_event = "run.completed" if status == "succeeded" else "run.cancelled" if status == "cancelled" else "run.failed"
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


@router.get("/wallet")
async def customer_wallet(request: Request, user: dict[str, Any] = Depends(current_user)):
    principal = await require_customer_context(request, user)
    rows = await repository(request).select("wallet_accounts", {
        "owner_type": "eq.user", "owner_id": f"eq.{principal['id']}",
        "status": "eq.active",
        "select": "id,currency,balance,status,created_at,updated_at",
        "order": "created_at.asc", "limit": "10",
    })
    return {"wallets": rows}


@router.get("/wallet/ledger")
async def customer_wallet_ledger(
    request: Request, limit: int = Query(default=50, ge=1, le=100),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    repo = repository(request)
    wallets = await repo.select("wallet_accounts", {
        "owner_type": "eq.user", "owner_id": f"eq.{principal['id']}",
        "select": "id", "limit": "10",
    })
    wallet_ids = [str(row["id"]) for row in wallets if row.get("id")]
    if not wallet_ids:
        return []
    filters = {
        "wallet_id": f"in.({','.join(wallet_ids)})",
        "select": "id,wallet_id,entry_type,amount,balance_after,reference_type,reference_id,description,created_at",
        "order": "created_at.desc", "limit": str(limit),
    }
    if before is not None:
        filters["created_at"] = f"lt.{before.astimezone(timezone.utc).isoformat()}"
    return await repo.select("credit_ledger", filters)


@router.get("/usage")
async def customer_usage(
    request: Request, limit: int = Query(default=50, ge=1, le=100),
    before: datetime | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_customer_context(request, user)
    filters = {
        "user_id": f"eq.{principal['id']}",
        "select": "id,run_id,provider_key,model_key,input_tokens,output_tokens,estimated_cost,actual_cost,status,latency_ms,created_at",
        "order": "created_at.desc", "limit": str(limit),
    }
    if before is not None:
        filters["created_at"] = f"lt.{before.astimezone(timezone.utc).isoformat()}"
    return await repository(request).select("llm_usage", filters)


@router.get("/entitlements")
async def customer_entitlements(request: Request, user: dict[str, Any] = Depends(current_user)):
    principal = await require_customer_context(request, user)
    now = datetime.now(timezone.utc).isoformat()
    return await repository(request).select("user_entitlements", {
        "user_id": f"eq.{principal['id']}", "status": "eq.active",
        "starts_at": f"lte.{now}", "or": f"(expires_at.is.null,expires_at.gt.{now})",
        "select": "id,entitlement_key,source_type,source_id,status,starts_at,expires_at,metadata,created_at",
        "order": "starts_at.desc", "limit": "100",
    })


@router.get("/quotas")
async def customer_quotas(request: Request, user: dict[str, Any] = Depends(current_user)):
    principal = await require_customer_context(request, user)
    scope_id = f"eq.{principal['id']}"
    repo = repository(request)
    policies = await repo.select("quota_policies", {
        "scope_type": "eq.user", "scope_id": scope_id, "enabled": "eq.true",
        "select": "id,metric_key,limit_value,window_seconds,enabled", "limit": "100",
    })
    usage = await repo.select("quota_usage", {
        "scope_type": "eq.user", "scope_id": scope_id,
        "select": "policy_id,metric_key,window_start,used_value,updated_at",
        "order": "window_start.desc", "limit": "200",
    })
    usage_by_policy = {str(row.get("policy_id")): row for row in usage}
    return [{**policy, "usage": usage_by_policy.get(str(policy["id"]))} for policy in policies]


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
        "or": f"(and(scope_type.eq.global,scope_id.is.null),and(scope_type.eq.user,scope_id.eq.{principal['id']}))",
        "select": "id,scope_type,scope_id,metric_key,limit_value,window_seconds",
        "order": "metric_key.asc", "limit": "200",
    })
    if not policies:
        return []
    policy_ids = [str(row["id"]) for row in policies]
    usage_rows = await repo.select("quota_usage", {
        "policy_id": f"in.({','.join(policy_ids)})",
        "scope_type": "eq.user", "scope_id": f"eq.{principal['id']}",
        "select": "policy_id,used_value,window_start,updated_at",
        "limit": "500",
    })
    usage_by_policy = {str(row["policy_id"]): row for row in usage_rows}
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
