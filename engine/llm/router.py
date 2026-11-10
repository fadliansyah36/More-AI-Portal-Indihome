from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class RouteRepository(Protocol):
    async def list_enabled_routes(self, task_type: str, *, user_id: str | None, workspace_id: str | None, partner_id: str | None) -> list[dict[str, Any]]: ...
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


@dataclass(frozen=True)
class CreditEstimate:
    estimated_cost: float
    estimated_credits: float


class ModelRouter:
    """Resolve routes from MoreAI's canonical model/provider policy tables."""

    def __init__(self, repository: RouteRepository):
        self.repository = repository

    async def resolve(self, task_type: str, required_capabilities: set[str] | None = None, *, user_id: str | None = None, workspace_id: str | None = None, partner_id: str | None = None) -> ResolvedModelRoute:
        required = required_capabilities or set()
        routes = await self.repository.list_enabled_routes(task_type, user_id=user_id, workspace_id=workspace_id, partner_id=partner_id)
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


class CreditEstimator(Protocol):
    async def estimate(self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]]) -> CreditEstimate: ...
    async def actual_credits(self, *, route: ResolvedModelRoute, result: dict[str, Any]) -> float: ...


class UsageAccounting(Protocol):
    async def claim_request(self, *, user_id: str, run_id: str, request_key: str, request_hash: str) -> dict[str, Any]: ...
    async def reserve(self, *, request_id: str, user_id: str, run_id: str, request_key: str, estimated_credits: float, estimated_cost: float) -> str: ...
    async def record_provider_result(self, *, request_id: str, result: dict[str, Any], latency_ms: int) -> None: ...
    async def finalize(self, *, request_id: str, actual_credits: float, request_key: str, provider_response_id: str | None) -> None: ...
    async def fail(self, *, request_id: str, error_code: str, release_reservation: bool, request_key: str) -> None: ...


class MeteredGateway:
    """Provider calls require an idempotent request claim and a credit reservation before network I/O."""

    def __init__(self, *, router: ModelRouter, estimator: CreditEstimator, accounting: UsageAccounting, adapter: Any):
        self.router = router
        self.estimator = estimator
        self.accounting = accounting
        self.adapter = adapter

    async def complete(self, *, user_id: str, run_id: str, request_key: str, messages: list[dict[str, Any]], task_type: str = "chat", workspace_id: str | None = None, partner_id: str | None = None) -> dict[str, Any]:
        import hashlib
        import json
        import time

        route = await self.router.resolve(task_type, user_id=user_id, workspace_id=workspace_id, partner_id=partner_id)
        request_hash = hashlib.sha256(json.dumps(messages, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        claim = await self.accounting.claim_request(user_id=user_id, run_id=run_id, request_key=request_key, request_hash=request_hash)
        if not claim.get("created"):
            if claim.get("status") == "succeeded" and isinstance(claim.get("response_text"), str):
                return {"text": claim["response_text"], "provider_key": claim.get("provider_key"), "model_key": claim.get("model_key"), "cached": True}
            raise RuntimeError("llm_request_already_in_progress")
        reservation_id: str | None = None
        try:
            estimate = await self.estimator.estimate(route=route, messages=messages)
            reservation_id = await self.accounting.reserve(
                request_id=str(claim["id"]), user_id=user_id, run_id=run_id, request_key=request_key,
                estimated_credits=estimate.estimated_credits, estimated_cost=estimate.estimated_cost,
            )
            started = time.monotonic()
            result = await self.adapter.complete(route=route, messages=messages)
            latency_ms = int((time.monotonic() - started) * 1000)
            await self.accounting.record_provider_result(request_id=str(claim["id"]), result=result, latency_ms=latency_ms)
            actual_credits = await self.estimator.actual_credits(route=route, result=result)
            await self.accounting.finalize(
                request_id=str(claim["id"]), actual_credits=actual_credits,
                request_key=f"{request_key}:settle", provider_response_id=result.get("provider_response_id"),
            )
            return result
        except Exception:
            await self.accounting.fail(
                request_id=str(claim["id"]), error_code="provider_execution_failed",
                release_reservation=reservation_id is not None, request_key=f"{request_key}:release",
            )
            raise
