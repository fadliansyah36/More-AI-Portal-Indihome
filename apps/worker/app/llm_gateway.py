from __future__ import annotations

from typing import Any

from app.client import WorkerRpcClient
from app.llm_accounting import ConfiguredCreditEstimator, SupabaseUsageAccounting
from engine.llm.providers.openai_compatible import OpenAICompatibleAdapter
from engine.llm.router import MeteredGateway, ModelRouter


class SupabaseRouteRepository:
    """Loads enabled model routes from MoreAI policy tables, scoped to the current principal."""

    def __init__(self, client: WorkerRpcClient):
        self.client = client

    async def list_enabled_routes(self, task_type: str, *, user_id: str | None, workspace_id: str | None, partner_id: str | None) -> list[dict[str, Any]]:
        scopes: list[tuple[str, str | None]] = [
            ("platform", None),\n            ("global", None),
            ("user", user_id),
            ("workspace", workspace_id),
            ("partner", partner_id),
        ]
        rows: list[dict[str, Any]] = []
        for scope_type, scope_id in scopes:
            if scope_type != "platform" and not scope_id:
                continue
            params = {
                "scope_type": f"eq.{scope_type}",
                "task_type": f"eq.{task_type}",
                "enabled": "eq.true",
                "select": "id,scope_type,scope_id,task_type,model_id,fallback_model_id,priority,enabled",
                "order": "priority.desc",
                "limit": "100",
            }
            params["scope_id"] = "is.null" if scope_id is None else f"eq.{scope_id}"
            rows.extend(await self.client.select("llm_routing_policies", params))
        specificity = {"platform": 0, "partner": 1, "user": 2, "workspace": 3}
        return sorted(rows, key=lambda row: (int(row.get("priority") or 0), specificity.get(row.get("scope_type"), 0)), reverse=True)

    async def get_enabled_model(self, model_id: str) -> dict[str, Any] | None:
        rows = await self.client.select("llm_models", {
            "id": f"eq.{model_id}", "enabled": "eq.true",
            "select": "id,provider_id,key,display_name,input_cost_per_million,output_cost_per_million,max_input_tokens,max_output_tokens,capabilities",
            "limit": "1",
        })
        return rows[0] if rows else None

    async def get_enabled_provider(self, provider_id: str) -> dict[str, Any] | None:
        rows = await self.client.select("llm_providers", {
            "id": f"eq.{provider_id}", "enabled": "eq.true",
            "select": "id,key,display_name,config", "limit": "1",
        })
        return rows[0] if rows else None


def create_metered_gateway(client: WorkerRpcClient, http_client: Any) -> MeteredGateway:
    repository = SupabaseRouteRepository(client)
    return MeteredGateway(
        router=ModelRouter(repository),
        estimator=ConfiguredCreditEstimator(),
        accounting=SupabaseUsageAccounting(client),
        adapter=OpenAICompatibleAdapter(http_client),
    )
