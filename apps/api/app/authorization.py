from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, HTTPException, Request

from app.dependencies import current_user


def _repository(request: Request):
    # Lazy import avoids a router/authorization import cycle.
    from app.routers.conversations import repository
    return repository(request)


PARTNER_ROLES = {
    "partner_owner", "partner_admin", "location_manager",
    "partner_staff", "partner_analyst",
}
PLATFORM_PRIVILEGED_ROLES = {
    "super_admin", "platform_admin", "security_admin", "support_admin",
    "finance_admin", "partner_manager", "read_only_analyst",
}


async def require_customer_context(request: Request, user: dict[str, Any]) -> dict[str, Any]:
    """Customer is the authenticated base role; partner and platform principals use separate APIs."""
    repo = _repository(request)
    memberships = await repo.select("partner_members", {
        "user_id": f"eq.{user['id']}", "status": "eq.active",
        "select": "partner_id,role_key", "limit": "100",
    })
    if memberships:
        raise HTTPException(403, "Partner principals must use the Partner API")

    assignments = await repo.select("user_role_assignments", {
        "user_id": f"eq.{user['id']}", "scope_type": "eq.platform",
        "scope_id": "is.null",
        "or": f"(expires_at.is.null,expires_at.gt.{datetime.now(timezone.utc).isoformat()})",
        "select": "role_id", "limit": "100",
    })
    role_ids = [row.get("role_id") for row in assignments if row.get("role_id")]
    if role_ids:
        roles = await repo.select("roles", {
            "id": f"in.({','.join(role_ids)})", "select": "key,scope", "limit": "100",
        })
        if any(row.get("key") in PLATFORM_PRIVILEGED_ROLES for row in roles):
            raise HTTPException(403, "Platform principals must use the administrative API")
    return {**user, "principal_role": "customer", "tenant_id": None}


async def require_partner_context(
    request: Request, user: dict[str, Any], partner_id: str | None = None,
) -> dict[str, Any]:
    """Resolve partner tenant exclusively from active server-side membership."""
    repo = _repository(request)
    rows = await repo.select("partner_members", {
        "user_id": f"eq.{user['id']}", "status": "eq.active",
        "select": "partner_id,role_key,location_id", "limit": "100",
    })
    memberships = [
        row for row in rows
        if row.get("role_key") in PARTNER_ROLES
        and (partner_id is None or row.get("partner_id") == partner_id)
    ]
    if not memberships:
        raise HTTPException(403, "An active Partner membership is required")
    role_rank = {
        "partner_owner": 0, "partner_admin": 1, "partner_analyst": 2,
        "location_manager": 3, "partner_staff": 4,
    }
    memberships.sort(key=lambda row: role_rank.get(row.get("role_key"), 99))
    partner_ids = {str(row["partner_id"]) for row in memberships if row.get("partner_id")}
    if partner_id is None and len(partner_ids) > 1:
        raise HTTPException(409, "Select a partner tenant explicitly")
    if len(partner_ids) != 1:
        raise HTTPException(403, "Partner tenant membership is invalid")
    resolved_id = next(iter(partner_ids))
    orgs = await repo.select("partner_organizations", {
        "id": f"eq.{resolved_id}", "status": "eq.active",
        "select": "id,display_name,legal_name,status", "limit": "1",
    })
    if not orgs:
        raise HTTPException(403, "Partner tenant is inactive")
    selected = memberships[0]
    return {
        **user,
        "principal_role": selected["role_key"],
        "partner_id": resolved_id,
        "location_id": selected.get("location_id"),
        "partner": orgs[0],
    }



async def customer_principal(
    request: Request, user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    return await require_customer_context(request, user)


async def require_platform_context(request: Request, user: dict[str, Any]) -> dict[str, Any]:
    """Resolve platform authority only from active, server-managed role assignments."""
    repo = _repository(request)
    assignments = await repo.select("user_role_assignments", {
        "user_id": f"eq.{user['id']}",
        "scope_type": "eq.platform",
        "scope_id": "is.null",
        "or": f"(expires_at.is.null,expires_at.gt.{datetime.now(timezone.utc).isoformat()})",
        "select": "id,role_id,expires_at",
        "limit": "100",
    })
    role_ids = [str(row["role_id"]) for row in assignments if row.get("role_id")]
    if not role_ids:
        raise HTTPException(403, "An active platform role assignment is required")
    roles = await repo.select("roles", {
        "id": f"in.({','.join(role_ids)})",
        "scope": "eq.platform",
        "select": "id,key,scope",
        "limit": "100",
    })
    allowed = {row["key"] for row in roles if row.get("key") in PLATFORM_PRIVILEGED_ROLES}
    if not allowed:
        raise HTTPException(403, "Platform administrative permission is required")
    return {**user, "principal_role": sorted(allowed)[0], "platform_roles": sorted(allowed)}
