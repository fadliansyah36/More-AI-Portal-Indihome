from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException


class SupabaseRepository:
    """Privileged PostgREST adapter. Every user-owned query is explicitly owner-scoped."""

    def __init__(self, *, url: str, service_role_key: str, http: httpx.AsyncClient):
        if not url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        if not service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")
        self.url = url.rstrip("/")
        self.key = service_role_key
        self.http = http

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def count(self, table: str, params: dict[str, str]) -> int:
        """Return an exact count for the caller's filtered PostgREST query."""
        count_params = {key: value for key, value in params.items() if key not in {"limit", "offset", "select"}}
        count_params["select"] = "id"
        headers = self._headers("count=exact")
        headers["Range"] = "0-0"
        response = await self.http.head(
            f"{self.url}/rest/v1/{table}", params=count_params, headers=headers, timeout=12.0,
        )
        if response.status_code >= 500:
            raise HTTPException(503, "Database service unavailable")
        if response.status_code >= 400:
            raise HTTPException(502, "Database count query failed")
        content_range = response.headers.get("content-range", "")
        total = content_range.rsplit("/", 1)[-1] if "/" in content_range else ""
        if not total.isdigit():
            raise HTTPException(502, "Database did not return an exact count")
        return int(total)

    async def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self.http.get(f"{self.url}/rest/v1/{table}", params=params, headers=self._headers(), timeout=12.0)
        if response.status_code >= 500:
            raise HTTPException(503, "Database service unavailable")
        if response.status_code >= 400:
            raise HTTPException(502, "Database query failed")
        data = response.json()
        return data if isinstance(data, list) else []

    async def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.http.post(f"{self.url}/rest/v1/{table}", json=payload, headers=self._headers("return=representation"), timeout=12.0)
        if response.status_code >= 500:
            raise HTTPException(503, "Database service unavailable")
        if response.status_code >= 400:
            raise HTTPException(409 if response.status_code == 409 else 422, "Database mutation rejected")
        rows = response.json()
        if not rows:
            raise HTTPException(502, "Database did not return the created record")
        return rows[0]

    async def update(self, table: str, params: dict[str, str], payload: dict[str, Any]) -> list[dict[str, Any]]:
        response = await self.http.patch(f"{self.url}/rest/v1/{table}", params=params, json=payload, headers=self._headers("return=representation"), timeout=12.0)
        if response.status_code >= 400:
            raise HTTPException(502, "Database update failed")
        return response.json() if response.content else []

    async def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        response = await self.http.post(f"{self.url}/rest/v1/rpc/{name}", json=payload, headers=self._headers(), timeout=12.0)
        if response.status_code >= 500:
            raise HTTPException(503, "Database RPC unavailable")
        if response.status_code >= 400:
            raise HTTPException(409, "Database operation was rejected")
        return response.json()

    async def owned_record(self, table: str, record_id: UUID | str, user_id: str) -> dict[str, Any]:
        rows = await self.select(table, {"id": f"eq.{record_id}", "user_id": f"eq.{user_id}", "select": "*", "limit": "1"})
        if not rows:
            raise HTTPException(404, "Resource not found")
        return rows[0]

    async def delete(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        """Delete only records selected by explicit caller-supplied ownership filters."""
        response = await self.http.delete(
            f"{self.url}/rest/v1/{table}", params=params,
            headers=self._headers("return=representation"), timeout=12.0,
        )
        if response.status_code >= 500:
            raise HTTPException(503, "Database service unavailable")
        if response.status_code >= 400:
            raise HTTPException(502, "Database deletion failed")
        return response.json() if response.content else []
