from __future__ import annotations

import json
import os
from typing import Any

import httpx

from engine.llm.router import ResolvedModelRoute


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls = []
    for index, item in enumerate(message.get("tool_calls") or []):
        function = item.get("function") or {}
        name = function.get("name")
        raw_arguments = function.get("arguments") or "{}"
        if not isinstance(name, str) or not name:
            continue
        try:
            arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        except (TypeError, json.JSONDecodeError):
            raise RuntimeError("provider_tool_arguments_invalid") from None
        if not isinstance(arguments, dict):
            raise RuntimeError("provider_tool_arguments_must_be_object")
        calls.append({
            "id": str(item.get("id") or f"tool-call-{index}"),
            "type": "function",
            "function": {"name": name, "arguments": arguments},
            "index": index,
        })
    return calls


class OpenAICompatibleAdapter:
    """OpenAI-compatible chat adapter; credentials are resolved from server env only."""

    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def complete(
        self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None, tool_choice: Any = None,
    ) -> dict[str, Any]:
        api_key = os.getenv(route.secret_env_name)
        if not api_key:
            raise RuntimeError("provider_secret_not_configured")
        body: dict[str, Any] = {"model": route.model_key, "messages": messages, "stream": False}
        if tools:
            body["tools"] = tools
        if tool_choice is not None:
            body["tool_choice"] = tool_choice
        response = await self.http.post(
            f"{route.base_url}/chat/completions", json=body,
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
        choice = choices[0]
        message = choice.get("message") or {}
        usage = payload.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        actual_cost = (
            input_tokens * route.input_cost_per_million
            + output_tokens * route.output_cost_per_million
        ) / 1_000_000
        return {
            "text": message.get("content") or "",
            "tool_calls": _tool_calls(message),
            "finish_reason": choice.get("finish_reason"),
            "raw_response": payload,
            "provider_key": route.provider_key,
            "model_key": route.model_key,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "actual_cost": actual_cost,
            "provider_response_id": payload.get("id"),
        }

    async def stream(
        self, *, route: ResolvedModelRoute, messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None, tool_choice: Any = None,
    ):
        api_key = os.getenv(route.secret_env_name)
        if not api_key:
            raise RuntimeError("provider_secret_not_configured")
        body: dict[str, Any] = {
            "model": route.model_key, "messages": messages, "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            body["tools"] = tools
        if tool_choice is not None:
            body["tool_choice"] = tool_choice
        usage = None
        response_id = None
        finish_reason = None
        async with self.http.stream(
            "POST", f"{route.base_url}/chat/completions", json=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=90.0,
        ) as response:
            response.raise_for_status()
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
                    raise RuntimeError("provider_stream_error")
                choices = payload.get("choices") or []
                if choices:
                    choice = choices[0]
                    delta = choice.get("delta") or {}
                    text = delta.get("content")
                    if isinstance(text, str) and text:
                        yield {"type": "delta", "text": text}
                    for call in delta.get("tool_calls") or []:
                        function = call.get("function") or {}
                        yield {
                            "type": "tool_call_delta",
                            "tool_call_index": int(call.get("index") or 0),
                            "tool_call_id": call.get("id"),
                            "tool_name": function.get("name"),
                            "arguments_delta": function.get("arguments"),
                        }
                    if choice.get("finish_reason") is not None:
                        finish_reason = choice["finish_reason"]
                if payload.get("usage"):
                    usage = payload["usage"]
        if usage is None:
            raise RuntimeError("provider_stream_usage_missing")
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
            "provider_response_id": response_id, "finish_reason": finish_reason,
        }
