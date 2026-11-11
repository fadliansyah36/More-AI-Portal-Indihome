import asyncio
from uuid import UUID

from app.routers.agent_runs import _event_with_checkpoint_state


class FakeRepository:
    async def select(self, table, params):
        assert table == "agent_run_checkpoints"
        return [{
            "checkpoint_key": "openmanus.round.1.response",
            "state": {
                "text": "safe assistant text",
                "tool_calls": [{"id": "call-1", "function": {"arguments": "secret-like input"}}],
                "arguments": {"private": "do-not-return"},
                "observation": "private tool output",
                "provider_key": "internal-provider",
                "rounds": 1,
            },
        }]


def test_run_event_checkpoint_redacts_tool_arguments_and_observations():
    async def run():
        row = await _event_with_checkpoint_state(
            FakeRepository(), UUID("00000000-0000-0000-0000-000000000001"),
            {"event_type": "worker.checkpoint", "sequence": 1, "payload": {"checkpoint_key": "openmanus.round.1.response"}},
        )
        assert row["checkpoint"] == {"text": "safe assistant text", "rounds": 1}
        assert "arguments" not in row["checkpoint"]
        assert "observation" not in row["checkpoint"]
        assert "tool_calls" not in row["checkpoint"]
    asyncio.run(run())
