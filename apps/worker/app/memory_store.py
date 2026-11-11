from __future__ import annotations

from typing import Any

from app.client import WorkerRpcClient
from engine.agents.memory import ConversationMemoryStore
from engine.agents.types import Message, ToolCall, ToolFunction


class SupabaseConversationMemoryStore(ConversationMemoryStore):
    """Durable conversation history with explicit owner/workspace checks and run-scoped replay."""

    def __init__(self, client: WorkerRpcClient):
        self.client = client

    async def _assert_owner(self, *, conversation_id: str, user_id: str, workspace_id: str | None) -> None:
        params = {
            "id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}",
            "select": "id,user_id,workspace_id,status", "limit": "1",
            "workspace_id": "is.null" if workspace_id is None else f"eq.{workspace_id}",
        }
        rows = await self.client.select("conversations", params)
        if not rows or rows[0].get("status") == "deleted":
            raise PermissionError("conversation_memory_access_denied")

    @staticmethod
    def _messages(rows: list[dict[str, Any]]) -> list[Message]:
        messages: list[Message] = []
        for row in rows:
            role = row.get("role")
            if role not in {"system", "user", "assistant", "tool"}:
                continue
            metadata = row.get("metadata") or {}
            raw_calls = metadata.get("tool_calls") if isinstance(metadata, dict) else None
            calls: list[ToolCall] = []
            if isinstance(raw_calls, list):
                for raw in raw_calls:
                    if not isinstance(raw, dict) or not isinstance(raw.get("function"), dict):
                        continue
                    function = raw["function"]
                    if isinstance(raw.get("id"), str) and isinstance(function.get("name"), str):
                        calls.append(ToolCall(
                            id=raw["id"], type=raw.get("type", "function"),
                            function=ToolFunction(
                                name=function["name"],
                                arguments=function.get("arguments", "{}"),
                            ),
                        ))
            messages.append(Message(
                role=role, content=row.get("content") or "",
                tool_calls=calls or None,
                name=metadata.get("name") if isinstance(metadata, dict) else None,
                tool_call_id=metadata.get("tool_call_id") if isinstance(metadata, dict) else None,
            ))
        return messages

    async def load(
        self, *, conversation_id: str, user_id: str,
        workspace_id: str | None = None, limit: int = 100,
    ) -> list[Message]:
        if not 1 <= limit <= 200:
            raise ValueError("conversation_memory_limit_out_of_range")
        await self._assert_owner(
            conversation_id=conversation_id, user_id=user_id, workspace_id=workspace_id,
        )
        rows = await self.client.select("conversation_messages", {
            "conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}",
            "select": "role,content,metadata,created_at",
            "order": "created_at.desc", "limit": str(limit),
        })
        return self._messages(list(reversed(rows)))

    async def load_run(
        self, *, conversation_id: str, user_id: str, run_id: str,
        workspace_id: str | None = None, limit: int = 200,
    ) -> list[Message]:
        if not 1 <= limit <= 500:
            raise ValueError("conversation_run_memory_limit_out_of_range")
        await self._assert_owner(
            conversation_id=conversation_id, user_id=user_id, workspace_id=workspace_id,
        )
        rows = await self.client.select("conversation_messages", {
            "conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}",
            "run_id": f"eq.{run_id}",
            "select": "role,content,metadata,created_at",
            "order": "created_at.asc", "limit": str(limit),
        })
        return self._messages(rows)

    async def append(
        self, *, conversation_id: str, user_id: str, run_id: str,
        message: Message, message_key: str, workspace_id: str | None = None,
    ) -> None:
        if not message_key or len(message_key) > 200:
            raise ValueError("conversation_memory_message_key_invalid")
        await self._assert_owner(
            conversation_id=conversation_id, user_id=user_id, workspace_id=workspace_id,
        )
        existing = await self.client.select("conversation_messages", {
            "conversation_id": f"eq.{conversation_id}", "user_id": f"eq.{user_id}",
            "run_id": f"eq.{run_id}", "metadata->>message_key": f"eq.{message_key}",
            "select": "id", "limit": "1",
        })
        if existing:
            return

        metadata: dict[str, Any] = {"message_key": message_key}
        if message.name is not None:
            metadata["name"] = message.name
        if message.tool_call_id is not None:
            metadata["tool_call_id"] = message.tool_call_id
        if message.tool_calls is not None:
            metadata["tool_calls"] = [
                {
                    "id": call.id, "type": call.type,
                    "function": {"name": call.function.name, "arguments": call.function.arguments},
                }
                for call in message.tool_calls
            ]
        await self.client.insert("conversation_messages", {
            "conversation_id": conversation_id, "user_id": user_id,
            "role": message.role, "content": message.content or "",
            "run_id": run_id, "token_input": 0, "token_output": 0,
            "metadata": metadata,
        })
