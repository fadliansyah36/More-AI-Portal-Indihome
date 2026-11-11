from __future__ import annotations

from typing import Any
from datetime import datetime, timezone, timedelta
import hashlib
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.authorization import require_partner_context
from app.dependencies import current_user
from app.routers.conversations import repository


router = APIRouter(prefix="/api/v1/partner", tags=["partner"])




class PartnerNetworkCreate(BaseModel):
    location_id: UUID
    provider_id: UUID | None = None
    name: str = Field(min_length=2, max_length=160)
    ssid_label: str | None = Field(default=None, max_length=120)
    gateway_type: str = Field(min_length=2, max_length=80)
    gateway_network_ref: str | None = Field(default=None, max_length=255)


class NetworkVerificationConfigInput(BaseModel):
    method_key: str = Field(pattern="^(gps|mikrotik_hotspot|radius|gateway|isp_api)$")
    config_public: dict[str, Any] = Field(default_factory=dict)
    secret_reference: str | None = Field(default=None, max_length=255)
    policy: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = False


class PartnerAccessCodeCreate(BaseModel):
    location_id: UUID | None = None
    network_id: UUID | None = None
    campaign_id: UUID | None = None
    reward_id: UUID | None = None
    expires_at: datetime
    max_redemptions: int = Field(default=1, ge=1, le=100000)


class PartnerLocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    address: dict[str, Any] = Field(default_factory=dict)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    timezone: str = Field(default="Asia/Jakarta", min_length=3, max_length=64)


class PartnerCampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    location_id: UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    budget: float | None = Field(default=None, ge=0)
    config: dict[str, Any] = Field(default_factory=dict)


class PartnerCampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=180)
    status: str | None = Field(default=None, pattern="^(draft|pending|active|paused|completed|cancelled)$")
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    budget: float | None = Field(default=None, ge=0)
    config: dict[str, Any] | None = None


class PartnerMemberInvite(BaseModel):
    user_id: UUID
    role_key: str = Field(pattern="^(partner_admin|location_manager|partner_staff|partner_analyst)$")
    location_id: UUID | None = None






@router.get("/tenants")
async def partner_tenants(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    """Return only active tenants for which the caller has an active partner membership."""
    repo = repository(request)
    rows = await repo.select("partner_members", {
        "user_id": f"eq.{user['id']}", "status": "eq.active",
        "select": "partner_id,role_key,location_id", "limit": "200",
    })
    role_rank = {
        "partner_owner": 0, "partner_admin": 1, "partner_analyst": 2,
        "location_manager": 3, "partner_staff": 4,
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("role_key") in role_rank and row.get("partner_id"):
            grouped.setdefault(str(row["partner_id"]), []).append(row)
    if not grouped:
        raise HTTPException(403, "An active Partner membership is required")
    orgs = await repo.select("partner_organizations", {
        "id": f"in.({','.join(grouped)})", "status": "eq.active",
        "select": "id,display_name,legal_name,status", "limit": "100",
    })
    result = []
    for org in orgs:
        memberships = grouped.get(str(org["id"]), [])
        if not memberships:
            continue
        memberships.sort(key=lambda row: role_rank.get(row.get("role_key"), 99))
        selected = memberships[0]
        result.append({
            "tenant": org,
            "principal_role": selected["role_key"],
            "location_scope": selected.get("location_id"),
        })
    return result


@router.get("/context")
async def partner_context(
    request: Request,
    partner_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    return {
        "principal": {"user_id": principal["id"], "role": principal["principal_role"]},
        "tenant": principal["partner"],
        "location_scope": principal.get("location_id"),
    }


@router.get("/locations")
async def partner_locations(
    request: Request,
    partner_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    filters = {
        "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,partner_id,name,address,status,created_at",
        "order": "name.asc", "limit": "200",
    }
    if principal["principal_role"] in {"location_manager", "partner_staff"}:
        if not principal.get("location_id"):
            return []
        filters["id"] = f"eq.{principal['location_id']}"
    return await repository(request).select("partner_locations", filters)


@router.get("/members")
async def partner_members(
    request: Request,
    partner_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    if principal["principal_role"] not in {"partner_owner", "partner_admin"}:
        raise HTTPException(403, "Partner owner or admin role is required to list members")
    return await repository(request).select("partner_members", {
        "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,partner_id,user_id,role_key,location_id,status,created_at",
        "order": "created_at.desc", "limit": "500",
    })



@router.get("/sessions")
async def partner_sessions(
    request: Request,
    partner_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    repo = repository(request)
    network_filters = {
        "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,location_id",
        "limit": "500",
    }
    if principal["principal_role"] in {"location_manager", "partner_staff"}:
        if not principal.get("location_id"):
            return []
        network_filters["location_id"] = f"eq.{principal['location_id']}"
    networks = await repo.select("partner_networks", network_filters)
    network_ids = [str(row["id"]) for row in networks if row.get("id")]
    if not network_ids:
        return []
    return await repo.select("network_sessions", {
        "network_id": f"in.({','.join(network_ids)})",
        "status": "eq.active",
        "select": "id,network_id,status,started_at,last_heartbeat_at,expires_at",
        "order": "started_at.desc",
        "limit": str(limit),
    })


@router.get("/campaigns")
async def partner_campaigns(
    request: Request,
    partner_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    filters = {
        "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,partner_id,location_id,name,status,starts_at,ends_at,budget,config,created_at,updated_at",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if principal["principal_role"] in {"location_manager", "partner_staff"}:
        if not principal.get("location_id"):
            return []
        filters["location_id"] = f"eq.{principal['location_id']}"
    return await repository(request).select("partner_campaigns", filters)


@router.get("/campaigns/{campaign_id}/rewards")
async def partner_campaign_rewards(
    campaign_id: UUID,
    request: Request,
    partner_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user),
):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    campaign = await repository(request).select("partner_campaigns", {
        "id": f"eq.{campaign_id}",
        "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,location_id",
        "limit": "1",
    })
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if principal["principal_role"] in {"location_manager", "partner_staff"}:
        if campaign[0].get("location_id") != principal.get("location_id"):
            raise HTTPException(403, "Campaign is outside the assigned location")
    return await repository(request).select("campaign_rewards", {
        "campaign_id": f"eq.{campaign_id}",
        "select": "id,campaign_id,reward_type,name,quantity_limit,quantity_claimed,reward_value,config,created_at",
        "order": "created_at.asc",
        "limit": "100",
    })


def _require_partner_manager(principal: dict[str, Any]) -> None:
    if principal["principal_role"] not in {"partner_owner", "partner_admin"}:
        raise HTTPException(403, "Partner owner or admin role is required")


async def _assert_partner_location(request: Request, partner_id: str, location_id: UUID | None) -> None:
    if location_id is None:
        return
    rows = await repository(request).select("partner_locations", {
        "id": f"eq.{location_id}", "partner_id": f"eq.{partner_id}",
        "select": "id", "limit": "1",
    })
    if not rows:
        raise HTTPException(422, "Location does not belong to the active partner tenant")


@router.post("/locations", status_code=201)
async def create_partner_location(body: PartnerLocationCreate, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    return await repository(request).insert("partner_locations", {
        "partner_id": principal["partner_id"], "name": body.name.strip(),
        "address": body.address, "latitude": body.latitude, "longitude": body.longitude,
        "timezone": body.timezone, "status": "active",
    })


@router.post("/campaigns", status_code=201)
async def create_partner_campaign(body: PartnerCampaignCreate, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    if body.starts_at and body.ends_at and body.ends_at <= body.starts_at:
        raise HTTPException(422, "Campaign end must be after campaign start")
    await _assert_partner_location(request, principal["partner_id"], body.location_id)
    return await repository(request).insert("partner_campaigns", {
        "partner_id": principal["partner_id"],
        "location_id": str(body.location_id) if body.location_id else None,
        "name": body.name.strip(), "status": "draft",
        "starts_at": body.starts_at.isoformat() if body.starts_at else None,
        "ends_at": body.ends_at.isoformat() if body.ends_at else None,
        "budget": body.budget, "config": body.config, "created_by": principal["id"],
    })


@router.patch("/campaigns/{campaign_id}")
async def update_partner_campaign(campaign_id: UUID, body: PartnerCampaignUpdate, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    repo = repository(request)
    existing = await repo.select("partner_campaigns", {
        "id": f"eq.{campaign_id}", "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,starts_at,ends_at,status", "limit": "1",
    })
    if not existing:
        raise HTTPException(404, "Campaign not found")
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "At least one campaign field must be supplied")
    starts = changes.get("starts_at", existing[0].get("starts_at"))
    ends = changes.get("ends_at", existing[0].get("ends_at"))
    if starts and ends:
        start_dt = starts if isinstance(starts, datetime) else datetime.fromisoformat(str(starts).replace("Z", "+00:00"))
        end_dt = ends if isinstance(ends, datetime) else datetime.fromisoformat(str(ends).replace("Z", "+00:00"))
        if end_dt <= start_dt:
            raise HTTPException(422, "Campaign end must be after campaign start")
    if changes.get("name") is not None:
        changes["name"] = changes["name"].strip()
    for key in ("starts_at", "ends_at"):
        if key in changes and changes[key] is not None:
            changes[key] = changes[key].isoformat()
    changes["updated_at"] = datetime.now(timezone.utc).isoformat()
    rows = await repo.update("partner_campaigns", {
        "id": f"eq.{campaign_id}", "partner_id": f"eq.{principal['partner_id']}",
    }, changes)
    if not rows:
        raise HTTPException(409, "Campaign update was not applied")
    return rows[0]


@router.post("/members", status_code=201)
async def invite_partner_member(body: PartnerMemberInvite, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    await _assert_partner_location(request, principal["partner_id"], body.location_id)
    existing = await repository(request).select("partner_members", {
        "partner_id": f"eq.{principal['partner_id']}", "user_id": f"eq.{body.user_id}",
        "select": "id,status", "limit": "1",
    })
    if existing:
        raise HTTPException(409, "User already has a membership record for this partner")
    return await repository(request).insert("partner_members", {
        "partner_id": principal["partner_id"], "user_id": str(body.user_id),
        "role_key": body.role_key,
        "location_id": str(body.location_id) if body.location_id else None,
        "status": "invited",
    })


@router.get("/networks")
async def list_partner_networks(request: Request, partner_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    filters = {"partner_id": f"eq.{principal['partner_id']}",
        "select": "id,partner_id,location_id,provider_id,name,ssid_label,gateway_type,gateway_network_ref,status,active_verification_method,created_at,updated_at",
        "order": "created_at.desc", "limit": "200"}
    if principal["principal_role"] in {"location_manager", "partner_staff"}:
        if not principal.get("location_id"):
            return []
        filters["location_id"] = f"eq.{principal['location_id']}"
    return await repository(request).select("partner_networks", filters)


@router.post("/networks", status_code=201)
async def create_partner_network(body: PartnerNetworkCreate, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    await _assert_partner_location(request, principal["partner_id"], body.location_id)
    if body.provider_id:
        providers = await repository(request).select("network_providers", {
            "id": f"eq.{body.provider_id}", "status": "eq.active", "select": "id", "limit": "1"})
        if not providers:
            raise HTTPException(422, "Network provider is not active")
    return await repository(request).insert("partner_networks", {
        "partner_id": principal["partner_id"], "location_id": str(body.location_id),
        "provider_id": str(body.provider_id) if body.provider_id else None,
        "name": body.name.strip(), "ssid_label": body.ssid_label,
        "gateway_type": body.gateway_type, "gateway_network_ref": body.gateway_network_ref,
        "status": "pending",
    })


@router.get("/networks/{network_id}/verification-configs")
async def list_network_verification_configs(network_id: UUID, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    networks = await repository(request).select("partner_networks", {
        "id": f"eq.{network_id}", "partner_id": f"eq.{principal['partner_id']}",
        "select": "id,location_id", "limit": "1"})
    if not networks:
        raise HTTPException(404, "Network not found")
    if principal["principal_role"] in {"location_manager", "partner_staff"} and networks[0].get("location_id") != principal.get("location_id"):
        raise HTTPException(403, "Network is outside the assigned location")
    return await repository(request).select("network_verification_configs", {
        "network_id": f"eq.{network_id}",
        "select": "id,network_id,method_key,config_public,secret_reference,enabled,policy,created_at,updated_at",
        "order": "created_at.desc", "limit": "100"})


@router.post("/networks/{network_id}/verification-configs", status_code=201)
async def configure_network_verification(network_id: UUID, body: NetworkVerificationConfigInput,
    request: Request, partner_id: UUID | None = Query(default=None),
    user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    networks = await repository(request).select("partner_networks", {
        "id": f"eq.{network_id}", "partner_id": f"eq.{principal['partner_id']}",
        "select": "id", "limit": "1"})
    if not networks:
        raise HTTPException(404, "Network not found")
    catalog = await repository(request).select("network_verification_method_catalog", {
        "method_key": f"eq.{body.method_key}", "select": "method_key,enabled,adapter_ready,requires_secret",
        "limit": "1"})
    if not catalog or not catalog[0].get("enabled"):
        raise HTTPException(409, "Verification method is not enabled in the platform catalog")
    if body.enabled and not catalog[0].get("adapter_ready"):
        raise HTTPException(409, "Verification adapter is not ready; configuration remains disabled")
    if catalog[0].get("requires_secret") and not body.secret_reference:
        raise HTTPException(422, "A secret vault reference is required")
    repo = repository(request)
    existing = await repo.select("network_verification_configs", {
        "network_id": f"eq.{network_id}", "method_key": f"eq.{body.method_key}",
        "select": "id", "limit": "1"})
    payload = {
        "config_public": body.config_public,
        "secret_reference": body.secret_reference,
        "policy": body.policy,
        "enabled": body.enabled and bool(catalog[0].get("adapter_ready")),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if existing:
        rows = await repo.update("network_verification_configs", {"id": f"eq.{existing[0]['id']}"}, payload)
        if not rows:
            raise HTTPException(409, "Verification configuration update was not applied")
        return rows[0]
    return await repo.insert("network_verification_configs", {
        "network_id": str(network_id), "method_key": body.method_key, **payload})


@router.post("/access-codes", status_code=201)
async def create_partner_access_code(body: PartnerAccessCodeCreate, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    if body.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(422, "Access code expiry must be in the future")
    if body.location_id:
        await _assert_partner_location(request, principal["partner_id"], body.location_id)
    repo = repository(request)
    if body.network_id and not body.location_id:
        raise HTTPException(422, "A location is required when an access code is bound to a network")
    if body.network_id:
        network = await repo.select("partner_networks", {
            "id": f"eq.{body.network_id}", "partner_id": f"eq.{principal['partner_id']}",
            "select": "id,location_id", "limit": "1"})
        if not network:
            raise HTTPException(422, "Network does not belong to the active partner tenant")
        if body.location_id and network[0].get("location_id") != str(body.location_id):
            raise HTTPException(422, "Network and location scopes do not match")
    if body.campaign_id:
        campaign = await repo.select("partner_campaigns", {
            "id": f"eq.{body.campaign_id}", "partner_id": f"eq.{principal['partner_id']}",
            "select": "id,location_id", "limit": "1"})
        if not campaign:
            raise HTTPException(422, "Campaign does not belong to the active partner tenant")
        if body.location_id and campaign[0].get("location_id") not in {None, str(body.location_id)}:
            raise HTTPException(422, "Campaign and location scopes do not match")
    if body.reward_id:
        reward = await repo.select("campaign_rewards", {
            "id": f"eq.{body.reward_id}", "select": "id,campaign_id", "limit": "1"})
        if not reward or (body.campaign_id and reward[0].get("campaign_id") != str(body.campaign_id)):
            raise HTTPException(422, "Reward does not match the selected campaign")
    raw_code = secrets.token_urlsafe(24)
    digest = hashlib.sha256(raw_code.encode("utf-8")).hexdigest()
    row = await repo.insert("partner_access_codes", {
        "partner_id": principal["partner_id"],
        "location_id": str(body.location_id) if body.location_id else None,
        "network_id": str(body.network_id) if body.network_id else None,
        "campaign_id": str(body.campaign_id) if body.campaign_id else None,
        "reward_id": str(body.reward_id) if body.reward_id else None,
        "code_hash": digest, "status": "active",
        "expires_at": body.expires_at.isoformat(),
        "max_redemptions": body.max_redemptions, "created_by": principal["id"],
    })
    return {"access_code": raw_code, "record": row,
        "notice": "The plaintext code is shown once. Store it securely; only its SHA-256 hash is persisted."}


@router.post("/access-codes/{access_code_id}/revoke")
async def revoke_partner_access_code(access_code_id: UUID, request: Request,
    partner_id: UUID | None = Query(default=None), user: dict[str, Any] = Depends(current_user)):
    principal = await require_partner_context(request, user, str(partner_id) if partner_id else None)
    _require_partner_manager(principal)
    rows = await repository(request).update("partner_access_codes", {
        "id": f"eq.{access_code_id}", "partner_id": f"eq.{principal['partner_id']}",
        "status": "eq.active",
    }, {"status": "revoked", "revoked_at": datetime.now(timezone.utc).isoformat()})
    if not rows:
        raise HTTPException(404, "Active access code not found")
    return {"id": rows[0]["id"], "status": rows[0]["status"]}
