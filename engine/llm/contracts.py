from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMRequest:
    task_type: str
    messages: list[dict[str, Any]]
    user_id: str
    run_id: str | None
    idempotency_key: str


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider_key: str
    model_key: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    provider_response_id: str | None = None


class LLMProviderAdapter(Protocol):
    async def generate(self, request: LLMRequest, *, model_key: str) -> LLMResult: ...
