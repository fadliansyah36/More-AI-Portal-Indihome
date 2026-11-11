from __future__ import annotations

import os
from typing import Any

import httpx

from engine.llm.errors import RetryableProviderError
from engine.llm.router import ResolvedModelRoute


class OpenAICompatibleAdapter:
    """OpenAI-compatible adapter with explicit retryable availability classification."""

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    @staticmethod
    def _request_timeout() -> float:
        raw = os.getenv("MOREAI_PROVIDER_TIMEOUT_SECONDS", "90")
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("invalid_provider_timeout_configuration") from exc
        if not 1 <= value <= 600:
            raise RuntimeError("provider_timeout_must_be_between_1_and_600_seconds")
        return value

    @staticmethod
    def _raise_status(response: httpx.Response) -> None:
        if response.status_code in {408, 425, 429} or response.status_code >= 500:
            raise RetryableProviderError(f"provider_retryable_http_{response.status_code}")
        if response.status_code >= 400:
            raise RuntimeError("provider_request_rejected")

    async def complete(
        self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        api_key = os.getenv(route.secret_env_name)
        if not api_key:
            raise RuntimeError("provider_secret_not_configured")
        try:
            response = await self.http.post(
                f"{route.base_url}/chat/completions",
                json={
                    "model": route.model_key, "messages": messages, "stream": False,
                    **({"tools": tools, "tool_choice": "auto"} if tools else {}),
                },
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=self._request_timeout(),
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise RetryableProviderError("provider_transport_unavailable") from exc
        self._raise_status(response)
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
        message = choices[0].get("message") or {}
        tool_calls = message.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            raise RuntimeError("provider_tool_calls_invalid")
        return {
            "text": message.get("content") or "", "tool_calls": tool_calls,
            "provider_key": route.provider_key, "model_key": route.model_key,
            "input_tokens": input_tokens, "output_tokens": output_tokens,
            "actual_cost": actual_cost, "provider_response_id": payload.get("id"),
        }

    async def stream(self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]]):
        import json

        api_key = os.getenv(route.secret_env_name)
        if not api_key:
            raise RuntimeError("provider_secret_not_configured")
        usage = None
        response_id = None
        try:
            async with self.http.stream(
                "POST", f"{route.base_url}/chat/completions",
                json={
                    "model": route.model_key, "messages": messages, "stream": True,
                    "stream_options": {"include_usage": True},
                },
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=self._request_timeout(),
            ) as response:
                self._raise_status(response)
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    response_id = payload.get("id") or response_id
                    if payload.get("error"):
                        raise RetryableProviderError("provider_stream_error")
                    choices = payload.get("choices") or []
                    if choices:
                        delta = (choices[0].get("delta") or {}).get("content")
                        if isinstance(delta, str) and delta:
                            yield {"type": "delta", "text": delta}
                    if payload.get("usage"):
                        usage = payload["usage"]
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise RetryableProviderError("provider_stream_transport_unavailable") from exc
        if usage is None:
            raise RetryableProviderError("provider_stream_usage_missing")
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        actual_cost = (
            input_tokens * route.input_cost_per_million
            + output_tokens * route.output_cost_per_million
        ) / 1_000_000
        yield {
            "type": "usage", "provider_key": route.provider_key,
            "model_key": route.model_key, "input_tokens": input_tokens,
            "output_tokens": output_tokens, "actual_cost": actual_cost,
            "provider_response_id": response_id,
        }
