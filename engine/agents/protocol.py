from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol


CheckpointWriter = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class AgentRunContext:
    run_id: str
    user_id: str
    workspace_id: str | None
    conversation_id: str | None
    agent_definition_id: str | None
    attempt: int
    max_attempts: int


@dataclass(frozen=True)
class AgentRunResult:
    output: dict[str, Any]


class AgentRuntime(Protocol):
    async def execute(
        self,
        context: AgentRunContext,
        payload: dict[str, Any],
        checkpoint: CheckpointWriter,
        cancelled: Any,
    ) -> AgentRunResult: ...
