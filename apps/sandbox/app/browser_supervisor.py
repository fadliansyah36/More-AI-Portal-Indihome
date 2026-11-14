from __future__ import annotations

import os
import base64
from urllib.parse import urlsplit

import httpx


class BrowserSupervisor:
    """Worker-side authenticated client for the isolated browser supervisor service."""

    def __init__(
        self, *, service_url: str, service_token: str, egress_enforced: bool,
        http: httpx.AsyncClient, allow_private_http: bool = False,
        api_url: str = "", internal_token: str = "",
    ):
        parsed = urlsplit(service_url)
        private_http = (
            allow_private_http
            and parsed.scheme == "http"
            and parsed.hostname == "browser-supervisor"
            and parsed.port == 8080
            and not parsed.username and not parsed.password
            and parsed.path in ("", "/")
            and not parsed.query and not parsed.fragment
        )
        secure_https = (
            parsed.scheme == "https" and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and parsed.path in ("", "/")
            and parsed.port in (None, 443)
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
        self.api_url = api_url.rstrip("/")
        self.internal_token = internal_token
        if len(internal_token) < 32 or not self.api_url.startswith(("https://", "http://api:8000")):
            raise ValueError("browser_session_api_internal_auth_required")

    async def check_ready(self) -> dict:
        response = await self.http.get(
            f"{self.service_url}/ready",
            headers={"Authorization": f"Bearer {self.service_token}"},
            timeout=httpx.Timeout(5.0, connect=2.0),
        )
        response.raise_for_status()
        payload = response.json()
        if (
            not isinstance(payload, dict)
            or payload.get("status") != "ready"
            or payload.get("egress_enforced") is not True
            or payload.get("proxy_configured") is not True
            or payload.get("proxy_reachable") is not True
        ):
            raise RuntimeError("browser_supervisor_egress_readiness_failed")
        return payload

    async def browser_use(self, arguments: dict, *, run_id: str, user_id: str) -> str:
        import json
        url = arguments.get("url")
        action = arguments.get("action")
        parsed = urlsplit(url if isinstance(url, str) else "")
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("browser_url_must_be_https_without_credentials")
        if action not in ("navigate", "extract"):
            raise ValueError("browser_action_not_supported_by_supervisor")
        headers = {"X-MoreAI-Worker-Token": self.internal_token}
        acquired = await self.http.post(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/acquire",
            json={"run_id": run_id, "user_id": user_id, "session_id": arguments.get("session_id"),
                  "origin_host": parsed.hostname.lower()},
            headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
        )
        acquired.raise_for_status()
        session = acquired.json()
        session_id = session.get("session_id")
        storage_state = session.get("storage_state", {})
        if not isinstance(session_id, str) or not isinstance(storage_state, dict):
            raise RuntimeError("browser_session_restore_contract_invalid")
        response = await self.http.post(
            f"{self.service_url}/v1/browser/actions",
            json={"url": url, "action": action, "run_id": run_id, "user_id": user_id,
                  "storage_state": storage_state},
            headers={"Authorization": f"Bearer {self.service_token}"},
            timeout=httpx.Timeout(45.0, connect=5.0),
        )
        response.raise_for_status()
        payload = response.json()
        updated_state = payload.pop("storage_state", None)
        downloads = payload.pop("downloads", [])
        if not isinstance(downloads, list): raise RuntimeError("browser_download_contract_invalid")
        stored_downloads = []
        for item in downloads:
            if not isinstance(item, dict) or item.get("scan_status") != "clean": raise RuntimeError("browser_download_not_scanner_approved")
            try: content = base64.b64decode(item["content_base64"], validate=True)
            except Exception as exc: raise RuntimeError("browser_download_payload_invalid") from exc
            uploaded = await self.http.post(
                f"{self.api_url}/api/v1/artifacts/internal/browser-download", content=content,
                headers={**headers, "Content-Type": "application/octet-stream", "X-Agent-Run-Id": run_id,
                    "X-Owner-User-Id": user_id, "X-Filename": str(item.get("filename") or "download"),
                    "X-Declared-Mime": str(item.get("mime_type") or ""),
                    "X-Declared-SHA256": str(item.get("checksum_sha256") or ""), "X-Scanner-Status": "clean"},
                timeout=httpx.Timeout(35.0, connect=5.0))
            uploaded.raise_for_status()
            stored_downloads.append(uploaded.json())
        if not isinstance(updated_state, dict):
            raise RuntimeError("browser_session_state_missing_from_supervisor")
        saved = await self.http.put(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/{session_id}/state",
            json={"run_id": run_id, "user_id": user_id, "storage_state": updated_state},
            headers=headers, timeout=httpx.Timeout(12.0, connect=3.0),
        )
        saved.raise_for_status()
        payload["downloads"] = stored_downloads
        payload["session_id"] = session_id
        payload["session_persistence"] = "saved"
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
