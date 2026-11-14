from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.authorization import require_platform_context, require_platform_permission
from app.dependencies import current_user
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/admin", tags=["platform-admin"])


class PartnerStatusUpdate(BaseModel):
    status: Literal["pending", "active", "suspended", "rejected", "closed"]


async def platform_admin(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_context(request, user)


async def overview_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "platform.overview.read")


async def partner_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "partner.organization.read")


async def partner_manager(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "partner.organization.manage")


async def audit_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "platform.audit.read")


@router.get("/context")
async def admin_context(principal=Depends(platform_admin)):
    return {"principal": {"user_id": principal["id"], "roles": principal["platform_roles"]}}


@router.get("/overview")
async def admin_overview(request: Request, principal=Depends(overview_reader)):
    repo = repository(request)
    specs = {
        "users": ("profiles", "id"),
        "partners": ("partner_organizations", "id"),
        "locations": ("partner_locations", "id"),
        "active_network_sessions": ("network_sessions", "id"),
        "agent_runs": ("agent_runs", "id"),
        "pending_tool_approvals": ("agent_tool_approvals", "id"),
    }
    totals: dict[str, int | None] = {}
    for key, (table, column) in specs.items():
        filters = {"select": column, "limit": "500"}
        if key == "active_network_sessions":
            filters["status"] = "eq.active"
        if key == "pending_tool_approvals":
            filters["status"] = "eq.pending"
        rows = await repo.select(table, filters)
        totals[key] = len(rows) if len(rows) < 500 else None
    recent_runs = await repo.select("agent_runs", {
        "select": "id,status,created_at,started_at,finished_at,attempt,max_attempts",
        "order": "created_at.desc", "limit": "10",
    })
    recent_partners = await repo.select("partner_organizations", {
        "select": "id,display_name,status,created_at",
        "order": "created_at.desc", "limit": "10",
    })
    return {
        "totals": totals,
        "recent_agent_runs": recent_runs,
        "recent_partners": recent_partners,
        "count_note": "Counts are exact up to 499; null means at least 500 records.",
    }


@router.get("/partners")
async def admin_partners(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    principal=Depends(partner_reader),
):
    rows = await repository(request).select("partner_organizations", {
        "select": "id,display_name,legal_name,status,created_at,updated_at",
        "order": "created_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    })
    return {"items": rows, "limit": limit, "offset": offset}


@router.patch("/partners/{partner_id}/status")
async def update_partner_status(
    partner_id: UUID,
    body: PartnerStatusUpdate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    principal=Depends(partner_manager),
):
    if not idempotency_key or not 12 <= len(idempotency_key) <= 128:
        raise HTTPException(400, "A 12–128 character Idempotency-Key header is required")
    return await repository(request).rpc("moreai_admin_update_partner_status", {
        "p_actor_user_id": principal["id"],
        "p_partner_id": str(partner_id),
        "p_status": body.status,
        "p_idempotency_key": idempotency_key,
        "p_correlation_id": getattr(request.state, "correlation_id", None),
    })


@router.get("/agent-runs")
async def admin_agent_runs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    status: str | None = Query(default=None, max_length=32),
    principal=Depends(overview_reader),
):
    filters = {
        "select": "id,user_id,workspace_id,conversation_id,status,attempt,max_attempts,created_at,started_at,finished_at,error",
        "order": "created_at.desc", "limit": str(limit), "offset": str(offset),
    }
    if status:
        filters["status"] = f"eq.{status}"
    rows = await repository(request).select("agent_runs", filters)
    return {"items": rows, "limit": limit, "offset": offset}


@router.get("/audit")
async def admin_audit(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    principal=Depends(audit_reader),
):
    rows = await repository(request).select("admin_audit_logs", {
        "select": "id,actor_user_id,action,resource_type,resource_id,scope_type,scope_id,correlation_id,outcome,created_at",
        "order": "created_at.desc", "limit": str(limit), "offset": str(offset),
    })
    return {"items": rows, "limit": limit, "offset": offset}


class LlmProviderMutation(BaseModel):
    key: Literal["google", "openai", "anthropic"]
    display_name: str = Field(min_length=2, max_length=120)
    enabled: bool = False


class LlmModelMutation(BaseModel):
    provider_id: UUID
    key: str = Field(min_length=1, max_length=160)
    display_name: str = Field(min_length=2, max_length=160)
    input_cost_per_million: float = Field(ge=0)
    output_cost_per_million: float = Field(ge=0)
    max_input_tokens: int | None = Field(default=None, ge=1)
    max_output_tokens: int | None = Field(default=None, ge=1)
    capabilities: list[str] = Field(default_factory=list, max_length=32)
    enabled: bool = False


class LlmRouteMutation(BaseModel):
    task_type: Literal["general"] = "general"
    model_id: UUID
    fallback_model_id: UUID | None = None
    priority: int = Field(default=100, ge=0, le=10000)
    enabled: bool = False


async def model_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "platform.models.read")


async def model_manager(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "platform.models.manage")


@router.get("/providers")
async def admin_llm_providers(request: Request, principal=Depends(model_reader)):
    """Return provider metadata only; provider config and credentials are never serialized."""
    repo = repository(request)
    providers = await repo.select("llm_providers", {
        "select": "id,key,display_name,enabled,created_at,updated_at",
        "order": "key.asc", "limit": "100",
    })
    models = await repo.select("llm_models", {
        "select": "id,provider_id,key,display_name,input_cost_per_million,output_cost_per_million,max_input_tokens,max_output_tokens,capabilities,enabled,created_at,updated_at",
        "order": "provider_id.asc,key.asc", "limit": "500",
    })
    routes = await repo.select("llm_routing_policies", {
        "select": "id,scope_type,scope_id,task_type,model_id,priority,fallback_model_id,enabled,created_at",
        "scope_type": "eq.platform", "scope_id": "is.null",
        "order": "priority.asc", "limit": "200",
    })
    return {"providers": providers, "models": models, "routing_policies": routes}


@router.post("/providers", status_code=201)
async def create_or_update_llm_provider(
    body: LlmProviderMutation,
    request: Request,
    provider_id: UUID | None = Query(default=None),
    principal=Depends(model_manager),
):
    # Credential readiness is deliberately false: registry edits cannot activate a provider.
    return await repository(request).rpc("moreai_admin_mutate_llm_provider", {
        "p_actor_user_id": principal["id"],
        "p_provider_id": str(provider_id) if provider_id else None,
        "p_key": body.key,
        "p_display_name": body.display_name.strip(),
        "p_enabled": body.enabled,
        "p_credentials_ready": False,
        "p_correlation_id": getattr(request.state, "correlation_id", None),
    })


@router.post("/models", status_code=201)
async def create_or_update_llm_model(
    body: LlmModelMutation,
    request: Request,
    model_id: UUID | None = Query(default=None),
    principal=Depends(model_manager),
):
    return await repository(request).rpc("moreai_admin_mutate_llm_model", {
        "p_actor_user_id": principal["id"],
        "p_model_id": str(model_id) if model_id else None,
        "p_provider_id": str(body.provider_id),
        "p_key": body.key.strip(),
        "p_display_name": body.display_name.strip(),
        "p_input_cost_per_million": body.input_cost_per_million,
        "p_output_cost_per_million": body.output_cost_per_million,
        "p_max_input_tokens": body.max_input_tokens,
        "p_max_output_tokens": body.max_output_tokens,
        "p_capabilities": body.capabilities,
        "p_enabled": body.enabled,
        "p_correlation_id": getattr(request.state, "correlation_id", None),
    })


@router.post("/routing-policies", status_code=201)
async def create_or_update_llm_route(
    body: LlmRouteMutation,
    request: Request,
    policy_id: UUID | None = Query(default=None),
    principal=Depends(model_manager),
):
    return await repository(request).rpc("moreai_admin_mutate_llm_route", {
        "p_actor_user_id": principal["id"],
        "p_policy_id": str(policy_id) if policy_id else None,
        "p_task_type": body.task_type,
        "p_model_id": str(body.model_id),
        "p_fallback_model_id": str(body.fallback_model_id) if body.fallback_model_id else None,
        "p_priority": body.priority,
        "p_enabled": body.enabled,
        "p_correlation_id": getattr(request.state, "correlation_id", None),
    })
