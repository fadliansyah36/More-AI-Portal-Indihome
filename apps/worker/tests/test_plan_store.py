import asyncio

from app.plan_store import SupabasePlanStore


class FakeClient:
    def __init__(self):
        self.rows = []
        self.checkpoints = []
    async def checkpoint(self, run_id, key, state):
        self.checkpoints.append((run_id, key, state))
        return {"ok": True}
    async def select(self, table, params):
        if table != "agent_run_steps":
            return []
        return self.rows
    async def insert(self, table, payload):
        row = dict(payload)
        self.rows.append(row)
        return row
    async def update(self, table, params, payload):
        row = next((x for x in self.rows if x["run_id"] == params["run_id"][3:] and x["sequence"] == int(params["sequence"][3:])), None)
        if row:
            row.update(payload)
            return [row]
        return []


def test_plan_store_persists_steps_and_valid_statuses():
    async def run():
        client = FakeClient()
        store = SupabasePlanStore(client)
        created = await store.create(run_id="run-1", title="A plan", steps=[{"objective": "one", "dependencies": [], "expected_output": "a", "tool_requirement": "none", "risk": "low", "estimated_usage": {}}, {"objective": "two", "dependencies": [0], "expected_output": "b", "tool_requirement": "none", "risk": "low", "estimated_usage": {}}])
        assert len(created["steps"]) == 2
        assert [x["status"] for x in client.rows] == ["pending", "pending"]
        updated = await store.mark_step(run_id="run-1", step_index=0, status="running")
        assert updated["status"] == "running"
    asyncio.run(run())
