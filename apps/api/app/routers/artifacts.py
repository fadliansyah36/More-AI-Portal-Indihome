from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.dependencies import current_user
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])


@router.get("")
async def list_artifacts(request: Request, user: dict[str, Any] = Depends(current_user)):
    """Return only artifact metadata owned by the authenticated principal."""
    return await repository(request).select("artifacts", {
        "user_id": f"eq.{user['id']}",
        "select": "id,storage_path,mime_type,size_bytes,checksum_sha256,metadata,created_at",
        "order": "created_at.desc",
        "limit": "200",
    })
