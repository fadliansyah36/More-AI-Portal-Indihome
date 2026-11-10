import asyncio
import json

from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.agents.protocol import AgentRunContext, AgentRunResult


class FakeGateway:
    async def complete(self, **kwargs):
        return {"text": json.dumps({"title": "Plan", "steps": [
            {"objective": "step one", "dependencies": [], "expected_output": "one", "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 10, "output_tokens": 10}},
            {"objective": "step two", "dependencies": [0], "expected_output": "two", "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 10, "output_tokens": 10}},
        ]})}


class FakeStore:
    def __init__(self):
        self.steps = []
    async def create(self, **kwargs):
        return {"run_id": kwargs["run_id"]}
    async def mark_step(self, **kwargs):
        self.steps.append(kwargs)
        return kwargs


class FakeExecutor:
    async def execute(self, context, payload, checkpoint, cancelled):
        return AgentRunResult({"text": payload["prompt"]})


def test_planning_runtime_persists_and_executes_steps():
    async def run():
        store = FakeStore()
        runtime = PlanningAgentRuntime(gateway=FakeGateway(), store=store, step_executor=FakeExecutor())
        async def checkpoint(key, state):
            return {"ok": True}
        result = await runtime.execute(
            AgentRunContext("run-1", "user-1", None, None, None, 0, 3),
            {"prompt": "build a plan"},
            checkpoint,
            asyncio.Event(),
        )
        assert result.output["completed_steps"] == 2
        assert [item["status"] for item in store.steps] == ["running", "succeeded", "running", "succeeded"]
    asyncio.run(run())
