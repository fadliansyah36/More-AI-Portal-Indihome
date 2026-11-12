from __future__ import annotations

import os
from urllib.parse import urlsplit

import httpx


class BrowserSupervisor:
    """Worker-side authenticated client for the isolated browser supervisor service."""

    def __init__(
        self, *, service_url: str, service_token: str, egress_enforced: bool,
        http: httpx.AsyncClient, allow_private_http: bool = False,
    ):
        parsed = urlsplit(service_url)
        private_http = (
            allow_private_http
            and parsed.scheme == "http"
            and parsed.hostname == "browser-supervisor"
            and parsed.port == 8080
            and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment
        )
        secure_https = (
            parsed.scheme == "https" and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment
        )
        if not (secure_https or private_http):
            raise ValueError("browser_supervisor_service_must_use_https_or_explicit_private_compose_http")
        if len(service_token) < 32:
            raise ValueError("browser_supervisor_service_token_invalid")
        if not egress_enforced:
            raise RuntimeError("browser_network_egress_enforcement_required")
        self.service_url = service_url.rstrip("/")
        self.service_token = service_token
        self.http = http

    async def browser_use(self, arguments: dict, *, run_id: str, user_id: str) -> str:
        import json
        url = arguments.get("url")
        action = arguments.get("action")
        parsed = urlsplit(url if isinstance(url, str) else "")
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("browser_url_must_be_https_without_credentials")
        if action not in ("navigate", "extract"):
            raise ValueError("browser_action_not_supported_by_supervisor")
        response = await self.http.post(
            f"{self.service_url}/v1/browser/actions",
            json={"url": url, "action": action, "run_id": run_id, "user_id": user_id},
            headers={"Authorization": f"Bearer {self.service_token}"},
            timeout=httpx.Timeout(45.0, connect=5.0),
        )
        response.raise_for_status()
        payload = response.json()
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
