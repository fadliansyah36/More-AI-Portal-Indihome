from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import time
from typing import Any
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, uuid5

import httpx

from engine.llm.router import ResolvedModelRoute


class RunwayVideoGenerationAdapter:
    """Durable, metered Runway Dev text-to-video adapter with task-id checkpoint recovery."""

    API_BASE = "https://api.dev.runwayml.com/v1"
    API_VERSION = "2024-11-06"
    SUPPORTED_MODELS = {"gen4.5"}


    def __init__(self, *, http: httpx.AsyncClient, client: Any, artifacts: Any, accounting: Any, estimator: Any):
        self.http = http
        self.client = client
        self.artifacts = artifacts
        self.accounting = accounting
        self.estimator = estimator

    @classmethod
    def from_environment(cls, *, http: httpx.AsyncClient, client: Any, artifacts: Any, accounting: Any, estimator: Any):
        required = (
            "RUNWAYML_API_SECRET",
            "MOREAI_MEDIA_ENTITLEMENT_KEY",
            "MOREAI_MEDIA_QUOTA_METRIC_KEY",
            "MOREAI_CREDIT_WALLET_CURRENCY",
            "MOREAI_CREDITS_PER_USD",
            "MOREAI_RUNWAY_VIDEO_COSTS_JSON",
            "MOREAI_RUNWAY_CREDIT_USD",
            "MOREAI_RUNWAY_OUTPUT_HOST_SUFFIXES",
        )
        if os.getenv("MOREAI_MEDIA_BILLING_ENABLED", "false").lower() != "true":
            return None
        if any(not os.getenv(key) for key in required):
            return None
        try:
            costs = json.loads(os.environ["MOREAI_RUNWAY_VIDEO_COSTS_JSON"])
            if not isinstance(costs, dict) or not costs:
                return None
            normalized = {
                str(key): float(value)
                for key, value in costs.items()
                if isinstance(key, str) and isinstance(value, (int, float)) and not isinstance(value, bool)
            }
            credit_usd = float(os.environ["MOREAI_RUNWAY_CREDIT_USD"])
            credits_per_usd = float(os.environ["MOREAI_CREDITS_PER_USD"])
            poll_timeout = float(os.getenv("MOREAI_VIDEO_PROVIDER_TIMEOUT_SECONDS", "420"))
            max_bytes = int(os.getenv("MOREAI_MEDIA_MAX_ARTIFACT_BYTES", "100000000"))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        configured_model = os.getenv("MOREAI_RUNWAY_VIDEO_MODEL", "gen4.5")
        if configured_model not in cls.SUPPORTED_MODELS:
            return None
        if f"{configured_model}:5:1280:720" not in normalized:
            return None
        if (
            len(normalized) != len(costs)
            or any(not math.isfinite(value) or value <= 0 for value in normalized.values())
            or not math.isfinite(credit_usd) or credit_usd <= 0
            or not math.isfinite(credits_per_usd) or credits_per_usd <= 0
            or not 30 <= poll_timeout <= 420
            or not 1_000_000 <= max_bytes <= 150_000_000
        ):
            return None
        suffixes = [item.strip().lower().lstrip(".") for item in os.environ["MOREAI_RUNWAY_OUTPUT_HOST_SUFFIXES"].split(",") if item.strip()]
        if not suffixes or any("/" in item or ":" in item for item in suffixes):
            return None
        return cls(http=http, client=client, artifacts=artifacts, accounting=accounting, estimator=estimator)

    def _price(self, model: str, duration: int, ratio: str) -> float:
        costs = json.loads(os.environ["MOREAI_RUNWAY_VIDEO_COSTS_JSON"])
        key = f"{model}:{duration}:{ratio}"
        value = costs.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError("runway_video_price_not_configured")
        price = float(value)
        if not math.isfinite(price) or price <= 0:
            raise RuntimeError("runway_video_price_invalid")
        return price

    def _route(self, model: str, max_cost: float) -> ResolvedModelRoute:
        return ResolvedModelRoute(
            provider_key="runway",
            model_key=model,
            display_name=model,
            base_url=self.API_BASE,
            secret_env_name="RUNWAYML_API_SECRET",
            input_cost_per_million=0.0,
            output_cost_per_million=max_cost * 1_000_000,
            max_input_tokens=32000,
            max_output_tokens=1,
            capabilities=("video_generation",),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {os.environ['RUNWAYML_API_SECRET']}",
            "Content-Type": "application/json",
            "X-Runway-Version": self.API_VERSION,
        }

    def _allowed_output_url(self, value: Any) -> str:
        if not isinstance(value, str) or len(value) > 2048:
            raise RuntimeError("runway_video_output_url_invalid")
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        suffixes = [
            item.strip().lower().lstrip(".")
            for item in os.environ["MOREAI_RUNWAY_OUTPUT_HOST_SUFFIXES"].split(",")
            if item.strip()
        ]
        if parsed.scheme != "https" or not host or not any(host == suffix or host.endswith("." + suffix) for suffix in suffixes):
            raise RuntimeError("runway_video_output_host_not_allowed")
        return value

    async def video_generate(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        prompt = arguments.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 1000:
            raise ValueError("video_prompt_invalid")
        model = os.getenv("MOREAI_RUNWAY_VIDEO_MODEL", "gen4.5")
        if model not in self.SUPPORTED_MODELS:
            raise ValueError("runway_video_model_not_supported")
        duration = arguments.get("duration", 5)
        if isinstance(duration, bool) or not isinstance(duration, int) or duration not in {5, 10}:
            raise ValueError("video_duration_not_supported")
        ratio = arguments.get("ratio", "1280:720")
        if ratio not in {"1280:720", "720:1280"}:
            raise ValueError("video_ratio_not_supported")
        seed = arguments.get("seed")
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 4294967295):
            raise ValueError("video_seed_invalid")

        max_cost = self._price(model, duration, ratio)
        route = self._route(model, max_cost)
        request_payload = {
            "model": model, "promptText": prompt.strip(),
            "ratio": ratio, "duration": duration, "outputFormat": "mp4",
        }
        if seed is not None:
            request_payload["seed"] = seed
        request_hash = hashlib.sha256(
            json.dumps(request_payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        request_key = f"{run_id}:video_generate:{request_hash[:32]}"
        checkpoint_key = f"media.runway.video.{request_hash[:32]}"
        checkpoints = await self.client.list_checkpoints(run_id)
        state = checkpoints.get(checkpoint_key) if isinstance(checkpoints, dict) else None
        state = state if isinstance(state, dict) else {}
        if state.get("status") == "completed" and isinstance(state.get("result_text"), str):
            return state["result_text"]

        if not state:
            state = {"status": "intent", "request_hash": request_hash}
            await self.client.checkpoint(run_id, checkpoint_key, state)

        claim = await self.accounting.claim_request(
            user_id=user_id, run_id=run_id, request_key=request_key, request_hash=request_hash,
        )
        request_id = str(claim["id"])
        if claim.get("status") == "succeeded" and isinstance(claim.get("response_text"), str):
            return claim["response_text"]
        if claim.get("status") in {"failed", "unknown"}:
            raise RuntimeError("runway_video_usage_request_not_recoverable")
        if state.get("request_hash") != request_hash:
            raise RuntimeError("runway_video_checkpoint_payload_conflict")
        if state.get("status") in {"submitting", "submission_unknown"} and not state.get("task_id"):
            await self.accounting.fail(
                request_id=request_id,
                error_code="runway_video_submission_outcome_unknown",
                release_reservation=False,
                request_key=f"{request_key}:unknown",
            )
            raise RuntimeError("runway_video_submission_outcome_unknown_reservation_retained")
        if state.get("status") == "failed":
            raise RuntimeError("runway_video_task_failed")

        request_rows = await self.client.select("llm_request_records", {
            "id": f"eq.{request_id}",
            "select": "id,status,reservation_id,quota_reservation,actual_cost",
            "limit": "1",
        })
        if not request_rows:
            raise RuntimeError("runway_video_usage_request_missing")
        request_row = request_rows[0]
        if claim.get("status") == "provider_succeeded":
            stored_cost = request_row.get("actual_cost")
            try:
                stored_cost = float(stored_cost)
            except (TypeError, ValueError):
                stored_cost = 0.0
            if not math.isfinite(stored_cost) or stored_cost <= 0:
                raise RuntimeError("runway_video_provider_result_cost_missing")
            stored_credits = stored_cost * float(os.environ["MOREAI_CREDITS_PER_USD"])
            await self.accounting.finalize(
                request_id=request_id, actual_credits=stored_credits,
                request_key=f"{request_key}:settle",
                provider_response_id=state.get("task_id") if isinstance(state.get("task_id"), str) else None,
            )
            if isinstance(claim.get("response_text"), str):
                return claim["response_text"]
            raise RuntimeError("runway_video_provider_result_text_missing")
        reservation_id = request_row.get("reservation_id")
        if not reservation_id:
            quota_reservation = request_row.get("quota_reservation")
            if quota_reservation:
                raise RuntimeError("runway_video_reservation_state_unknown")
            estimate = await self.estimator.estimate(
                route=route, messages=[{"role": "user", "content": prompt.strip()}],
            )
            reserved = await self.accounting.reserve(
                request_id=request_id, user_id=user_id, run_id=run_id,
                request_key=request_key,
                estimated_credits=estimate.estimated_credits,
                estimated_cost=estimate.estimated_cost,
                workspace_id=None, partner_id=None,
                entitlement_key=os.environ["MOREAI_MEDIA_ENTITLEMENT_KEY"],
                quota_metric_key=os.environ["MOREAI_MEDIA_QUOTA_METRIC_KEY"],
            )
            reservation_id = reserved
        if state.get("status") in {"intent", "reserved"}:
            state = {"status": "reserved", "request_hash": request_hash, "request_id": request_id, "reservation_id": str(reservation_id)}
            await self.client.checkpoint(run_id, checkpoint_key, state)
            state = {**state, "status": "submitting"}
            await self.client.checkpoint(run_id, checkpoint_key, state)
            try:
                response = await self.http.post(
                    f"{self.API_BASE}/text_to_video",
                    json=request_payload,
                    headers=self._headers(),
                    timeout=30.0,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                state = {**state, "status": "submission_unknown"}
                await self.client.checkpoint(run_id, checkpoint_key, state)
                await self.accounting.fail(
                    request_id=request_id, error_code="runway_video_submission_unknown",
                    release_reservation=False, request_key=f"{request_key}:unknown",
                )
                raise RuntimeError("runway_video_submission_outcome_unknown_reservation_retained") from exc
            if response.status_code >= 500:
                state = {**state, "status": "submission_unknown"}
                await self.client.checkpoint(run_id, checkpoint_key, state)
                await self.accounting.fail(
                    request_id=request_id, error_code="runway_video_provider_server_error",
                    release_reservation=False, request_key=f"{request_key}:unknown",
                )
                raise RuntimeError("runway_video_submission_outcome_unknown_reservation_retained")
            if response.status_code >= 400:
                await self.accounting.fail(
                    request_id=request_id, error_code="runway_video_provider_rejected",
                    release_reservation=True, request_key=f"{request_key}:release",
                )
                await self.client.checkpoint(run_id, checkpoint_key, {**state, "status": "failed", "provider_status_code": response.status_code})
                raise RuntimeError("runway_video_provider_rejected")
            created = response.json()
            task_id = created.get("id") if isinstance(created, dict) else None
            estimated = created.get("estimatedCost") if isinstance(created, dict) else None
            provider_credits = estimated.get("credits") if isinstance(estimated, dict) else None
            if not isinstance(task_id, str) or not task_id or isinstance(provider_credits, bool) or not isinstance(provider_credits, (int, float)) or provider_credits <= 0:
                state = {**state, "status": "submission_unknown"}
                await self.client.checkpoint(run_id, checkpoint_key, state)
                await self.accounting.fail(
                    request_id=request_id, error_code="runway_video_task_receipt_invalid",
                    release_reservation=False, request_key=f"{request_key}:unknown",
                )
                raise RuntimeError("runway_video_task_receipt_invalid_reservation_retained")
            state = {
                **state, "status": "submitted", "task_id": task_id,
                "provider_credits": float(provider_credits),
            }
            await self.client.checkpoint(run_id, checkpoint_key, state)
        task_id = state.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise RuntimeError("runway_video_task_checkpoint_missing")

        poll_timeout = min(420.0, max(30.0, float(os.getenv("MOREAI_VIDEO_PROVIDER_TIMEOUT_SECONDS", "420"))))
        poll_interval = max(5.0, min(15.0, float(os.getenv("MOREAI_RUNWAY_POLL_INTERVAL_SECONDS", "5"))))
        poll_started = time.monotonic()
        task: dict[str, Any] | None = None
        while time.monotonic() - poll_started < poll_timeout:
            try:
                status_response = await self.http.get(
                    f"{self.API_BASE}/tasks/{task_id}", headers=self._headers(), timeout=30.0,
                )
                status_response.raise_for_status()
                current = status_response.json()
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError):
                raise RuntimeError("runway_video_task_poll_transient")
            if not isinstance(current, dict):
                raise RuntimeError("runway_video_task_response_invalid")
            task = current
            status = str(current.get("status") or "").upper()
            if status == "SUCCEEDED":
                break
            if status in {"FAILED", "CANCELLED", "ABORTED"}:
                await self.accounting.fail(
                    request_id=request_id, error_code="runway_video_task_failed",
                    release_reservation=True, request_key=f"{request_key}:release",
                )
                await self.client.checkpoint(run_id, checkpoint_key, {
                    **state, "status": "failed", "provider_status": status,
                })
                raise RuntimeError("runway_video_task_failed")
            await self.client.checkpoint(run_id, checkpoint_key, {
                **state, "status": "polling", "provider_status": status,
            })
            await asyncio.sleep(poll_interval)
        if not isinstance(task, dict) or str(task.get("status") or "").upper() != "SUCCEEDED":
            raise TimeoutError("runway_video_task_still_processing")

        output = task.get("output")
        if not isinstance(output, list) or not output:
            raise RuntimeError("runway_video_output_missing")
        output_url = self._allowed_output_url(output[0])
        provider_credits = state.get("provider_credits")
        credit_usd = float(os.environ["MOREAI_RUNWAY_CREDIT_USD"])
        actual_cost = float(provider_credits) * credit_usd
        if not math.isfinite(actual_cost) or actual_cost <= 0 or actual_cost > max_cost:
            await self.accounting.fail(
                request_id=request_id, error_code="runway_video_cost_exceeds_reserved_max",
                release_reservation=False, request_key=f"{request_key}:unknown",
            )
            raise RuntimeError("runway_video_cost_exceeds_reserved_max_reservation_retained")

        artifact_json = state.get("artifact_json")
        if not isinstance(artifact_json, str):
            download = await self.http.get(output_url, timeout=120.0)
            download.raise_for_status()
            content_type = (download.headers.get("content-type") or "").split(";", 1)[0].lower()
            if content_type not in {"video/mp4", "application/octet-stream"}:
                raise RuntimeError("runway_video_artifact_mime_type_invalid")
            content_length = download.headers.get("content-length")
            max_bytes = int(os.getenv("MOREAI_MEDIA_MAX_ARTIFACT_BYTES", "100000000"))
            if content_length and int(content_length) > max_bytes:
                raise RuntimeError("runway_video_artifact_size_invalid")
            raw = download.content
            if not raw or len(raw) > max_bytes:
                raise RuntimeError("runway_video_artifact_size_invalid")
            artifact_id = str(uuid5(NAMESPACE_URL, f"moreai:{user_id}:{run_id}:{request_hash}"))
            artifact_json = await self.artifacts.save_bytes(
                filename=f"moreai-video-{run_id[:8]}.mp4",
                raw=raw, mime_type="video/mp4", run_id=run_id, user_id=user_id,
                metadata={"provider": "runway", "model": model, "media_type": "video", "provider_task_id": task_id},
                artifact_id=artifact_id,
            )
            state = {**state, "status": "artifact_stored", "artifact_json": artifact_json}
            await self.client.checkpoint(run_id, checkpoint_key, state)

        artifact = json.loads(artifact_json)
        result_text = json.dumps({
            "status": "generated", "provider": "runway", "model": model,
            "provider_task_id": task_id, "duration_seconds": duration, "artifact": artifact,
        }, ensure_ascii=False, separators=(",", ":"))
        provider_result = {
            "text": result_text, "provider_key": "runway", "model_key": model,
            "input_tokens": 0, "output_tokens": 0, "actual_cost": actual_cost,
            "provider_response_id": task_id,
        }
        await self.accounting.record_provider_result(
            request_id=request_id, result=provider_result, latency_ms=0,
        )
        actual_credits = await self.estimator.actual_credits(route=route, result=provider_result)
        await self.accounting.finalize(
            request_id=request_id, actual_credits=actual_credits,
            request_key=f"{request_key}:settle", provider_response_id=task_id,
        )
        state = {**state, "status": "completed", "result_text": result_text}
        await self.client.checkpoint(run_id, checkpoint_key, state)
        return result_text
