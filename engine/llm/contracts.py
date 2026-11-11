from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class LLMToolCall:
    """Provider-neutral, replayable function call emitted by an LLM."""

    id: str
    name: str
    arguments: dict[str, Any]
    index: int = 0


@dataclass(frozen=True)
class LLMStreamEvent:
    """Typed stream event; tool-call deltas are never flattened into assistant text."""

    type: Literal["delta", "tool_call_delta", "usage", "done", "error"]
    text: str | None = None
    tool_call_index: int | None = None
    tool_call_id: str | None = None
    tool_name: str | None = None
    arguments_delta: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    provider_key: str | None = None
    model_key: str | None = None
    provider_response_id: str | None = None
    finish_reason: str | None = None


@dataclass(frozen=True)
class LLMRequest:
    task_type: str
    messages: list[dict[str, Any]]
    user_id: str
    run_id: str | None
    idempotency_key: str
    workspace_id: str | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str | dict[str, Any] | None = None
    max_retries: int = 0


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider_key: str
    model_key: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    provider_response_id: str | None = None
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    finish_reason: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


class LLMProviderAdapter(Protocol):
    async def generate(self, request: LLMRequest, *, model_key: str) -> LLMResult: ...

    def stream(self, request: LLMRequest, *, model_key: str): ...
