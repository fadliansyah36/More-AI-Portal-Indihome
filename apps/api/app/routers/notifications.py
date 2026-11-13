from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.dependencies import current_user
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: UUID
    notification_type: str
    title: str
    body: str
    resource_type: str | None
    resource_id: UUID | str | None
    action_url: str | None
    metadata: dict[str, Any]
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    limit: int


class NotificationPreferencesResponse(BaseModel):
    in_app_enabled: bool
    email_enabled: bool
    category_settings: dict[str, bool]
    updated_at: datetime | None


class NotificationReadResponse(BaseModel):
    id: UUID
    read_at: datetime


class NotificationReadAllResponse(BaseModel):
    updated: int


class NotificationPreferencesUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    category_settings: dict[str, bool] | None = Field(default=None, max_length=100)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    request: Request,
    unread_only: bool = False,
    limit: int = Query(default=30, ge=1, le=100),
    user: dict[str, Any] = Depends(current_user),
):
    filters = {
        "user_id": f"eq.{user['id']}",
        "select": "id,notification_type,title,body,resource_type,resource_id,action_url,metadata,read_at,created_at",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if unread_only:
        filters["read_at"] = "is.null"
    rows = await repository(request).select("notifications", filters)
    return {"items": rows, "limit": limit}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    rows = await repository(request).select("notification_preferences", {
        "user_id": f"eq.{user['id']}",
        "select": "in_app_enabled,email_enabled,category_settings,updated_at",
        "limit": "1",
    })
    return rows[0] if rows else {
        "in_app_enabled": True, "email_enabled": False, "category_settings": {},
        "updated_at": None,
    }


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    body: NotificationPreferencesUpdate,
    request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    changes = body.model_dump(exclude_unset=True)
    if not changes:
        return await get_notification_preferences(request, user)
    changes["user_id"] = user["id"]
    changes["updated_at"] = datetime.now(timezone.utc).isoformat()
    settings = request.app.state.settings
    response = await request.app.state.http.post(
        f"{settings.supabase_url.rstrip('/')}/rest/v1/notification_preferences",
        params={"on_conflict": "user_id", "select": "in_app_enabled,email_enabled,category_settings,updated_at"},
        json=changes,
        headers={
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
        },
        timeout=10.0,
    )
    if response.status_code >= 500:
        raise HTTPException(503, "Notification preference service unavailable")
    if response.status_code >= 400:
        raise HTTPException(422, "Notification preference update was rejected")
    rows = response.json()
    return rows[0] if rows else await get_notification_preferences(request, user)


@router.post("/{notification_id}/read", response_model=NotificationReadResponse)
async def mark_notification_read(
    notification_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(current_user),
):
    rows = await repository(request).update(
        "notifications",
        {"id": f"eq.{notification_id}", "user_id": f"eq.{user['id']}", "select": "id,read_at"},
        {"read_at": datetime.now(timezone.utc).isoformat()},
    )
    if not rows:
        raise HTTPException(404, "Notification not found")
    return rows[0]


@router.post("/read-all", response_model=NotificationReadAllResponse)
async def mark_all_notifications_read(
    request: Request, user: dict[str, Any] = Depends(current_user),
):
    rows = await repository(request).update(
        "notifications",
        {"user_id": f"eq.{user['id']}", "read_at": "is.null", "select": "id"},
        {"read_at": datetime.now(timezone.utc).isoformat()},
    )
    return {"updated": len(rows)}
