import asyncio

import pytest

from engine.agents.durable_tool_runtime import DurableOpenManusRuntime
from engine.agents.protocol import AgentRunContext
from engine.agents.types import Message


class FakeMemoryStore:
    def __init__(self):
        self.rows = []

    async def load(self, *, conversation_id, user_id, workspace_id=None, limit=100):
        return [row["message"] for row in self.rows[-limit:]]

    async def load_run(self, *, conversation_id, user_id, run_id, workspace_id=None, limit=200):
        return [row["message"] for row in self.rows if row["run_id"] == run_id][-limit:]

    async def append(self, *, conversation_id, user_id, run_id, message, message_key, workspace_id=None):
        if any(row["key"] == message_key for row in self.rows):
            return
        self.rows.append({"run_id": run_id, "key": message_key, "message": message})


class FakeGateway:
    def __init__(self):
        self.outer_rounds = 0
        self.nested_calls = 0

    async def complete(self, *, request_key, **kwargs):
        if ":tool:nested:" in request_key:
            self.nested_calls += 1
            return {"text": "tool-result"}
        self.outer_rounds += 1
        if self.outer_rounds == 1:
            return {
                "text": "",
                "provider_key": "provider",
                "model_key": "model",
                "tool_calls": [{
                    "id": "call-1", "type": "function",
                    "function": {
                        "name": "create_chat_completion",
                        "arguments": '{"messages":[{"role":"user","content":"nested"}]}',
                    },
                }],
            }
        return {"text": "completed after recovery", "provider_key": "provider", "model_key": "model", "tool_calls": []}


@pytest.mark.asyncio
async def test_tool_transcript_and_settled_tool_result_resume_after_worker_restart():
    memory = FakeMemoryStore()
    gateway = FakeGateway()
    runtime = DurableOpenManusRuntime(gateway, memory_store=memory)
    states = {}
    context = AgentRunContext(
        run_id="run-1", user_id="user-1", workspace_id="workspace-1",
        conversation_id="conversation-1", agent_definition_id=None,
        attempt=1, max_attempts=3,
    )

    async def first_checkpoint(key, state):
        if key.endswith(".observations"):
            raise RuntimeError("simulated_worker_restart_before_round_commit")
        states[key] = state
        return {"ok": True}

    with pytest.raises(RuntimeError, match="simulated_worker_restart"):
        await runtime.execute(
            context, {"prompt": "run a tool"}, first_checkpoint, asyncio.Event(),
        )

    assert gateway.nested_calls == 1
    assert any(row["message"].role == "tool" for row in memory.rows)

    async def retry_checkpoint(key, state):
        states[key] = state
        return {"ok": True}

    recovered_context = AgentRunContext(
        run_id="run-1", user_id="user-1", workspace_id="workspace-1",
        conversation_id="conversation-1", agent_definition_id=None,
        attempt=2, max_attempts=3, recovery_checkpoints=states,
    )
    result = await runtime.execute(
        recovered_context, {"prompt": "run a tool"}, retry_checkpoint, asyncio.Event(),
    )

    assert result.output["text"] == "completed after recovery"
    assert gateway.nested_calls == 1
    assert gateway.outer_rounds == 2
    assert "openmanus.round.1.observations" in states
    assert states["openmanus.final"]["output"]["text"] == "completed after recovery"
