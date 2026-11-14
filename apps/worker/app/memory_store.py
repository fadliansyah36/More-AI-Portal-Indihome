from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta, timezone
import json
import os

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
                metadata=metadata if isinstance(metadata, dict) else {},
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

    async def load_episodes(
        self, *, user_id: str, workspace_id: str | None = None, limit: int = 8,
    ) -> list[dict[str, str]]:
        """Load only consented episodic records in the exact owner/workspace scope."""
        if not 1 <= limit <= 12:
            raise ValueError("episodic_memory_limit_out_of_range")
        preferences = await self.client.select("moreai_customer_memory_preferences", {
            "user_id": f"eq.{user_id}", "enabled": "eq.true",
            "select": "user_id,enabled,consent_version", "limit": "1",
        })
        if not preferences:
            return []
        try:
            retention_days = int(os.getenv("MOREAI_EPISODIC_MEMORY_RETENTION_DAYS", "90"))
        except ValueError:
            retention_days = 90
        if not 7 <= retention_days <= 3650:
            retention_days = 90
        now = datetime.now(timezone.utc)
        expiry_cutoff = now.isoformat()
        # Expire episodic metadata without deleting the underlying chat transcript
        # or its independent citation provenance.
        expired = await self.client.select("conversation_messages", {
            "user_id": f"eq.{user_id}",
            "metadata->>memory_type": "eq.episodic",
            "metadata->>episode_expires_at": f"lte.{expiry_cutoff}",
            "select": "id,metadata",
            "order": "created_at.asc,id.asc",
            "limit": "100",
        })
        for row in expired:
            prior = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            cleaned = {key: value for key, value in prior.items()
                       if key not in {"memory_type", "memory_scope", "workspace_id", "episode"}}
            await self.client.update(
                "conversation_messages",
                {"id": f"eq.{row['id']}", "user_id": f"eq.{user_id}"},
                {"metadata": cleaned},
            )
        filters = {
            "user_id": f"eq.{user_id}",
            "metadata->>memory_type": "eq.episodic",
            "metadata->>episode_expires_at": f"gt.{expiry_cutoff}",
            "select": "content,metadata,created_at",
            "order": "created_at.desc,id.desc",
            "limit": str(limit),
        }
        filters["metadata->>workspace_id"] = "is.null" if workspace_id is None else f"eq.{workspace_id}"
        rows = await self.client.select("conversation_messages", filters)
        episodes: list[dict[str, str]] = []
        for row in rows:
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            episode = metadata.get("episode") if isinstance(metadata.get("episode"), dict) else {}
            prompt = episode.get("prompt")
            outcome = episode.get("outcome")
            if not isinstance(prompt, str) or not isinstance(outcome, str):
                continue
            episodes.append({
                "prompt": prompt[:900],
                "outcome": outcome[:1400],
                "created_at": str(row.get("created_at") or "")[:40],
            })
        return episodes

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
        if isinstance(message.metadata, dict):
            # Episodic recall/write is opt-in; citations remain attached to the chat
            # message even when the owner has not enabled long-term memory.
            supplied = dict(message.metadata)
            if supplied.get("memory_type") == "episodic":
                preferences = await self.client.select("moreai_customer_memory_preferences", {
                    "user_id": f"eq.{user_id}", "enabled": "eq.true",
                    "select": "user_id", "limit": "1",
                })
                if not preferences:
                    for key in ("memory_type", "memory_scope", "workspace_id", "episode", "episode_expires_at"):
                        supplied.pop(key, None)
                else:
                    try:
                        retention_days = int(os.getenv("MOREAI_EPISODIC_MEMORY_RETENTION_DAYS", "90"))
                    except ValueError:
                        retention_days = 90
                    if not 7 <= retention_days <= 3650:
                        retention_days = 90
                    supplied["episode_expires_at"] = (
                        datetime.now(timezone.utc) + timedelta(days=retention_days)
                    ).isoformat()
            if len(json.dumps(supplied, ensure_ascii=False, default=str)) > 12000:
                raise ValueError("conversation_message_metadata_exceeds_limit")
            metadata.update(supplied)
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


class SupabasePersonalMemoryStore:
    """Loads only explicitly consented, user-authored Personal Memory records."""

    def __init__(self, client: WorkerRpcClient):
        self.client = client

    async def load_for_context(self, *, user_id: str, limit: int = 20) -> list[dict[str, str]]:
        if not 1 <= limit <= 20:
            raise ValueError("personal_memory_context_limit_out_of_range")
        preferences = await self.client.select("moreai_customer_memory_preferences", {
            "user_id": f"eq.{user_id}",
            "enabled": "eq.true",
            "select": "user_id,enabled,consent_version",
            "limit": "1",
        })
        if not preferences:
            return []
        from datetime import datetime, timezone
        rows = await self.client.select("moreai_customer_memories", {
            "user_id": f"eq.{user_id}",
            "expires_at": f"gt.{datetime.now(timezone.utc).isoformat()}",
            "source_type": "eq.user_created", "scope": "eq.personal",
            "select": "title,content,expires_at",
            "order": "updated_at.desc,id.desc",
            "limit": str(limit),
        })
        return [
            {"title": str(row.get("title") or "")[:120], "content": str(row.get("content") or "")[:4000]}
            for row in rows
            if isinstance(row.get("title"), str) and isinstance(row.get("content"), str)
        ]
