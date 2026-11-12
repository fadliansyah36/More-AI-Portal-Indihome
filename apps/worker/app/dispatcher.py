from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.runtime import AgentDispatcher, Checkpoint
from app.client import RunPausedForApproval
from engine.agents.errors import AgentExecutionError, classify_agent_exception
from engine.agents.protocol import AgentRunContext
from engine.orchestration.registry import AgentRegistry


CheckpointLoader = Callable[[str], Awaitable[dict[str, dict[str, Any]]]]


class RegisteredAgentDispatcher(AgentDispatcher):
    """Dispatch durable runs and enforce execution-supervisor readiness at the boundary."""

    def __init__(
        self,
        registry: AgentRegistry,
        checkpoint_loader: CheckpointLoader | None = None,
        sandbox_supervisor: Any | None = None,
    ):
        self.registry = registry
        self.checkpoint_loader = checkpoint_loader
        self.sandbox_supervisor = sandbox_supervisor

    async def dispatch(
        self, run: dict[str, Any], checkpoint: Checkpoint, cancelled: asyncio.Event,
    ) -> dict[str, Any]:
        run_id = str(run.get("id") or "")
        user_id = str(run.get("user_id") or "")
        payload = run.get("input") or {}
        if not run_id or not user_id or not isinstance(payload, dict):
            raise ValueError("invalid_durable_run_payload")
        if cancelled.is_set():
            raise asyncio.CancelledError()
        agent_key = payload.get("agent_key", "manus")
        if not isinstance(agent_key, str):
            raise ValueError("invalid_agent_key")
        runtime = self.registry.resolve(agent_key)
        # SWE is never dispatched without a separately deployed, authenticated
        # sandbox supervisor. The tool adapter repeats readiness before each
        # invocation so a supervisor outage cannot silently fall back to host exec.
        if agent_key == "swe":
            if self.sandbox_supervisor is None:
                raise PermissionError("isolated_sandbox_supervisor_required")
            await self.sandbox_supervisor.check_ready()
        restored = await self.checkpoint_loader(run_id) if self.checkpoint_loader else {}
        if not isinstance(restored, dict):
            raise RuntimeError("run_checkpoint_restore_failed")
        context = AgentRunContext(
            run_id=run_id,
            user_id=user_id,
            workspace_id=str(run["workspace_id"]) if run.get("workspace_id") else None,
            conversation_id=str(run["conversation_id"]) if run.get("conversation_id") else None,
            agent_definition_id=str(run["agent_definition_id"]) if run.get("agent_definition_id") else None,
            attempt=int(run.get("attempt") or 0),
            max_attempts=int(run.get("max_attempts") or 3),
            recovery_checkpoints=restored,
        )
        if cancelled.is_set():
            raise asyncio.CancelledError()
        try:
            result = await runtime.execute(context, payload, checkpoint, cancelled)
        except (asyncio.CancelledError, RunPausedForApproval):
            # Approval pauses are durable control flow, not agent failures.
            raise
        except httpx.TimeoutException as exc:
            raise AgentExecutionError("upstream_timeout", retryable=True) from exc
        except httpx.TransportError as exc:
            raise AgentExecutionError("upstream_unavailable", retryable=True) from exc
        except httpx.HTTPStatusError as exc:
            retryable = exc.response.status_code >= 500 or exc.response.status_code == 429
            raise AgentExecutionError(
                "upstream_rejected_request" if not retryable else "upstream_service_error",
                retryable=retryable,
            ) from exc
        except Exception as exc:
            classified = classify_agent_exception(exc)
            if classified is exc:
                raise
            raise classified from exc
        return result.output
