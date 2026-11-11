import asyncio

from engine.agents.gateway_runtime import GatewayManusRuntime
from engine.agents.protocol import AgentRunContext


class FakeGateway:
    async def stream(self, **kwargs):
        yield {"type": "delta", "text": "verified "}
        yield {"type": "delta", "text": "answer"}
        yield {"type": "done", "provider_key": "test", "model_key": "test-model"}


def test_gateway_manus_runtime_uses_metered_gateway_and_checkpoints():
    async def run():
        checkpoints = []

        async def checkpoint(key, state):
            checkpoints.append((key, state))
            return {"ok": True}

        runtime = GatewayManusRuntime(FakeGateway())
        result = await runtime.execute(
            AgentRunContext("run-1", "user-1", None, None, None, 0, 3),
            {"prompt": "hello"},
            checkpoint,
            asyncio.Event(),
        )
        assert result.output["text"] == "verified answer"
        assert checkpoints[-1][0] == "manus.response"
        assert checkpoints[0][0] == "stream.chunk.000001"

    asyncio.run(run())


def test_gateway_manus_runtime_restores_and_persists_conversation_memory():
    async def run():
        from engine.agents.types import Message

        class MemoryStore:
            def __init__(self):
                self.saved = []
            async def load(self, *, conversation_id, user_id, workspace_id=None, limit=100):
                assert (conversation_id, user_id, workspace_id) == ("conv-1", "user-1", "ws-1")
                return [Message.user_message("earlier question"), Message.assistant_message("earlier answer")]
            async def append(self, *, conversation_id, user_id, run_id, message, message_key, workspace_id=None):
                self.saved.append((message.role, message.content, message_key))

        class CapturingGateway(FakeGateway):
            async def stream(self, **kwargs):
                self.messages = kwargs["messages"]
                async for event in super().stream(**kwargs):
                    yield event

        memory = MemoryStore()
        gateway = CapturingGateway()
        runtime = GatewayManusRuntime(gateway, memory_store=memory)
        async def checkpoint(key, state):
            return {"ok": True}

        context = AgentRunContext("run-1", "user-1", "ws-1", "conv-1", None, 0, 3)
        result = await runtime.execute(context, {"prompt": "new question"}, checkpoint, asyncio.Event())
        assert result.output["text"] == "verified answer"
        assert [item["content"] for item in gateway.messages if item["role"] in {"user", "assistant"}] == [
            "earlier question", "earlier answer", "new question"
        ]
        assert memory.saved == [
            ("user", "new question", "run-1:user"),
            ("assistant", "verified answer", "run-1:assistant"),
        ]

    asyncio.run(run())
