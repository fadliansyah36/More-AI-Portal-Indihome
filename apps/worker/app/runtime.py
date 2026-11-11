from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from app.client import WorkerRpcClient


Checkpoint = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


class AgentDispatcher(Protocol):
    async def dispatch(
        self, run: dict[str, Any], checkpoint: Checkpoint, cancelled: asyncio.Event,
    ) -> dict[str, Any]: ...


class WorkerRuntime:
    """Durable lifecycle coordinator; interrupted leases are left recoverable."""

    def __init__(self, rpc: WorkerRpcClient, dispatcher: AgentDispatcher):
        if dispatcher is None:
            raise ValueError("A production AgentDispatcher must be registered before claiming runs")
        self.rpc = rpc
        self.dispatcher = dispatcher

    async def run_once(self) -> bool:
        run = await self.rpc.claim_run()
        if not run:
            return False

        run_id = str(run["id"])
        cancelled = asyncio.Event()
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(run_id, cancelled))
        try:
            async def checkpoint(key: str, state: dict[str, Any]):
                return await self.rpc.checkpoint(run_id, key, state)

            output = await self.dispatcher.dispatch(run, checkpoint, cancelled)
            if cancelled.is_set():
                await self.rpc.finish(run_id, "cancelled")
            else:
                await self.rpc.finish(run_id, "succeeded", output=output)
        except asyncio.CancelledError:
            # A user-requested cancellation is terminal. A process shutdown is not:
            # leave its lease/checkpoints intact so another worker can recover it.
            if cancelled.is_set():
                await asyncio.shield(self.rpc.finish(run_id, "cancelled"))
            raise
        except Exception:
            if cancelled.is_set():
                await self.rpc.finish(run_id, "cancelled")
            else:
                await self.rpc.finish(
                    run_id, "failed", error={"code": "agent_execution_failed"},
                    retry_delay_seconds=30,
                )
        finally:
            cancelled.set()
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        return True

    async def _heartbeat_loop(self, run_id: str, cancelled: asyncio.Event):
        while not cancelled.is_set():
            try:
                await asyncio.wait_for(cancelled.wait(), timeout=30)
            except TimeoutError:
                state = await self.rpc.heartbeat(run_id)
                if not state.get("alive", False) or state.get("cancel_requested", False):
                    cancelled.set()
                    return
