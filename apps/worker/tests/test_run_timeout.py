import asyncio
from types import SimpleNamespace

import pytest

from app.runtime import WorkerRuntime


class FakeRpc:
    def __init__(self):
        self.settings = SimpleNamespace(lease_seconds=90, run_timeout_seconds=30)
        self.events = []
        self.finished = []

    async def claim_run(self):
        return {"id": "run-timeout", "attempt": 1}

    async def append_run_event(self, run_id, event_key, event_type, payload=None):
        self.events.append((run_id, event_key, event_type, payload or {}))
        return {"sequence": len(self.events)}

    async def finish(self, run_id, status, **kwargs):
        self.finished.append((run_id, status, kwargs))
        return {"status": status}

    async def heartbeat(self, run_id):
        return {"alive": True, "cancel_requested": False}


class HangingDispatcher:
    def __init__(self):
        self.cancelled = False

    async def dispatch(self, run, checkpoint, cancelled):
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


@pytest.mark.asyncio
async def test_run_timeout_cancels_dispatch_and_records_retryable_failure(monkeypatch):
    rpc = FakeRpc()
    dispatcher = HangingDispatcher()
    runtime = WorkerRuntime(rpc, dispatcher)
    original_wait = asyncio.wait

    async def fast_wait(tasks, *, timeout=None, return_when=asyncio.ALL_COMPLETED):
        # Keep this test deterministic and fast while asserting the configured
        # production timeout is passed to the asyncio lifecycle race.
        assert timeout == 30
        return await original_wait(tasks, timeout=0.02, return_when=return_when)

    monkeypatch.setattr("app.runtime.asyncio.wait", fast_wait)

    assert await runtime.run_once() is True
    assert dispatcher.cancelled is True
    assert any(event[2] == "run.timed_out" for event in rpc.events)
    assert rpc.finished == [
        ("run-timeout", "failed", {
            "error": {"code": "agent_run_timeout"},
            "retry_delay_seconds": 30,
        })
    ]


def test_worker_timeout_configuration_is_bounded():
    from app.client import WorkerSettings

    with pytest.raises(ValueError, match="run_timeout_seconds"):
        WorkerSettings(
            supabase_url="https://project.supabase.co",
            service_role_key="server-only",
            worker_id="worker-timeout-01",
            run_timeout_seconds=7201,
        )
