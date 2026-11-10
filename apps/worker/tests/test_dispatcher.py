import asyncio

from app.dispatcher import RegisteredAgentDispatcher
from engine.agents.protocol import AgentRunResult
from engine.orchestration.registry import AgentRegistry


class FakeAgent:
    async def execute(self, context, payload, checkpoint, cancelled):
        await checkpoint("agent.started", {"agent": payload["agent_key"]})
        return AgentRunResult({"text": payload["prompt"]})


def test_dispatcher_routes_only_registered_agent_keys():
    async def run():
        registry = AgentRegistry()
        registry.register("manus", FakeAgent())
        dispatcher = RegisteredAgentDispatcher(registry)
        events = []
        async def checkpoint(key, state):
            events.append((key, state))
            return {"ok": True}
        output = await dispatcher.dispatch(
            {"id": "run-1", "user_id": "user-1", "input": {"agent_key": "manus", "prompt": "hello"}},
            checkpoint,
            asyncio.Event(),
        )
        assert output == {"text": "hello"}
        assert events[0][0] == "agent.started"
    asyncio.run(run())


def test_dispatcher_fails_closed_for_unknown_agent():
    async def run():
        dispatcher = RegisteredAgentDispatcher(AgentRegistry())
        async def checkpoint(key, state):
            return {"ok": True}
        try:
            await dispatcher.dispatch(
                {"id": "run-1", "user_id": "user-1", "input": {"agent_key": "not-enabled", "prompt": "hello"}},
                checkpoint,
                asyncio.Event(),
            )
        except LookupError:
            return
        raise AssertionError("unknown agent should be rejected")
    asyncio.run(run())
