from __future__ import annotations

from typing import Any
import os

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from uuid import UUID

from app.authorization import customer_principal
from app.routers.conversations import repository
from engine.tools.catalog import tool_catalog
from engine.llm.router import ModelRouter

class AgentCatalogItemResponse(BaseModel):
    id: UUID
    key: str
    name: str
    description: str | None = None
    version: str
    enabled: bool


class ToolCatalogItemResponse(BaseModel):
    key: str
    version: str
    description: str
    input_schema: dict[str, Any]
    capability_tags: list[str]
    permission_scope: str
    risk: str
    approval_mode: str
    execution_environment: str
    timeout_seconds: int
    resource_limits: dict[str, Any]
    idempotency: str
    audit_category: str
    available_by_default: list[str]
    enabled_by_default: bool


class ModelCapabilityItemResponse(BaseModel):
    provider_key: str
    provider_name: str
    model_key: str
    model_name: str
    capabilities: list[str]
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None


class ModelCapabilityListResponse(BaseModel):
    items: list[ModelCapabilityItemResponse]
    count: int
    source: str


router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/agents", response_model=list[AgentCatalogItemResponse])
async def list_agents(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    rows = await repository(request).select("agent_definitions", {
        "enabled": "eq.true", "select": "id,key,name,description,version,enabled",
        "order": "display_name.asc", "limit": "200",
    })
    # Do not advertise DB definitions that have no registered production runtime.
    supported = {"manus", "planning", "toolcall"}
    sandbox_image = os.getenv("MOREAI_SANDBOX_IMAGE", "")
    if (
        os.getenv("MOREAI_SANDBOX_ENABLED", "false").lower() == "true"
        and os.getenv("MOREAI_SANDBOX_RELEASE_GATE_PASSED", "false").lower() == "true"
        and "@sha256:" in sandbox_image
    ):
        supported.add("swe")
    return [row for row in rows if str(row.get("key", "")).lower() in supported]


@router.get("/models/capabilities", response_model=ModelCapabilityListResponse)
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


@router.get("/tools", response_model=list[ToolCatalogItemResponse])
async def list_tools(user: dict[str, Any] = Depends(current_user)):
    # The catalog describes upstream tools; availability remains false until a safe adapter is enabled.
    return tool_catalog()
