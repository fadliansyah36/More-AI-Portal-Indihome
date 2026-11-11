import asyncio

import pytest

from app.memory_store import SupabaseConversationMemoryStore
from engine.agents.types import Message, ToolCall, ToolFunction


class FakeClient:
    def __init__(self):
        self.inserted = []
        self.owner_rows = [{"id": "conv-1", "user_id": "user-1", "workspace_id": "ws-1", "status": "active"}]
        self.history = []

    async def select(self, table, params):
        if table == "conversations":
            return self.owner_rows
        if table == "conversation_messages":
            if "metadata->>message_key" in params:
                return []
            return self.history

    async def insert(self, table, payload):
        self.inserted.append((table, payload))
        return payload


def test_memory_store_loads_messages_in_chronological_order_and_restores_tool_calls():
    async def run():
        client = FakeClient()
        client.history = [
            {"role": "assistant", "content": "second", "metadata": {}},
            {
                "role": "assistant",
                "content": "",
                "metadata": {
                    "tool_call_id": "call-1",
                    "tool_calls": [{
                        "id": "call-1",
                        "type": "function",
                        "function": {"name": "search", "arguments": "{\"q\":\"x\"}"},
                    }],
                },
            },
        ]
        store = SupabaseConversationMemoryStore(client)
        messages = await store.load(conversation_id="conv-1", user_id="user-1", workspace_id="ws-1")
        assert len(messages) == 2
        assert messages[0].tool_calls[0].function.name == "search"
        assert messages[1].content == "second"

    asyncio.run(run())


def test_memory_store_append_is_owner_scoped_and_idempotent():
    async def run():
        client = FakeClient()
        store = SupabaseConversationMemoryStore(client)
        message = Message.tool_message("result", name="search", tool_call_id="call-1")
        await store.append(
            conversation_id="conv-1",
            user_id="user-1",
            workspace_id="ws-1",
            run_id="run-1",
            message=message,
            message_key="run-1:tool:0",
        )
        assert len(client.inserted) == 1
        table, payload = client.inserted[0]
        assert table == "conversation_messages"
        assert payload["user_id"] == "user-1"
        assert payload["conversation_id"] == "conv-1"
        assert payload["metadata"]["tool_call_id"] == "call-1"
        assert payload["metadata"]["message_key"] == "run-1:tool:0"
        assert payload["token_input"] == 0
        assert payload["token_output"] == 0

    asyncio.run(run())


def test_memory_store_denies_access_when_conversation_owner_does_not_match():
    async def run():
        client = FakeClient()
        client.owner_rows = []
        store = SupabaseConversationMemoryStore(client)
        with pytest.raises(PermissionError, match="conversation_memory_access_denied"):
            await store.load(conversation_id="conv-1", user_id="attacker", workspace_id="ws-1")

    asyncio.run(run())
