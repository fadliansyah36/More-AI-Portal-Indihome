from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.dependencies import current_user
from app.routers.conversations import repository
from engine.tools.catalog import tool_catalog
from engine.llm.router import ModelRouter

router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/agents")
async def list_agents(request: Request, user: dict[str, Any] = Depends(current_user)):
    rows = await repository(request).select("agent_definitions", {
        "enabled": "eq.true", "select": "id,key,name,description,version,enabled",
        "order": "display_name.asc", "limit": "200",
    })
    # Do not advertise DB definitions that have no registered production runtime.
    supported = {"manus", "planning"}
    return [row for row in rows if str(row.get("key", "")).lower() in supported]


@router.get("/models/capabilities")
async def list_model_capabilities(request: Request, user: dict[str, Any] = Depends(current_user)):
    """Expose only enabled provider/model capabilities; never return provider secrets/config."""
    repo = repository(request)
    providers = await repo.select("llm_providers", {
        "enabled": "eq.true",
        "select": "id,key,display_name",
        "order": "display_name.asc",
        "limit": "200",
    })
    provider_by_id = {str(row["id"]): row for row in providers if row.get("id")}
    models = await repo.select("llm_models", {
        "enabled": "eq.true",
        "select": "id,provider_id,key,display_name,capabilities,max_input_tokens,max_output_tokens",
        "order": "display_name.asc",
        "limit": "500",
    })
    items = []
    for model in models:
        provider = provider_by_id.get(str(model.get("provider_id")))
        if not provider:
            continue
        items.append({
            "provider_key": provider.get("key"),
            "provider_name": provider.get("display_name"),
            "model_key": model.get("key"),
            "model_name": model.get("display_name"),
            "capabilities": sorted(ModelRouter.normalize_capabilities(model.get("capabilities"))),
            "max_input_tokens": model.get("max_input_tokens"),
            "max_output_tokens": model.get("max_output_tokens"),
        })
    return {"items": items, "count": len(items), "source": "enabled_provider_model_registry"}


@router.get("/tools")
async def list_tools(user: dict[str, Any] = Depends(current_user)):
    # The catalog describes upstream tools; availability remains false until a safe adapter is enabled.
    return tool_catalog()
