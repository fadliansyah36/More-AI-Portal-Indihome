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
        assert checkpoints[0][0] == "manus.response"
    asyncio.run(run())
