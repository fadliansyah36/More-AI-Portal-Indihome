from __future__ import annotations

import json
import math
import os
from typing import Any

from app.client import WorkerRpcClient
from engine.llm.router import CreditEstimate, ResolvedModelRoute


class ConfiguredCreditEstimator:
    """Requires explicit business-approved USD-to-credit and output-token configuration."""

    def _credits_per_usd(self) -> float:
        raw = os.getenv("MOREAI_CREDITS_PER_USD")
        if not raw:
            raise RuntimeError("credit_conversion_not_configured")
        value = float(raw)
        if not math.isfinite(value) or value <= 0:
            raise RuntimeError("invalid_credit_conversion")
        return value

    async def estimate(self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]]) -> CreditEstimate:
        if not route.max_output_tokens or route.max_output_tokens < 1:
            raise RuntimeError("model_output_limit_not_configured")
        encoded = json.dumps(messages, ensure_ascii=False, separators=(",", ":"))
        input_tokens = max(1, math.ceil(len(encoded) / 3))
        if route.max_input_tokens and input_tokens > route.max_input_tokens:
            raise RuntimeError("prompt_exceeds_model_input_limit")
        estimated_cost = (
            input_tokens * route.input_cost_per_million
            + route.max_output_tokens * route.output_cost_per_million
        ) / 1_000_000
        credits = estimated_cost * self._credits_per_usd()
        if credits <= 0:
            raise RuntimeError("estimated_credit_reservation_is_zero")
        return CreditEstimate(estimated_cost=estimated_cost, estimated_credits=credits)

    async def actual_credits(self, *, route: ResolvedModelRoute, result: dict[str, Any]) -> float:
        actual_cost = float(result.get("actual_cost") or 0)
        credits = actual_cost * self._credits_per_usd()
        if not math.isfinite(credits) or credits < 0:
            raise RuntimeError("invalid_actual_credit_amount")
        return credits


class SupabaseUsageAccounting:
    """Implements MoreAI's idempotent LLM request, entitlement, quota and credit lifecycle."""

    def __init__(self, client: WorkerRpcClient):
        self.client = client

    async def claim_request(self, *, user_id: str, run_id: str, request_key: str, request_hash: str) -> dict[str, Any]:
        result = await self.client.rpc("moreai_llm_claim_request", {
            "p_user_id": user_id,
            "p_run_id": run_id,
            "p_idempotency_key": request_key,
            "p_request_hash": request_hash,
        })
        if not isinstance(result, dict) or not result.get("id"):
            raise RuntimeError("llm_request_claim_failed")
        return result

    async def reserve(
        self, *, request_id: str, user_id: str, run_id: str, request_key: str,
        estimated_credits: float, estimated_cost: float,
        workspace_id: str | None, partner_id: str | None,
        entitlement_key: str | None = None,
        quota_metric_key: str | None = None,
    ) -> str:
        currency = os.getenv("MOREAI_CREDIT_WALLET_CURRENCY")
        entitlement_key = entitlement_key or os.getenv("MOREAI_LLM_ENTITLEMENT_KEY")
        quota_metric_key = quota_metric_key or os.getenv("MOREAI_LLM_QUOTA_METRIC_KEY")
        if not currency or not entitlement_key or not quota_metric_key:
            raise RuntimeError("wallet_entitlement_and_quota_policy_must_be_configured")
        wallets = await self.client.select("wallet_accounts", {
            "owner_type": "eq.user",
            "owner_id": f"eq.{user_id}",
            "currency": f"eq.{currency}",
            "status": "eq.active",
            "select": "id,balance,currency",
            "order": "created_at.asc",
            "limit": "2",
        })
        if len(wallets) != 1:
            raise RuntimeError("user_credit_wallet_missing_or_ambiguous")
        reservation = await self.client.rpc("moreai_llm_reserve_request", {
            "p_request_id": request_id,
            "p_user_id": user_id,
            "p_run_id": run_id,
            "p_wallet_id": wallets[0]["id"],
            "p_credit_amount": estimated_credits,
            "p_estimated_cost": estimated_cost,
            "p_reservation_key": f"{request_key}:reserve",
            "p_entitlement_key": entitlement_key,
            "p_quota_metric_key": quota_metric_key,
            "p_quota_amount": estimated_credits,
            "p_workspace_id": workspace_id,
            "p_partner_id": partner_id,
        })
        if not isinstance(reservation, dict) or not reservation.get("reservation_id"):
            raise RuntimeError("atomic_llm_quota_credit_reservation_failed")
        return str(reservation["reservation_id"])

    async def record_provider_result(self, *, request_id: str, result: dict[str, Any], latency_ms: int) -> None:
        await self.client.rpc("moreai_llm_mark_provider_result", {
            "p_request_id": request_id,
            "p_provider_key": result["provider_key"],
            "p_model_key": result["model_key"],
            "p_response_text": result["text"],
            "p_input_tokens": int(result["input_tokens"]),
            "p_output_tokens": int(result["output_tokens"]),
            "p_actual_cost": float(result["actual_cost"]),
            "p_latency_ms": max(0, latency_ms),
            "p_provider_response_id": result.get("provider_response_id"),
        })

    async def finalize(self, *, request_id: str, actual_credits: float, request_key: str, provider_response_id: str | None) -> None:
        await self.client.rpc("moreai_llm_finalize_request", {
            "p_request_id": request_id,
            "p_actual_credits": actual_credits,
            "p_settlement_key": request_key,
            "p_provider_response_id": provider_response_id,
        })

    async def fail(self, *, request_id: str, error_code: str, release_reservation: bool, request_key: str) -> None:
        await self.client.rpc("moreai_llm_fail_request", {
            "p_request_id": request_id,
            "p_error_code": error_code[:120],
            "p_release": release_reservation,
            "p_release_key": request_key,
        })
