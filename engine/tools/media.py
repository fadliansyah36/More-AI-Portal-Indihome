from __future__ import annotations

import hashlib
import json
import math
import os
import time
from typing import Any

import httpx

from engine.llm.router import ResolvedModelRoute


class OpenAIImageGenerationAdapter:
    """Metered OpenAI Images API adapter; registered only when every billing/secret gate is set."""

    MIME_TYPES = {
        "png": "image/png",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }

    def __init__(self, *, http: httpx.AsyncClient, artifacts: Any, accounting: Any, estimator: Any):
        self.http = http
        self.artifacts = artifacts
        self.accounting = accounting
        self.estimator = estimator

    @classmethod
    def from_environment(cls, *, http: httpx.AsyncClient, artifacts: Any, accounting: Any, estimator: Any):
        required = (
            "OPENAI_API_KEY",
            "MOREAI_MEDIA_ENTITLEMENT_KEY",
            "MOREAI_MEDIA_QUOTA_METRIC_KEY",
            "MOREAI_CREDIT_WALLET_CURRENCY",
            "MOREAI_CREDITS_PER_USD",
            "MOREAI_OPENAI_IMAGE_COSTS_JSON",
        )
        if os.getenv("MOREAI_MEDIA_BILLING_ENABLED", "false").lower() != "true":
            return None
        if any(not os.getenv(key) for key in required):
            return None
        try:
            costs = json.loads(os.environ["MOREAI_OPENAI_IMAGE_COSTS_JSON"])
            if not isinstance(costs, dict) or not costs:
                return None
            normalized_costs = {
                str(key): float(value)
                for key, value in costs.items()
                if isinstance(key, str) and isinstance(value, (int, float)) and not isinstance(value, bool)
            }
            if len(normalized_costs) != len(costs) or any(not math.isfinite(value) or value <= 0 for value in normalized_costs.values()):
                return None
            credits_per_usd = float(os.environ["MOREAI_CREDITS_PER_USD"])
            timeout_seconds = float(os.getenv("MOREAI_IMAGE_PROVIDER_TIMEOUT_SECONDS", "600"))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        if not math.isfinite(credits_per_usd) or credits_per_usd <= 0 or not 1 <= timeout_seconds <= 600:
            return None
        return cls(http=http, artifacts=artifacts, accounting=accounting, estimator=estimator)

    def _route(self, model: str, image_cost: float) -> ResolvedModelRoute:
        # The existing usage ledger is reused for atomic wallet/quota reservation.
        # One synthetic output unit represents the configured per-image USD cost;
        # token counters recorded for this media request remain zero.
        return ResolvedModelRoute(
            provider_key="openai",
            model_key=model,
            display_name=model,
            base_url="https://api.openai.com/v1",
            secret_env_name="OPENAI_API_KEY",
            input_cost_per_million=0.0,
            output_cost_per_million=image_cost * 1_000_000,
            max_input_tokens=32000,
            max_output_tokens=1,
            capabilities=("image_generation",),
        )

    def _image_cost(self, size: str, quality: str) -> float:
        costs = json.loads(os.environ["MOREAI_OPENAI_IMAGE_COSTS_JSON"])
        keys = [f"{size}:{quality}"]
        if size == "auto" and quality != "auto":
            keys.append(f"auto:{quality}")
        if quality == "auto" and size != "auto":
            keys.append(f"{size}:auto")
        if size == "auto" and quality == "auto":
            keys.append("auto:auto")
        for key in keys:
            value = costs.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cost = float(value)
                if math.isfinite(cost) and cost > 0:
                    return cost
        raise RuntimeError("image_price_not_configured_for_size_and_quality")

    async def image_generate(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        prompt = arguments.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
            raise ValueError("image_prompt_invalid")
        model = os.getenv("MOREAI_OPENAI_IMAGE_MODEL", "gpt-image-2")
        output_format = arguments.get("output_format", "png")
        if output_format not in self.MIME_TYPES:
            raise ValueError("image_output_format_not_supported")
        size = arguments.get("size", "1024x1024")
        quality = arguments.get("quality", "medium")
        background = arguments.get("background", "auto")
        if size not in {"auto", "1024x1024", "1536x1024", "1024x1536"}:
            raise ValueError("image_size_not_supported")
        if quality not in {"low", "medium", "high", "auto"}:
            raise ValueError("image_quality_not_supported")
        if background not in {"auto", "opaque"}:
            raise ValueError("image_background_not_supported")

        image_cost = self._image_cost(size, quality)
        route = self._route(model, image_cost)
        request_payload = {
            "model": model,
            "prompt": prompt.strip(),
            "size": size,
            "quality": quality,
            "background": background,
            "output_format": output_format,
        }
        request_hash = hashlib.sha256(
            json.dumps(request_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        request_key = f"{run_id}:image_generate:{request_hash[:32]}"
        claim = await self.accounting.claim_request(
            user_id=user_id, run_id=run_id, request_key=request_key, request_hash=request_hash,
        )
        if not claim.get("created"):
            if claim.get("status") == "succeeded" and isinstance(claim.get("response_text"), str):
                return claim["response_text"]
            raise RuntimeError("image_generation_request_already_claimed")

        reservation_id: str | None = None
        provider_succeeded = False
        provider_outcome_unknown = False
        request_id = str(claim["id"])
        try:
            estimate = await self.estimator.estimate(
                route=route,
                messages=[{"role": "user", "content": prompt.strip()}],
            )
            reservation_id = await self.accounting.reserve(
                request_id=request_id,
                user_id=user_id,
                run_id=run_id,
                request_key=request_key,
                estimated_credits=estimate.estimated_credits,
                estimated_cost=estimate.estimated_cost,
                workspace_id=None,
                partner_id=None,
                entitlement_key=os.environ["MOREAI_MEDIA_ENTITLEMENT_KEY"],
                quota_metric_key=os.environ["MOREAI_MEDIA_QUOTA_METRIC_KEY"],
            )
            started = time.monotonic()
            try:
                response = await self.http.post(
                    "https://api.openai.com/v1/images/generations",
                    json={
                        **request_payload,
                        "n": 1,
                     },
                    headers={
                        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
                        "Content-Type": "application/json",
                        "Idempotency-Key": request_key,
                    },
                    timeout=float(os.getenv("MOREAI_IMAGE_PROVIDER_TIMEOUT_SECONDS", "600")),
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                provider_outcome_unknown = True
                raise RuntimeError("image_provider_outcome_unknown_reservation_retained") from exc
            if response.status_code in {408, 425} or response.status_code >= 500:
                provider_outcome_unknown = True
                raise RuntimeError("image_provider_outcome_unknown_reservation_retained")
            response.raise_for_status()
            provider_succeeded = True
            payload = response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list) or not data or not isinstance(data[0], dict):
                raise RuntimeError("image_provider_returned_no_image")
            image_base64 = data[0].get("b64_json")
            if not isinstance(image_base64, str):
                raise RuntimeError("image_provider_binary_missing")
            # Image API pricing is per generated image/quality/size, so settlement
            # uses the explicitly configured price map rather than assuming token
            # usage fields that the Images API response does not promise.
            input_tokens = 0
            output_tokens = 0
            actual_cost = image_cost

            extension = "jpg" if output_format == "jpeg" else output_format
            filename = f"moreai-image-{run_id[:8]}.{extension}"
            artifact_json = await self.artifacts.binary_saver({
                "path": filename,
                "content_base64": image_base64,
                "mime_type": self.MIME_TYPES[output_format],
                "metadata": {"provider": "openai", "model": model, "media_type": "image"},
            }, run_id=run_id, user_id=user_id)
            artifact = json.loads(artifact_json)
            result_text = json.dumps({
                "status": "generated",
                "provider": "openai",
                "model": model,
                "artifact": artifact,
            }, ensure_ascii=False, separators=(",", ":"))
            provider_result = {
                "text": result_text,
                "provider_key": "openai",
                "model_key": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "actual_cost": actual_cost,
                "provider_response_id": payload.get("id") or response.headers.get("x-request-id"),
            }
            await self.accounting.record_provider_result(
                request_id=request_id,
                result=provider_result,
                latency_ms=max(0, int((time.monotonic() - started) * 1000)),
            )
            actual_credits = await self.estimator.actual_credits(route=route, result=provider_result)
            await self.accounting.finalize(
                request_id=request_id,
                actual_credits=actual_credits,
                request_key=f"{request_key}:settle",
                provider_response_id=provider_result["provider_response_id"],
            )
            return result_text
        except Exception as exc:
            await self.accounting.fail(
                request_id=request_id,
                error_code="image_generation_failed",
                release_reservation=reservation_id is not None and not provider_succeeded and not provider_outcome_unknown,
                request_key=f"{request_key}:release",
            )
            raise
