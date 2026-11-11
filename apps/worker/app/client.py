from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class WorkerSettings:
    supabase_url: str
    service_role_key: str
    worker_id: str
    lease_seconds: int = 90

    def __post_init__(self):
        if not self.supabase_url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        if not 8 <= len(self.worker_id) <= 128:
            raise ValueError("WORKER_ID must contain 8 to 128 characters")
        if not 15 <= self.lease_seconds <= 900:
            raise ValueError("lease_seconds must be between 15 and 900")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")


class WorkerRpcClient:
    """Server-only client for the existing MoreAI worker SECURITY DEFINER RPCs."""

    def __init__(self, settings: WorkerSettings, client: httpx.AsyncClient):
        self.settings = settings
        self.client = client

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.service_role_key,
            "Authorization": f"Bearer {self.settings.service_role_key}",
            "Content-Type": "application/json",
        }

    async def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        response = await self.client.post(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/rpc/{name}",
            json=payload, headers=self._headers(), timeout=15.0,
        )
        response.raise_for_status()
        return response.json()

    async def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self.client.get(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}",
            params=params, headers=self._headers(), timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    async def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}",
            json=payload, headers={**self._headers(), "Prefer": "return=representation"}, timeout=15.0,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise RuntimeError("Supabase insert returned no record")
        return rows[0]

    async def update(self, table: str, params: dict[str, str], payload: dict[str, Any]) -> list[dict[str, Any]]:
        response = await self.client.patch(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}",
            params=params, json=payload,
            headers={**self._headers(), "Prefer": "return=representation"}, timeout=15.0,
        )
        response.raise_for_status()
        return response.json() if response.content else []

    async def list_checkpoints(self, run_id: str) -> dict[str, dict[str, Any]]:
        rows = await self.select("agent_run_checkpoints", {
            "run_id": f"eq.{run_id}",
            "select": "checkpoint_key,state,created_at",
            "order": "created_at.asc",
            "limit": "1000",
        })
        restored: dict[str, dict[str, Any]] = {}
        for row in rows:
            key, state = row.get("checkpoint_key"), row.get("state")
            if isinstance(key, str) and isinstance(state, dict):
                restored[key] = state
        return restored

    async def append_run_event(
        self, run_id: str, event_key: str, event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = await self.rpc("moreai_worker_append_run_event", {
            "p_run_id": run_id,
            "p_event_key": event_key,
            "p_event_type": event_type,
            "p_payload": payload or {},
        })
        if not isinstance(result, dict) or not isinstance(result.get("sequence"), int):
            raise RuntimeError("durable_run_event_append_failed")
        return result

    async def claim_event_outbox(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = await self.rpc("moreai_worker_claim_event_outbox", {
            "p_worker_id": self.settings.worker_id,
            "p_limit": max(1, min(100, limit)),
            "p_lease_seconds": 45,
        })
        return rows if isinstance(rows, list) else []

    async def ack_event_outbox(self, event_id: str) -> bool:
        result = await self.rpc("moreai_worker_ack_event_outbox", {
            "p_event_id": event_id, "p_worker_id": self.settings.worker_id,
        })
        return result is True

    async def retry_event_outbox(self, event_id: str, error_code: str) -> str:
        result = await self.rpc("moreai_worker_retry_event_outbox", {
            "p_event_id": event_id, "p_worker_id": self.settings.worker_id,
            "p_error_code": error_code[:80],
        })
        if result not in {"pending", "dead_letter"}:
            raise RuntimeError("outbox_retry_state_invalid")
        return result

    async def publish_run_event(self, event: dict[str, Any]) -> None:
        run_id = event.get("run_id")
        event_id = event.get("event_id")
        sequence = event.get("sequence")
        if not isinstance(run_id, str) or not isinstance(event_id, str) or not isinstance(sequence, int):
            raise ValueError("outbox_event_identity_invalid")
        response = await self.client.post(
            f"{self.settings.supabase_url.rstrip('/')}/realtime/v1/api/broadcast",
            headers=self._headers(),
            json={"messages": [{
                "topic": f"run:{run_id}",
                "event": "run.event",
                "payload": {
                    "event_id": event_id,
                    "run_id": run_id,
                    "sequence": sequence,
                    "type": event.get("event_type"),
                    "payload": event.get("payload") or {},
                    "created_at": event.get("created_at"),
                },
                "private": True,
            }]},
            timeout=10.0,
        )
        response.raise_for_status()

    async def claim_run(self) -> dict[str, Any] | None:
        return await self.rpc("moreai_worker_claim_run", {
            "p_worker_id": self.settings.worker_id,
            "p_lease_seconds": self.settings.lease_seconds,
        })

    async def heartbeat(self, run_id: str) -> dict[str, Any]:
        return await self.rpc("moreai_worker_heartbeat", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_lease_seconds": self.settings.lease_seconds,
        })

    async def checkpoint(self, run_id: str, key: str, state: dict[str, Any]) -> dict[str, Any]:
        return await self.rpc("moreai_worker_checkpoint", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_checkpoint_key": key, "p_state": state,
        })

    async def wait_for_tool_approval(
        self, run_id: str, user_id: str, tool_key: str, arguments: dict[str, Any],
    ) -> bool:
        """Pause execution until an owner decision, then atomically consume one approval."""
        arguments_hash = hashlib.sha256(
            json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        approval_id = await self.rpc("moreai_request_tool_approval", {
            "p_run_id": run_id,
            "p_user_id": user_id,
            "p_tool_key": tool_key,
            "p_arguments_hash": arguments_hash,
            "p_summary": f"Approval required for isolated {tool_key} execution",
            "p_expires_in_seconds": 900,
        })
        if isinstance(approval_id, dict):
            approval_id = approval_id.get("id")
        if not isinstance(approval_id, str) or not approval_id:
            raise RuntimeError("tool_approval_request_failed")

        for _ in range(450):
            rows = await self.select("agent_tool_approvals", {
                "id": f"eq.{approval_id}",
                "run_id": f"eq.{run_id}",
                "user_id": f"eq.{user_id}",
                "select": "id,status,expires_at",
                "limit": "1",
            })
            if not rows:
                raise RuntimeError("tool_approval_record_missing")
            status = rows[0].get("status")
            if status == "approved":
                consumed = await self.rpc("moreai_consume_tool_approval", {
                    "p_run_id": run_id,
                    "p_user_id": user_id,
                    "p_tool_key": tool_key,
                    "p_arguments_hash": arguments_hash,
                })
                return bool(consumed)
            if status in {"denied", "expired", "consumed"}:
                return False
            if status != "pending":
                raise RuntimeError("tool_approval_state_invalid")
            lease = await self.heartbeat(run_id)
            if lease.get("cancel_requested"):
                raise asyncio.CancelledError()
            if not lease.get("alive", False):
                raise RuntimeError("worker_lease_lost_while_waiting_for_approval")
            await asyncio.sleep(2)
        return False

    async def finish(
        self, run_id: str, status: str, output: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None, retry_delay_seconds: int = 30,
    ) -> dict[str, Any]:
        if status not in {"succeeded", "failed", "cancelled"}:
            raise ValueError("Only terminal run statuses can be submitted")
        return await self.rpc("moreai_worker_finish_run", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_status": status, "p_output": output, "p_error": error,
            "p_retry_delay_seconds": retry_delay_seconds,
        })
