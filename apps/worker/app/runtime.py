from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from app.client import RunPausedForApproval, WorkerRpcClient


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
            await self.rpc.append_run_event(run_id, "worker:run.started", "run.started", {
                "attempt": int(run.get("attempt") or 0),
            })

            async def checkpoint(key: str, state: dict[str, Any]):
                result = await self.rpc.checkpoint(run_id, key, state)
                # Never publish checkpoint bodies: they may contain prompts, tool arguments,
                # observations or credentials. Only bounded, scalar progress metadata is public.
                safe = {"checkpoint_key": key[:160]}
                for field in ("phase", "progress", "rounds", "tool_count", "next_round"):
                    value = state.get(field) if isinstance(state, dict) else None
                    if isinstance(value, (str, int, float, bool)) and not isinstance(value, str) or (
                        isinstance(value, str) and len(value) <= 80
                    ):
                        safe[field] = value
                import hashlib
                event_digest = hashlib.sha256(
                    json.dumps(safe, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()[:16]
                await self.rpc.append_run_event(
                    run_id, f"checkpoint:{key[:150]}:{event_digest}",
                    "run.progress", safe,
                )
                return result

            output = await self.dispatcher.dispatch(run, checkpoint, cancelled)
            if cancelled.is_set():
                await self.rpc.append_run_event(run_id, "worker:run.cancelled", "run.cancelled", {})
                await self.rpc.finish(run_id, "cancelled")
            else:
                await self.rpc.append_run_event(run_id, "worker:run.completed", "run.completed", {})
                await self.rpc.finish(run_id, "succeeded", output=output)
        except RunPausedForApproval:
            # Pause RPC committed the checkpoint and released the lease atomically.
            # Owner decision will enqueue a continuation; do not finish this run.
            pass
        except asyncio.CancelledError:
            # A user-requested cancellation is terminal. A process shutdown is not:
            # leave its lease/checkpoints intact so another worker can recover it.
            if cancelled.is_set():
                await asyncio.shield(self.rpc.append_run_event(run_id, "worker:run.cancelled", "run.cancelled", {}))
                await asyncio.shield(self.rpc.finish(run_id, "cancelled"))
            raise
        except Exception:
            if cancelled.is_set():
                await self.rpc.append_run_event(run_id, "worker:run.cancelled", "run.cancelled", {})
                await self.rpc.finish(run_id, "cancelled")
            else:
                await self.rpc.append_run_event(run_id, "worker:run.failed", "run.failed", {"code": "agent_execution_failed"})
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
