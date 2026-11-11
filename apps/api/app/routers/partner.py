from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request

from app.authorization import require_partner_context
from app.dependencies import current_user
from app.routers.conversations import repository


router = APIRouter(prefix="/api/v1/partner", tags=["partner"])


@router.get("/context")
async def partner_context(
    request: Request,
    partner_id: str | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, partner_id)
    return {
        "principal": {"user_id": principal["id"], "role": principal["principal_role"]},
        "tenant": principal["partner"],
        "location_scope": principal.get("location_id"),
    }


@router.get("/locations")
async def partner_locations(
    request: Request,
    partner_id: str | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, partner_id)
    filters = {
        "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,partner_id,name,address,created_at",
        "order": "name.asc", "limit": "200",
    }
    if principal["principal_role"] in {"location_manager", "partner_staff"}:
        if not principal.get("location_id"):
            return []
        filters["id"] = f"eq.{principal['location_id']}"
    return await repository(request).select("partner_locations", filters)
