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
        self.plan_steps = []

    async def create(self, **kwargs):
        self.plan_steps = [
            {"sequence": index + 1, "input": step, "status": "pending", "output": None}
            for index, step in enumerate(kwargs["steps"])
        ]
        return {"run_id": kwargs["run_id"]}

    async def get(self, *, run_id):
        return {"run_id": run_id, "steps": [dict(row) for row in self.plan_steps]}

    async def mark_step(self, **kwargs):
        self.steps.append(kwargs)
        row = self.plan_steps[kwargs["step_index"]]
        row["status"] = kwargs["status"]
        if kwargs.get("output") is not None:
            row["output"] = kwargs["output"]
        if kwargs.get("notes") is not None:
            row["notes"] = kwargs["notes"]
        return kwargs


class FakeExecutor:
    def __init__(self):
        self.payloads = []

    async def execute(self, context, payload, checkpoint, cancelled):
        self.payloads.append(payload)
        return AgentRunResult({"text": payload["prompt"]})


def test_planning_runtime_persists_and_executes_steps():
    async def run():
        store = FakeStore()
        executor = FakeExecutor()
        runtime = PlanningAgentRuntime(gateway=FakeGateway(), store=store, step_executor=executor)

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
        assert [item["status"] for item in store.plan_steps] == ["succeeded", "succeeded"]
        assert executor.payloads[0]["dependencies"] == []
        assert executor.payloads[1]["dependencies"] == [0]
        assert "Completed dependency results" in executor.payloads[1]["prompt"]
        assert "step one" in executor.payloads[1]["prompt"]

    asyncio.run(run())
