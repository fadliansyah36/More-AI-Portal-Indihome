from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.dependencies import current_user
from app.routers.conversations import repository
from engine.tools.catalog import tool_catalog

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/agents")
async def list_agents(request: Request, user: dict[str, Any] = Depends(current_user)):
    rows = await repository(request).select("agent_definitions", {
        "enabled": "eq.true", "select": "id,key,display_name,description,version,capabilities",
        "order": "display_name.asc", "limit": "200",
    })
    return rows


@router.get("/tools")
async def list_tools(user: dict[str, Any] = Depends(current_user)):
    # The catalog describes upstream tools; availability remains false until a safe adapter is enabled.
    return tool_catalog()
