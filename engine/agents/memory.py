from __future__ import annotations

from typing import Protocol

from engine.agents.types import Message


class ConversationMemoryStore(Protocol):
    """Owner-scoped durable conversation memory boundary."""

    async def load(
        self, *, conversation_id: str, user_id: str,
        workspace_id: str | None = None, limit: int = 100,
    ) -> list[Message]: ...

    async def load_run(
        self, *, conversation_id: str, user_id: str, run_id: str,
        workspace_id: str | None = None, limit: int = 200,
    ) -> list[Message]: ...

    async def append(
        self, *, conversation_id: str, user_id: str, run_id: str,
        message: Message, message_key: str, workspace_id: str | None = None,
    ) -> None: ...
