from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.authorization import customer_principal
from app.routers.conversations import repository
from engine.tools.catalog import tool_catalog
from engine.llm.router import ModelRouter

class AgentCatalogItemResponse(BaseModel):
    id: str
    key: str
    name: str
    description: str | None = None
    version: str
    enabled: bool
    capability_tags: list[str]
    tool_keys: list[str]
    runtime_available: bool
    active_workers: int
    live_tool_keys: list[str]
    last_seen_at: datetime | None = None


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
    # The code-registered runtimes are the source of executable agents. Database
    # definitions may customize their customer-facing name/description or disable
    # a runtime, but an empty definitions table must not make Agent Studio empty.
    configured_rows = await repository(request).select("agent_definitions", {
        "select": "id,key,name,description,version,enabled",
        "order": "name.asc", "limit": "200",
    })
    configured = {str(row.get("key", "")).lower(): row for row in configured_rows}
    runtime_descriptors = {
        "manus": ("Manus", "General-purpose OpenManus agent for chat, research, and tool-assisted work."),
        "planning": ("Planning Agent", "Creates durable multi-step plans and coordinates dependency-aware execution."),
        "toolcall": ("ToolCall Agent", "Executes registered OpenManus tools through policy and approval controls."),
    }
    tools = tool_catalog()
    heartbeat_cutoff = (datetime.now(timezone.utc) - timedelta(seconds=90)).isoformat()
    worker_snapshots = await repository(request).select("moreai_worker_capability_snapshots", {
        "last_seen_at": f"gt.{heartbeat_cutoff}",
        "select": "worker_id,runtime_keys,capabilities,status,last_seen_at",
        "order": "last_seen_at.desc",
        "limit": "100",
    })
    runtime_workers: dict[str, list[dict[str, Any]]] = {}
    for snapshot in worker_snapshots:
        runtime_keys = snapshot.get("runtime_keys") if isinstance(snapshot.get("runtime_keys"), list) else []
        for runtime_key in runtime_keys:
            if isinstance(runtime_key, str):
                runtime_workers.setdefault(runtime_key, []).append(snapshot)
    items: list[dict[str, Any]] = []
    for key, (default_name, default_description) in runtime_descriptors.items():
        definition = configured.get(key)
        if definition is not None and not bool(definition.get("enabled")):
            continue
        mapped_tools = [
            tool for tool in tools
            if key in tool.get("available_by_default", []) and bool(tool.get("enabled_by_default"))
        ]
        capability_tags = sorted({
            str(tag) for tool in mapped_tools for tag in tool.get("capability_tags", [])
        })
        active = runtime_workers.get(key, [])
        live_tool_keys: set[str] = set()
        for snapshot in active:
            snapshot_capabilities = snapshot.get("capabilities") if isinstance(snapshot.get("capabilities"), dict) else {}
            runtimes = snapshot_capabilities.get("runtimes") if isinstance(snapshot_capabilities.get("runtimes"), dict) else {}
            runtime_capability = runtimes.get(key) if isinstance(runtimes.get(key), dict) else {}
            keys = runtime_capability.get("tool_keys") if isinstance(runtime_capability.get("tool_keys"), list) else []
            live_tool_keys.update(item for item in keys if isinstance(item, str))
        last_seen = max(
            (row.get("last_seen_at") for row in active if isinstance(row.get("last_seen_at"), str)),
            default=None,
        )
        items.append({
            "id": str(definition.get("id")) if definition and definition.get("id") else key,
            "key": key,
            "name": str(definition.get("name") or default_name) if definition else default_name,
            "description": str(definition.get("description") or default_description) if definition else default_description,
            "version": str(definition.get("version") or "1") if definition else "1.0.0",
            "enabled": True,
            "capability_tags": capability_tags,
            "tool_keys": [str(tool["key"]) for tool in mapped_tools],
            "runtime_available": bool(active),
            "active_workers": len({str(row.get("worker_id")) for row in active}),
            "live_tool_keys": sorted(live_tool_keys),
            "last_seen_at": last_seen,
        })
    return items


@router.get("/models/capabilities", response_model=ModelCapabilityListResponse)
async def list_model_capabilities(request: Request, user: dict[str, Any] = Depends(customer_principal)):
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
async def list_tools(user: dict[str, Any] = Depends(customer_principal)):
    # The catalog describes upstream tools; availability remains false until a safe adapter is enabled.
    return tool_catalog()
