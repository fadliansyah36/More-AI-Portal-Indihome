from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RouteRepository(Protocol):
    async def list_enabled_routes(self, task_type: str) -> list[dict[str, Any]]: ...
    async def get_enabled_model(self, model_id: str) -> dict[str, Any] | None: ...
    async def get_enabled_provider(self, provider_id: str) -> dict[str, Any] | None: ...


class NoEligibleModelRoute(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedModelRoute:
    provider_key: str
    model_key: str
    display_name: str
    base_url: str
    secret_env_name: str
    input_cost_per_million: float
    output_cost_per_million: float
    max_input_tokens: int | None
    max_output_tokens: int | None
    capabilities: tuple[str, ...]


class ModelRouter:
    """Resolve routes from MoreAI's canonical model/provider policy tables."""

    def __init__(self, repository: RouteRepository):
        self.repository = repository

    async def resolve(self, task_type: str, required_capabilities: set[str] | None = None) -> ResolvedModelRoute:
        required = required_capabilities or set()
        routes = await self.repository.list_enabled_routes(task_type)
        for route in routes:
            model = await self.repository.get_enabled_model(str(route["model_id"]))
            if not model:
                continue
            capabilities = set(model.get("capabilities") or [])
            if not required.issubset(capabilities):
                continue
            provider = await self.repository.get_enabled_provider(str(model["provider_id"]))
            if not provider:
                continue
            config = provider.get("config") or {}
            base_url = config.get("base_url")
            secret_env_name = config.get("secret_env_name")
            if not isinstance(base_url, str) or not base_url.startswith("https://"):
                continue
            if not isinstance(secret_env_name, str) or not secret_env_name.startswith("MOREAI_PROVIDER_"):
                continue
            return ResolvedModelRoute(
                provider_key=provider["key"],
                model_key=model["key"],
                display_name=model["display_name"],
                base_url=base_url.rstrip("/"),
                secret_env_name=secret_env_name,
                input_cost_per_million=float(model["input_cost_per_million"]),
                output_cost_per_million=float(model["output_cost_per_million"]),
                max_input_tokens=model.get("max_input_tokens"),
                max_output_tokens=model.get("max_output_tokens"),
                capabilities=tuple(sorted(capabilities)),
            )
        raise NoEligibleModelRoute(f"No enabled model route for task type: {task_type}")


class UsageAccounting(Protocol):
    async def reserve(self, *, user_id: str, run_id: str, request_key: str, estimated_cost: float) -> str: ...
    async def settle(self, *, reservation_id: str, actual_cost: float, request_key: str) -> None: ...
    async def release(self, *, reservation_id: str, request_key: str) -> None: ...


class MeteredGateway:
    """No provider call is allowed without an explicit credit/usage accounting adapter."""

    def __init__(self, *, router: ModelRouter, accounting: UsageAccounting, adapter: Any):
        self.router = router
        self.accounting = accounting
        self.adapter = adapter

    async def complete(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "chat") -> dict[str, Any]:
        route = await self.router.resolve(task_type)
        # Accounting must reserve before the external provider is called.
        reservation_id = await self.accounting.reserve(user_id=user_id, run_id=run_id, request_key=request_key, estimated_cost=0.0)
        try:
            result = await self.adapter.complete(route=route, messages=messages)
            await self.accounting.settle(reservation_id=reservation_id, actual_cost=result["actual_cost"], request_key=f"{request_key}:settle")
            return result
        except Exception:
            await self.accounting.release(reservation_id=reservation_id, request_key=f"{request_key}:release")
            raise
