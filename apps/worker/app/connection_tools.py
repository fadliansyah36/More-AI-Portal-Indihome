from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx


class GoogleConnectionTools:
    """Google Workspace tools delegated through FastAPI; writes are gated by durable run approval."""

    def __init__(self, http: httpx.AsyncClient, api_url: str, worker_token: str):
        self.http = http
        self.api_url = api_url.rstrip("/")
        self.worker_token = worker_token

    async def _request(self, path: str, arguments: dict[str, Any], *, run_id: str, user_id: str, idempotency_key: str | None = None) -> str:
        response = await self.http.post(
            self.api_url + path,
            headers={"X-MoreAI-Worker-Token": self.worker_token, "Accept": "application/json", **({"Idempotency-Key": idempotency_key} if idempotency_key else {})},
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


    async def gmail_send(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        recipients = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")
        if (not isinstance(recipients, list) or not 1 <= len(recipients) <= 5
            or any(not isinstance(item, str) for item in recipients)
            or not isinstance(subject, str) or not 1 <= len(subject) <= 240
            or not isinstance(body, str) or not 1 <= len(body) <= 20000):
            raise ValueError("gmail_send_arguments_invalid")
        payload = {"to": recipients, "subject": subject, "body": body}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
        key = f"{run_id}:gmail.send:{digest}"[:128]
        return await self._request("/api/v1/customer/connections/internal/google/gmail/send",
            payload, run_id=run_id, user_id=user_id, idempotency_key=key)

    async def calendar_create_event(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        summary = arguments.get("summary")
        start = arguments.get("start")
        end = arguments.get("end")
        description = arguments.get("description", "")
        timezone_name = arguments.get("timezone", "Asia/Jakarta")
        if (not isinstance(summary, str) or not 1 <= len(summary) <= 240
            or not isinstance(start, str) or not isinstance(end, str)
            or not isinstance(description, str) or len(description) > 4000
            or not isinstance(timezone_name, str) or len(timezone_name) > 64):
            raise ValueError("calendar_create_arguments_invalid")
        payload = {"summary": summary, "start": start, "end": end,
            "description": description, "timezone": timezone_name}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
        key = f"{run_id}:calendar.create:{digest}"[:128]
        return await self._request("/api/v1/customer/connections/internal/google/calendar/create",
            payload, run_id=run_id, user_id=user_id, idempotency_key=key)


    async def calendar_update_event(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        connection_id = arguments.get("connection_id")
        event_id = arguments.get("event_id")
        etag = arguments.get("etag")
        if (not isinstance(connection_id, str) or not connection_id
            or not isinstance(event_id, str) or not 1 <= len(event_id) <= 256
            or not isinstance(etag, str) or not 1 <= len(etag) <= 256):
            raise ValueError("calendar_update_arguments_invalid")
        payload: dict[str, Any] = {"connection_id": connection_id, "event_id": event_id, "etag": etag}
        for key, maximum in (("summary", 240), ("description", 4000), ("start", 64), ("end", 64), ("timezone", 64)):
            value = arguments.get(key)
            if value is not None:
                if not isinstance(value, str) or len(value) > maximum:
                    raise ValueError("calendar_update_arguments_invalid")
                payload[key] = value
        if not any(key in payload for key in ("summary", "description", "start", "end")):
            raise ValueError("calendar_update_empty")
        if ("start" in payload) != ("end" in payload):
            raise ValueError("calendar_update_time_pair_required")
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
        key = f"{run_id}:calendar.update:{digest}"[:128]
        return await self._request("/api/v1/customer/connections/internal/google/calendar/update",
            payload, run_id=run_id, user_id=user_id, idempotency_key=key)

    async def calendar_delete_event(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        connection_id = arguments.get("connection_id")
        event_id = arguments.get("event_id")
        etag = arguments.get("etag")
        if (not isinstance(connection_id, str) or not connection_id
            or not isinstance(event_id, str) or not 1 <= len(event_id) <= 256
            or not isinstance(etag, str) or not 1 <= len(etag) <= 256):
            raise ValueError("calendar_delete_arguments_invalid")
        payload = {"connection_id": connection_id, "event_id": event_id, "etag": etag}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:24]
        key = f"{run_id}:calendar.delete:{digest}"[:128]
        return await self._request("/api/v1/customer/connections/internal/google/calendar/delete",
            payload, run_id=run_id, user_id=user_id, idempotency_key=key)
