import asyncio
import json

from engine.agents.planning_runtime import PlanningAgentRuntime
from engine.agents.protocol import AgentRunContext, AgentRunResult


class FakeGateway:
    def __init__(self, agent_key="manus"):
        self.agent_key = agent_key

    async def complete(self, **kwargs):
        return {"text": json.dumps({"title": "Plan", "steps": [
            {"objective": "step one", "agent_key": self.agent_key, "dependencies": [], "expected_output": "one", "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 10, "output_tokens": 10}},
            {"objective": "step two", "agent_key": self.agent_key, "dependencies": [0], "expected_output": "two", "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 10, "output_tokens": 10}},
        ]})}


class FakeStore:
    def __init__(self):
        self.steps = []
        self.plan_steps = []

    async def create(self, **kwargs):
        self.plan_steps = [
            {
                "sequence": index + 1,
                "step_key": f"planning.step.{index + 1}",
                "input": {**step, "agent_key": step.get("agent_key", "manus")},
                "status": "pending",
                "output": None,
            }
            for index, step in enumerate(kwargs["steps"])
        ]
        return await self.get(run_id=kwargs["run_id"])

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

        checkpoints = {}
        async def checkpoint(key, state):
            checkpoints[key] = state
            return {"ok": True}

        result = await runtime.execute(
            AgentRunContext("run-1", "user-1", None, None, None, 0, 3),
            {"prompt": "build a plan"},
            checkpoint,
            asyncio.Event(),
        )
        assert result.output["completed_steps"] == 2
        assert checkpoints["planning.manifest"]["step_count"] == 2
        assert [item["status"] for item in store.steps] == ["running", "succeeded", "running", "succeeded"]
        assert [item["status"] for item in store.plan_steps] == ["succeeded", "succeeded"]
        assert executor.payloads[0]["dependencies"] == []
        assert executor.payloads[1]["dependencies"] == [0]
        assert "Completed dependency results" in executor.payloads[1]["prompt"]
        assert "step one" in executor.payloads[1]["prompt"]
        assert "Expected output: one" in executor.payloads[1]["prompt"]

    asyncio.run(run())


def test_planning_runtime_recovers_rows_when_manifest_checkpoint_is_missing():
    async def run():
        store = FakeStore()
        store.plan_steps = [
            {"sequence": 1, "input": {
                "objective": "step one", "dependencies": [], "expected_output": "one",
                "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 1, "output_tokens": 1},
            }, "status": "pending", "output": None},
            {"sequence": 2, "input": {
                "objective": "step two", "dependencies": [0], "expected_output": "two",
                "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 1, "output_tokens": 1},
            }, "status": "pending", "output": None},
        ]
        executor = FakeExecutor()
        runtime = PlanningAgentRuntime(gateway=FakeGateway(), store=store, step_executor=executor)
        checkpoints = {}
        async def checkpoint(key, state):
            checkpoints[key] = state
            return {"ok": True}
        result = await runtime.execute(
            AgentRunContext("run-recover", "user-1", None, None, None, 0, 3),
            {"prompt": "recover plan"},
            checkpoint,
            asyncio.Event(),
        )
        assert result.output["completed_steps"] == 2
        assert checkpoints["planning.manifest"]["title"] == "recover plan"
        assert len(executor.payloads) == 2
    asyncio.run(run())


def test_planning_runtime_repairs_partial_rows_from_checkpoint_manifest():
    async def run():
        store = FakeStore()
        store.plan_steps = [
            {"sequence": 1, "input": {
                "objective": "step one", "dependencies": [], "expected_output": "one",
                "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 1, "output_tokens": 1},
            }, "status": "pending", "output": None},
        ]
        executor = FakeExecutor()
        runtime = PlanningAgentRuntime(gateway=FakeGateway(), store=store, step_executor=executor)
        async def checkpoint(key, state):
            return {"ok": True}
        recovered_manifest = {
            "title": "Plan",
            "step_count": 2,
            "steps": [
                {"objective": "step one", "dependencies": [], "expected_output": "one", "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 10, "output_tokens": 10}},
                {"objective": "step two", "dependencies": [0], "expected_output": "two", "tool_requirement": "none", "risk": "low", "estimated_usage": {"input_tokens": 10, "output_tokens": 10}},
            ],
        }
        context = AgentRunContext("run-partial", "user-1", None, None, None, 0, 3, recovery_checkpoints={"planning.manifest": recovered_manifest})
        result = await runtime.execute(context, {"prompt": "ignored on recovery"}, checkpoint, asyncio.Event())
        assert result.output["completed_steps"] == 2
        assert len(store.plan_steps) == 2
        assert len(executor.payloads) == 2
    asyncio.run(run())


def test_planning_runtime_dispatches_steps_to_registered_agent_key():
    async def run():
        store = FakeStore()
        default_executor = FakeExecutor()
        research_executor = FakeExecutor()
        runtime = PlanningAgentRuntime(
            gateway=FakeGateway("research"),
            store=store,
            step_executors={"manus": default_executor, "research": research_executor},
            default_executor="manus",
        )
        async def checkpoint(key, state):
            return {"ok": True}
        result = await runtime.execute(
            AgentRunContext("run-agents", "user-1", None, None, None, 0, 3),
            {"prompt": "use research agent"},
            checkpoint,
            asyncio.Event(),
        )
        assert result.output["completed_steps"] == 2
        assert default_executor.payloads == []
        assert [p["agent_key"] for p in research_executor.payloads] == ["research", "research"]
    asyncio.run(run())


def test_planning_runtime_rejects_unregistered_agent_before_plan_persistence():
    async def run():
        store = FakeStore()
        runtime = PlanningAgentRuntime(
            gateway=FakeGateway("not-enabled"),
            store=store,
            step_executor=FakeExecutor(),
        )
        async def checkpoint(key, state):
            return {"ok": True}
        try:
            await runtime.execute(
                AgentRunContext("run-invalid-agent", "user-1", None, None, None, 0, 3),
                {"prompt": "use an unknown agent"},
                checkpoint,
                asyncio.Event(),
            )
        except RuntimeError as exc:
            assert "planning_step_agent_not_registered" in str(exc)
        else:
            raise AssertionError("unregistered agent should fail closed")
        assert store.plan_steps == []
    asyncio.run(run())
