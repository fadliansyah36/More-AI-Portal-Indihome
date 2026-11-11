from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Request

from app.authorization import require_platform_context, require_platform_permission
from app.dependencies import current_user
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/admin", tags=["platform-admin"])


async def platform_admin(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_context(request, user)


async def overview_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "platform.overview.read")


async def partner_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "partner.organization.read")


async def audit_reader(request: Request, user: dict[str, Any] = Depends(current_user)):
    return await require_platform_permission(request, user, "platform.audit.read")


@router.get("/context")
async def admin_context(principal=Depends(platform_admin)):
    return {"principal": {"user_id": principal["id"], "roles": principal["platform_roles"]}}


@router.get("/overview")
async def admin_overview(request: Request, principal=Depends(overview_reader)):
    repo = repository(request)
    # Counts are derived from bounded live records; this endpoint intentionally
    # avoids exposing PII or relying on client-supplied role/tenant filters.
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
    # Avoid leaking raw prompts, outputs, message content or provider secrets to the admin table.
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
