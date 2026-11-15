from __future__ import annotations

import asyncio
import hashlib
import json
from urllib.parse import quote, urlsplit

import httpx


class BrowserSupervisor:
    """Authenticated adapter for the pinned OpenFuse persistent Chromium worker API."""

    def __init__(
        self, *, service_url: str, service_token: str, egress_enforced: bool,
        http: httpx.AsyncClient, allow_private_http: bool = False,
        api_url: str = "", internal_token: str = "",
    ):
        parsed = urlsplit(service_url)
        private_http = (
            allow_private_http
            and parsed.scheme == "http"
            and parsed.hostname in {"browser-supervisor", "browser-worker", "openfuse-browser"}
            and parsed.port in {8080, 8790}
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

    def _worker_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.service_token}"}

    def _internal_headers(self) -> dict[str, str]:
        return {"X-MoreAI-Worker-Token": self.internal_token}

    async def check_ready(self) -> dict:
        # This is the actual OpenFuse worker health contract: /health is public
        # process health, while authenticated /sessions confirms worker auth/API.
        health = await self.http.get(
            f"{self.service_url}/health",
            timeout=httpx.Timeout(5.0, connect=2.0),
        )
        health.raise_for_status()
        payload = health.json()
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            raise RuntimeError("openfuse_browser_worker_health_contract_invalid")
        sessions = await self.http.get(
            f"{self.service_url}/sessions",
            headers=self._worker_headers(),
            timeout=httpx.Timeout(5.0, connect=2.0),
        )
        sessions.raise_for_status()
        if not isinstance(sessions.json(), list):
            raise RuntimeError("openfuse_browser_worker_sessions_contract_invalid")
        return {"status": "ready", "egress_enforced": True, "session_api": "openfuse-v1"}

    async def _finish_receipt(
        self, *, receipt_id: str, run_id: str, user_id: str,
        status: str, session_id: str | None = None,
        result: dict | None = None, error_code: str | None = None,
    ) -> None:
        response = await self.http.post(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/actions/{receipt_id}/finish",
            json={
                "run_id": run_id, "user_id": user_id, "status": status,
                "session_id": session_id, "result": result, "error_code": error_code,
            },
            headers=self._internal_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        response.raise_for_status()

    async def _ensure_session(self, session_id: str, url: str) -> tuple[dict, bool]:
        response = await self.http.get(
            f"{self.service_url}/sessions",
            headers=self._worker_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        response.raise_for_status()
        sessions = response.json()
        if not isinstance(sessions, list):
            raise RuntimeError("openfuse_browser_sessions_response_invalid")
        current = next((item for item in sessions if isinstance(item, dict) and item.get("id") == session_id), None)
        if current and current.get("status") == "active":
            return current, False
        opened = await self.http.post(
            f"{self.service_url}/sessions",
            json={"id": session_id, "url": url},
            headers={**self._worker_headers(), "Content-Type": "application/json"},
            timeout=httpx.Timeout(45.0, connect=5.0),
        )
        opened.raise_for_status()
        value = opened.json()
        if not isinstance(value, dict) or value.get("id") != session_id:
            raise RuntimeError("openfuse_browser_session_open_contract_invalid")
        return value, True

    async def _session_request(self, session_id: str, action: str, *, body: dict | None = None) -> httpx.Response:
        url = f"{self.service_url}/sessions/{quote(session_id, safe='')}/{action}"
        response = await self.http.request(
            "POST" if body is not None else "GET",
            url,
            json=body,
            headers={**self._worker_headers(), **({"Content-Type": "application/json"} if body is not None else {})},
            timeout=httpx.Timeout(45.0, connect=5.0),
        )
        response.raise_for_status()
        return response

    async def close_session(self, session_id: str) -> None:
        sessions = await self.http.get(
            f"{self.service_url}/sessions",
            headers=self._worker_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        sessions.raise_for_status()
        payload = sessions.json()
        if not isinstance(payload, list):
            raise RuntimeError("openfuse_browser_sessions_response_invalid")
        current = next((item for item in payload if isinstance(item, dict) and item.get("id") == session_id), None)
        if current and current.get("status") == "active":
            await self._session_request(session_id, "close", body={})

    async def browser_use(
        self, arguments: dict, *, run_id: str, user_id: str,
        tool_call_id: str | None = None,
    ) -> str:
        url = arguments.get("url")
        action = arguments.get("action")
        parsed = urlsplit(url if isinstance(url, str) else "")
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("browser_url_must_be_https_without_credentials")
        if action not in ("navigate", "extract", "input", "screenshot", "close", "downloads"):
            raise ValueError("browser_action_not_supported_by_openfuse_worker")
        if action in {"input", "close", "downloads"} and not arguments.get("session_id"):
            raise ValueError("browser_action_requires_existing_session_id")
        if action == "input" and not isinstance(arguments.get("input"), dict):
            raise ValueError("browser_input_payload_required")

        canonical = json.dumps(arguments, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        request_hash = hashlib.sha256(canonical.encode()).hexdigest()
        action_identity = tool_call_id if isinstance(tool_call_id, str) and tool_call_id else request_hash
        action_key = hashlib.sha256(f"{run_id}:{action_identity}".encode()).hexdigest()
        claim = await self.http.post(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/actions/claim",
            json={
                "run_id": run_id, "user_id": user_id, "action_key": action_key,
                "request_hash": request_hash, "action_type": action,
                "target_host": parsed.hostname.lower(),
            },
            headers=self._internal_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        claim.raise_for_status()
        receipt = claim.json()
        receipt_id = receipt.get("receipt_id")
        if not isinstance(receipt_id, str):
            raise RuntimeError("browser_action_receipt_claim_invalid")
        if receipt.get("can_execute") is not True:
            if receipt.get("status") == "succeeded" and isinstance(receipt.get("result"), dict):
                return json.dumps(receipt["result"], ensure_ascii=False, separators=(",", ":"))
            raise RuntimeError("browser_action_replay_blocked_by_receipt_" + str(receipt.get("status") or "unknown"))

        session_id: str | None = None
        action_submitted = False
        try:
            acquired = await self.http.post(
                f"{self.api_url}/api/v1/customer/browser-sessions/internal/acquire",
                json={
                    "run_id": run_id, "user_id": user_id,
                    "session_id": arguments.get("session_id"),
                    "origin_host": parsed.hostname.lower(),
                },
                headers=self._internal_headers(),
                timeout=httpx.Timeout(12.0, connect=3.0),
            )
            acquired.raise_for_status()
            session = acquired.json()
            session_id = session.get("session_id")
            if not isinstance(session_id, str):
                raise RuntimeError("browser_session_acquire_contract_invalid")

            if action == "close":
                sessions_response = await self.http.get(
                    f"{self.service_url}/sessions", headers=self._worker_headers(),
                    timeout=httpx.Timeout(12.0, connect=3.0),
                )
                sessions_response.raise_for_status()
                known = sessions_response.json()
                current = next((item for item in known if isinstance(item, dict) and item.get("id") == session_id), None) if isinstance(known, list) else None
                if current and current.get("status") == "active":
                    action_submitted = True
                    closed = await self._session_request(session_id, "close", body={})
                    output = closed.json()
                else:
                    output = {"id": session_id, "status": "closed", "already_closed": True}
                marked = await self.http.post(
                    f"{self.api_url}/api/v1/customer/browser-sessions/internal/{session_id}/closed",
                    json={"run_id": run_id, "user_id": user_id},
                    headers=self._internal_headers(),
                    timeout=httpx.Timeout(12.0, connect=3.0),
                )
                marked.raise_for_status()
                result = {"action": "close", "session_id": session_id, "status": "closed"}
            elif action == "downloads":
                response = await self._session_request(session_id, "downloads")
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RuntimeError("openfuse_browser_downloads_contract_invalid")
                # OpenFuse worker accepts PDF signatures, but it does not provide a
                # malware scan verdict. Only metadata/failures are exposed here;
                # importing bytes into customer Files stays fail-closed.
                result = {
                    "action": "downloads",
                    "session_id": session_id,
                    "downloads": payload.get("downloads", []),
                    "failures": payload.get("failures", []),
                    "import_status": "blocked_until_malware_scanner_is_configured",
                }
            else:
                # Opening/reopening a persistent Chromium profile can itself navigate
                # and is therefore an externally visible action with ambiguous outcomes.
                action_submitted = True
                current, opened = await self._ensure_session(session_id, url)
                if action == "navigate":
                    if opened:
                        output = current
                    else:
                        action_submitted = True
                        output = (await self._session_request(session_id, "navigate", body={"url": url})).json()
                    result = {"action": "navigate", "session_id": session_id, "session": output}
                elif action == "screenshot":
                    if current.get("url") != url:
                        action_submitted = True
                        current = (await self._session_request(session_id, "navigate", body={"url": url})).json()
                    action_submitted = True
                    screenshot = await self._session_request(session_id, "screenshot")
                    image_bytes = screenshot.content
                    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n") or len(image_bytes) > 2_000_000:
                        raise RuntimeError("openfuse_browser_screenshot_signature_or_size_invalid")
                    uploaded = await self.http.post(
                        f"{self.api_url}/api/v1/artifacts/internal/browser-screenshot",
                        content=image_bytes,
                        headers={
                            **self._internal_headers(),
                            "Content-Type": "image/png",
                            "X-Agent-Run-Id": run_id,
                            "X-Owner-User-Id": user_id,
                            "X-Browser-Session-Id": session_id,
                        },
                        timeout=httpx.Timeout(35.0, connect=5.0),
                    )
                    uploaded.raise_for_status()
                    artifact = uploaded.json()
                    result = {
                        "action": "screenshot", "session_id": session_id,
                        "artifact_id": artifact.get("artifact_id"),
                        "mime_type": "image/png", "size_bytes": len(image_bytes),
                    }
                else:
                    # Read/input actions are bound to the URL supplied with the
                    # approved tool call; do not operate on a different stale page.
                    if current.get("url") != url:
                        action_submitted = True
                        current = (await self._session_request(session_id, "navigate", body={"url": url})).json()
                    if action == "input":
                        action_submitted = True
                        output = (await self._session_request(session_id, "input", body=arguments["input"])).json()
                    page = (await self._session_request(session_id, "read")).json()
                    if not isinstance(page, dict) or not isinstance(page.get("text"), str):
                        raise RuntimeError("openfuse_browser_read_contract_invalid")
                    original_length = len(page["text"])
                    page["text"] = page["text"][:40000]
                    page["truncated"] = bool(page.get("truncated")) or original_length > 40000
                    result = {
                        "action": action,
                        "session_id": session_id,
                        "session": output if action == "input" else current,
                        "page": page,
                    }

            serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            if len(serialized.encode("utf-8")) > 65536:
                raise RuntimeError("browser_action_result_exceeds_receipt_limit")
            await self._finish_receipt(
                receipt_id=receipt_id, run_id=run_id, user_id=user_id,
                status="succeeded", session_id=session_id, result=result,
            )
            return serialized
        except asyncio.CancelledError:
            await asyncio.shield(self._finish_receipt(
                receipt_id=receipt_id, run_id=run_id, user_id=user_id,
                status="unknown" if action_submitted else "failed",
                session_id=session_id, error_code="execution_cancelled",
            ))
            raise
        except Exception as exc:
            await self._finish_receipt(
                receipt_id=receipt_id, run_id=run_id, user_id=user_id,
                status="unknown" if action_submitted else "failed",
                session_id=session_id, error_code=type(exc).__name__.lower()[:100],
            )
            raise
