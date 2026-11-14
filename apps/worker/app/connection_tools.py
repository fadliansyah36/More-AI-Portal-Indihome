from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


class GoogleConnectionTools:
    """Read-only Google Workspace tools delegated through the FastAPI trust boundary."""

    def __init__(self, http: httpx.AsyncClient, api_url: str, worker_token: str):
        self.http = http
        self.api_url = api_url.rstrip("/")
        self.worker_token = worker_token

    async def _request(self, path: str, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        response = await self.http.post(
            self.api_url + path,
            headers={"X-MoreAI-Worker-Token": self.worker_token, "Accept": "application/json"},
            json={"user_id": user_id, "run_id": run_id, **arguments},
            timeout=30.0,
            follow_redirects=False,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("google_connection_tool_response_invalid")
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    async def gmail_search(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        query = arguments.get("query", "newer_than:30d")
        limit = arguments.get("limit", 20)
        if not isinstance(query, str) or len(query) > 500 or not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 30:
            raise ValueError("gmail_search_arguments_invalid")
        return await self._request("/api/v1/customer/connections/internal/google/gmail/search",
            {"query": query, "limit": limit}, run_id=run_id, user_id=user_id)

    async def calendar_list_events(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        start = arguments.get("time_min", now.isoformat())
        end = arguments.get("time_max", (now + timedelta(days=30)).isoformat())
        limit = arguments.get("limit", 30)
        if not isinstance(start, str) or not isinstance(end, str) or not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
            raise ValueError("calendar_list_arguments_invalid")
        return await self._request("/api/v1/customer/connections/internal/google/calendar/list",
            {"time_min": start, "time_max": end, "limit": limit}, run_id=run_id, user_id=user_id)
