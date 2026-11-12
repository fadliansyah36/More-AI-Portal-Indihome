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
        lease_lost = asyncio.Event()
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(run_id, cancelled, lease_lost))
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

            # Race execution against the durable cancellation signal. The heartbeat
            # sets this event when the API/RPC reports cancel_requested; merely passing
            # the event into the agent is insufficient when a provider/tool call is
            # currently blocked awaiting I/O.
            dispatch_task = asyncio.create_task(
                self.dispatcher.dispatch(run, checkpoint, cancelled),
                name=f"moreai-run-dispatch:{run_id}",
            )
            cancel_wait_task = asyncio.create_task(
                cancelled.wait(), name=f"moreai-run-cancel-watch:{run_id}",
            )
            lease_wait_task = asyncio.create_task(
                lease_lost.wait(), name=f"moreai-run-lease-lost-watch:{run_id}",
            )
            run_timeout_seconds = int(
                getattr(self.rpc.settings, "run_timeout_seconds", 1800)
            )
            if not 30 <= run_timeout_seconds <= 7200:
                raise RuntimeError("worker_run_timeout_configuration_invalid")
            done, _ = await asyncio.wait(
                {dispatch_task, cancel_wait_task, lease_wait_task},
                timeout=run_timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done and not lease_lost.is_set() and not cancelled.is_set():
                # Timeouts are durable failures, not process crashes: stop the
                # current attempt, append an idempotent event and let the database
                # retry policy decide whether another attempt may be claimed.
                dispatch_task.cancel()
                await asyncio.gather(dispatch_task, return_exceptions=True)
                if lease_lost.is_set():
                    return True
                await self.rpc.append_run_event(
                    run_id, "worker:run.timed_out", "run.timed_out",
                    {"timeout_seconds": run_timeout_seconds},
                )
                await self.rpc.finish(
                    run_id, "failed",
                    error={"code": "agent_run_timeout"},
                    retry_delay_seconds=30,
                )
                return True
            if lease_wait_task in done and lease_lost.is_set():
                # A stale worker must never finish or publish against a lease it no
                # longer owns. Stop local execution and let the current lease owner
                # (or the expiry reaper) decide the durable run state.
                cancelled.set()
                dispatch_task.cancel()
                await asyncio.gather(dispatch_task, return_exceptions=True)
                return True
            if cancel_wait_task in done and cancelled.is_set():
                dispatch_task.cancel()
                await asyncio.gather(dispatch_task, return_exceptions=True)
                await self.rpc.append_run_event(
                    run_id, "worker:run.cancelled", "run.cancelled", {},
                )
                await self.rpc.finish(run_id, "cancelled")
                return True

            cancel_wait_task.cancel()
            lease_wait_task.cancel()
            await asyncio.gather(cancel_wait_task, lease_wait_task, return_exceptions=True)
            output = await dispatch_task
            if lease_lost.is_set():
                # The lease may have been lost immediately after dispatch completed.
                # Never race the new owner with a stale terminal write.
                return True
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
            if cancelled.is_set() and not lease_lost.is_set():
                await asyncio.shield(self.rpc.append_run_event(run_id, "worker:run.cancelled", "run.cancelled", {}))
                await asyncio.shield(self.rpc.finish(run_id, "cancelled"))
            raise
        except Exception:
            if lease_lost.is_set():
                # Lease loss is not a user cancellation or execution failure. Leave
                # the durable row untouched for the lease owner/recovery path.
                pass
            elif cancelled.is_set():
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
            # Reap any child tasks if the worker process is shutting down while a
            # provider/tool call is still active. The run lease remains recoverable.
            for task_name in ("dispatch_task", "cancel_wait_task", "lease_wait_task"):
                task = locals().get(task_name)
                if task is not None and not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        return True

    async def _heartbeat_loop(
        self, run_id: str, cancelled: asyncio.Event, lease_lost: asyncio.Event,
    ):
        # Renew well before the configured lease expires. A fixed 30s interval
        # silently loses leases when deployments configure lease_seconds below 90.
        lease_seconds = self.rpc.settings.lease_seconds
        heartbeat_interval = max(1.0, min(30.0, lease_seconds / 3.0))
        while not cancelled.is_set():
            try:
                await asyncio.wait_for(cancelled.wait(), timeout=heartbeat_interval)
            except TimeoutError:
                try:
                    state = await self.rpc.heartbeat(run_id)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # A heartbeat transport failure means ownership cannot be
                    # proven. Fail closed; do not issue finish/event writes on a
                    # potentially stale lease.
                    lease_lost.set()
                    cancelled.set()
                    return
                if not isinstance(state, dict) or not state.get("alive", False):
                    lease_lost.set()
                    cancelled.set()
                    return
                if state.get("cancel_requested", False):
                    cancelled.set()
                    return
