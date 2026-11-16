from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import struct
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
        self.worker_id = (os.getenv("MOREAI_BROWSER_WORKER_ID") or parsed.hostname or "browser-supervisor")[:128]
        if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", self.worker_id):
            raise ValueError("browser_supervisor_worker_id_invalid")
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
        try:
            await self._clamav_ping()
            scanner_status = "ready"
        except Exception:
            scanner_status = "unavailable_fail_closed"
        return {
            "status": "ready",
            "egress_enforced": True,
            "session_api": "openfuse-v1",
            "download_scanner": scanner_status,
        }

    async def _clamav_ping(self) -> None:
        host = os.getenv("MOREAI_CLAMAV_HOST", "")
        try:
            port = int(os.getenv("MOREAI_CLAMAV_PORT", "3310"))
        except ValueError as exc:
            raise RuntimeError("browser_download_scanner_configuration_invalid") from exc
        if not host or not 1 <= port <= 65535:
            raise RuntimeError("browser_download_scanner_not_configured")
        reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=5.0)
        try:
            writer.write(b"zPING\0")
            await writer.drain()
            verdict = await asyncio.wait_for(reader.read(128), timeout=5.0)
            if verdict.rstrip(b"\0\r\n") != b"PONG":
                raise RuntimeError("browser_download_scanner_not_ready")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _clamav_scan(self, content: bytes) -> None:
        host = os.getenv("MOREAI_CLAMAV_HOST", "")
        try:
            port = int(os.getenv("MOREAI_CLAMAV_PORT", "3310"))
        except ValueError as exc:
            raise RuntimeError("browser_download_scanner_configuration_invalid") from exc
        if not host or not 1 <= port <= 65535:
            raise RuntimeError("browser_download_scanner_not_configured")
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=5.0,
        )
        try:
            writer.write(b"zINSTREAM\0")
            await writer.drain()
            for offset in range(0, len(content), 65536):
                chunk = content[offset:offset + 65536]
                writer.write(struct.pack("!I", len(chunk)) + chunk)
                await writer.drain()
            writer.write(struct.pack("!I", 0))
            await writer.drain()
            verdict = await asyncio.wait_for(reader.read(4096), timeout=25.0)
            if not verdict.rstrip(b"\0\r\n").endswith(b"OK"):
                raise RuntimeError("browser_download_malware_scan_rejected")
        finally:
            writer.close()
            await writer.wait_closed()

    async def _finish_receipt(
        self, *, receipt_id: str, run_id: str, user_id: str,
        status: str, session_id: str | None = None,
        result: dict | None = None, error_code: str | None = None,
    ) -> None:
        response = await self.http.post(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/actions/{receipt_id}/finish",
            json={
                "run_id": run_id, "user_id": user_id, "worker_id": self.worker_id, "status": status,
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

    async def takeover_input(
        self, session_id: str, grant_token: str, input_payload: dict,
    ) -> dict:
        """Consume a customer-scoped one-time grant before forwarding human input to OpenFuse."""
        if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", session_id):
            raise ValueError("browser_takeover_session_id_invalid")
        if not isinstance(grant_token, str) or not 32 <= len(grant_token) <= 256:
            raise ValueError("browser_takeover_grant_token_invalid")
        if not isinstance(input_payload, dict) or len(json.dumps(input_payload).encode()) > 16_384:
            raise ValueError("browser_takeover_input_invalid")
        consumed = await self.http.post(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/takeover-grants/consume",
            json={"token": grant_token, "worker_id": self.worker_id},
            headers=self._internal_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        consumed.raise_for_status()
        grant = consumed.json()
        if (
            not isinstance(grant, dict)
            or grant.get("status") != "consumed"
            or grant.get("session_id") != session_id
            or "browser.input" not in grant.get("scopes", [])
            or not isinstance(grant.get("grant_id"), str)
            or not isinstance(grant.get("user_id"), str)
        ):
            raise RuntimeError("browser_takeover_grant_scope_or_session_mismatch")
        status, error_code = "failed", None
        try:
            response = await self._session_request(session_id, "input", body=input_payload)
            result = response.json()
            if not isinstance(result, dict) or result.get("id") != session_id:
                raise RuntimeError("browser_takeover_input_response_invalid")
            status = "succeeded"
            return result
        except Exception as exc:
            error_code = type(exc).__name__.lower()[:100]
            raise
        finally:
            audited = await self.http.post(
                f"{self.api_url}/api/v1/customer/browser-sessions/internal/takeover-grants/{quote(grant['grant_id'], safe='')}/input-result",
                json={
                    "session_id": session_id, "user_id": grant["user_id"],
                    "worker_id": self.worker_id, "status": status, "error_code": error_code,
                },
                headers=self._internal_headers(),
                timeout=httpx.Timeout(12.0, connect=3.0),
            )
            audited.raise_for_status()

    async def capture_session_preview(
        self, session_id: str, *, run_id: str, user_id: str,
    ) -> dict:
        """Capture the current OpenFuse page without navigation or human-input privileges."""
        if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", session_id):
            raise ValueError("browser_preview_session_id_invalid")
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
        if not current or current.get("status") != "active":
            raise RuntimeError("browser_preview_session_not_active")
        screenshot = await self._session_request(session_id, "screenshot")
        image_bytes = screenshot.content
        if not image_bytes.startswith(b"\\x89PNG\\r\\n\\x1a\\n") or not 8 <= len(image_bytes) <= 2_000_000:
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
        if not isinstance(artifact, dict) or not isinstance(artifact.get("artifact_id"), str):
            raise RuntimeError("browser_preview_artifact_persist_contract_invalid")
        return {
            "artifact_id": artifact["artifact_id"],
            "mime_type": "image/png",
            "size_bytes": len(image_bytes),
            "checksum_sha256": artifact.get("checksum_sha256"),
        }

    async def list_profiles(self) -> list[dict]:
        response = await self.http.get(
            f"{self.service_url}/sessions",
            headers=self._worker_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("id"), str)
            for item in payload
        ):
            raise RuntimeError("openfuse_browser_profiles_response_invalid")
        return payload

    async def delete_profile(self, profile_id: str) -> dict:
        # Requires the separately maintained pinned OpenFuse profile-delete patch.
        response = await self.http.delete(
            f"{self.service_url}/sessions/{quote(profile_id, safe='')}/delete-profile",
            headers=self._worker_headers(),
            timeout=httpx.Timeout(20.0, connect=3.0),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("id") != profile_id or payload.get("status") != "deleted":
            raise RuntimeError("openfuse_browser_profile_delete_contract_invalid")
        return payload

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
        # Fail before claiming a receipt if the isolated OpenFuse service is down.
        await self.check_ready()

        canonical = json.dumps(arguments, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        request_hash = hashlib.sha256(canonical.encode()).hexdigest()
        action_identity = tool_call_id if isinstance(tool_call_id, str) and tool_call_id else request_hash
        action_key = hashlib.sha256(f"{run_id}:{action_identity}".encode()).hexdigest()
        claim = await self.http.post(
            f"{self.api_url}/api/v1/customer/browser-sessions/internal/actions/claim",
            json={
                "run_id": run_id, "user_id": user_id, "worker_id": self.worker_id, "action_key": action_key,
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
                    "action": action,
                    "worker_id": self.worker_id,
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
                if not isinstance(payload, dict) or not isinstance(payload.get("downloads", []), list):
                    raise RuntimeError("openfuse_browser_downloads_contract_invalid")
                # Download import is a side effect. Mark the receipt ambiguous if
                # cancellation occurs after this point; never replay an import.
                action_submitted = True
                imported: list[dict] = []
                failures = list(payload.get("failures", []))[:100]
                for item in payload.get("downloads", [])[:20]:
                    if not isinstance(item, dict):
                        failures.append({"code": "download_metadata_invalid"})
                        continue
                    download_id = item.get("id")
                    filename = item.get("name")
                    if (
                        not isinstance(download_id, str)
                        or not re.fullmatch(r"[0-9a-fA-F-]{36}", download_id)
                        or not isinstance(filename, str)
                        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,179}", filename)
                        or item.get("mimeType") != "application/pdf"
                    ):
                        failures.append({"name": str(filename or "")[:80], "code": "download_metadata_invalid"})
                        continue
                    try:
                        downloaded = await self._session_request(
                            session_id, "downloads/" + quote(download_id, safe=""),
                        )
                        content = downloaded.content
                        if not content or len(content) > 10_000_000 or not content.startswith(b"%PDF-"):
                            raise ValueError("browser_download_signature_or_size_invalid")
                        await self._clamav_scan(content)
                        digest = hashlib.sha256(content).hexdigest()
                        uploaded = await self.http.post(
                            f"{self.api_url}/api/v1/artifacts/internal/browser-download",
                            content=content,
                            headers={
                                **self._internal_headers(),
                                "Content-Type": "application/pdf",
                                "X-Agent-Run-Id": run_id,
                                "X-Owner-User-Id": user_id,
                                "X-Browser-Session-Id": session_id,
                                "X-Filename": filename,
                                "X-Declared-Mime": "application/pdf",
                                "X-Declared-SHA256": digest,
                                "X-Scanner-Status": "clean",
                            },
                            timeout=httpx.Timeout(45.0, connect=5.0),
                        )
                        uploaded.raise_for_status()
                        artifact = uploaded.json()
                        imported.append({
                            "artifact_id": artifact.get("artifact_id"),
                            "filename": artifact.get("filename"),
                            "mime_type": artifact.get("mime_type"),
                            "size_bytes": artifact.get("size_bytes"),
                            "checksum_sha256": artifact.get("checksum_sha256"),
                            "scan_status": artifact.get("scan_status"),
                        })
                    except Exception as exc:
                        code = "malware_scan_or_storage_failed" if isinstance(exc, RuntimeError) else "download_import_failed"
                        failures.append({"name": filename, "code": code})
                result = {
                    "action": "downloads",
                    "session_id": session_id,
                    "imports": imported,
                    "failures": failures,
                    "import_status": "imported" if imported else "no_clean_downloads_imported",
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
