from __future__ import annotations

import os
from typing import Any

import httpx

from engine.llm.router import ResolvedModelRoute


class OpenAICompatibleAdapter:
    """OpenAI-compatible chat adapter; API keys are resolved from server environment only."""

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def complete(self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]]) -> dict[str, Any]:
        api_key = os.getenv(route.secret_env_name)
        if not api_key:
            raise RuntimeError("provider_secret_not_configured")
        response = await self.http.post(
            f"{route.base_url}/chat/completions",
            json={"model": route.model_key, "messages": messages, "stream": False},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=90.0,
        )
        if response.status_code >= 500:
            raise RuntimeError("provider_unavailable")
        if response.status_code >= 400:
            raise RuntimeError("provider_request_rejected")
        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("provider_empty_response")
        usage = payload.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        actual_cost = (
            input_tokens * route.input_cost_per_million
            + output_tokens * route.output_cost_per_million
        ) / 1_000_000
        return {
            "text": choices[0].get("message", {}).get("content") or "",
            "provider_key": route.provider_key,
            "model_key": route.model_key,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "actual_cost": actual_cost,
            "provider_response_id": payload.get("id"),
        }
