from __future__ import annotations

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
