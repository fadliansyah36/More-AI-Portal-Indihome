from __future__ import annotations

import asyncio
import base64
import json
from uuid import uuid4
from urllib.parse import urlsplit
from typing import Any

import httpx


class IsolatedSandboxToolAdapter:
    """Worker client for the separately deployed execution supervisor.

    The worker never receives a Docker socket or starts a host-side Docker CLI.
    Approval is enforced centrally by the policy-enforced tool dispatcher.
    """

    def __init__(
        self, *, service_url: str, service_token: str, http: httpx.AsyncClient,
        allow_private_http: bool = False,
    ):
        parsed = urlsplit(service_url)
        private_http = (
            allow_private_http and parsed.scheme == "http"
            and parsed.hostname == "execution-supervisor" and parsed.port == 8080
            and not parsed.username and not parsed.password
            and parsed.path in ("", "/") and not parsed.query and not parsed.fragment
        )
        secure_https = (
            parsed.scheme == "https" and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and parsed.path in ("", "/") and parsed.port in (None, 443)
            and not parsed.query and not parsed.fragment
        )
        if not (secure_https or private_http):
            raise ValueError("sandbox_supervisor_service_url_invalid")
        if len(service_token) < 32:
            raise ValueError("sandbox_supervisor_service_token_invalid")
        self.service_url = service_url.rstrip("/")
        self.service_token = service_token
        self.http = http\n        self.workspace_tools = workspace_tools

    async def check_ready(self) -> dict[str, Any]:
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
            or payload.get("isolated_runner") is not True
            or payload.get("network_disabled") is not True
            or payload.get("digest_pinned_image") is not True
        ):
            raise RuntimeError("sandbox_supervisor_readiness_failed")
        return payload

    async def _cancel_remote(self, request_id: str, run_id: str, user_id: str) -> None:
        try:
            await asyncio.shield(self.http.post(
                f"{self.service_url}/v1/cancel",
                json={"request_id": request_id, "run_id": run_id, "user_id": user_id},
                headers={"Authorization": f"Bearer {self.service_token}"},
                timeout=httpx.Timeout(5.0, connect=2.0),
            ))
        except Exception:
            # The remote supervisor has its own hard execution deadline. Never
            # convert a local cancellation into an apparent successful execution.
            return

    async def _execute(
        self, *, source: str, language: str, run_id: str, user_id: str,
        timeout_seconds: int = 30, workspace_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        if not isinstance(run_id, str) or not run_id or not isinstance(user_id, str) or not user_id:
            raise PermissionError("sandbox_run_identity_required")
        if not isinstance(source, str) or not source or len(source.encode("utf-8")) > 8_000_000:
            raise ValueError("sandbox_source_size_invalid")
        if not workspace_id or self.workspace_tools is None:
            raise PermissionError("sandbox_workspace_binding_required")
        snapshot, baseline = await self.workspace_tools.export_execution_snapshot(
            user_id=user_id, workspace_id=workspace_id,
        )
        encoded_snapshot = {path: base64.b64encode(raw).decode("ascii") for path, raw in snapshot.items()}
        await self.check_ready()
        request_id = uuid4().hex
        try:
            response = await self.http.post(
                f"{self.service_url}/v1/execute",
                json={
                    "request_id": request_id,
                    "run_id": run_id, "user_id": user_id,
                    "language": language, "source": source,
                    "timeout_seconds": timeout_seconds,
                    "workspace_files": encoded_snapshot,
                },
                headers={"Authorization": f"Bearer {self.service_token}"},
                timeout=httpx.Timeout(timeout_seconds + 10.0, connect=3.0),
            )
        except asyncio.CancelledError:
            await self._cancel_remote(request_id, run_id, user_id)
            raise
        response.raise_for_status()
        result = response.json()
        if (
            not isinstance(result, dict)
            or result.get("request_id") != request_id
            or result.get("run_id") != run_id
            or result.get("isolated") is not True
            or isinstance(result.get("exit_code"), bool)
            or not isinstance(result.get("exit_code"), int)
            or not isinstance(result.get("stdout"), str)
            or not isinstance(result.get("stderr"), str)
            or not isinstance(result.get("timed_out"), bool)
            or not isinstance(result.get("workspace_files"), dict)
        ):
            raise RuntimeError("sandbox_supervisor_response_invalid")
        returned_files = {}
        returned_total = 0
        for path, encoded in result["workspace_files"].items():
            if not isinstance(path, str) or not isinstance(encoded, str):
                raise RuntimeError("sandbox_supervisor_workspace_response_invalid")
            raw = base64.b64decode(encoded, validate=True)
            returned_total += len(raw)
            if returned_total > 2_000_000:
                raise RuntimeError("sandbox_supervisor_workspace_response_too_large")
            returned_files[path] = raw
        changes = {"saved": [], "deleted": [], "saved_count": 0, "deleted_count": 0}
        if result["exit_code"] == 0 and not result["timed_out"]:
            changes = await self.workspace_tools.apply_execution_snapshot(
                run_id=run_id, user_id=user_id, workspace_id=workspace_id,
                before=snapshot, baseline=baseline, after=returned_files,
            )
        result.pop("workspace_files", None)
        result["workspace_changes"] = changes
        result["workspace_writeback"] = "committed" if result["exit_code"] == 0 and not result["timed_out"] else "discarded_execution_failed"
        return json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    async def python_execute(self, arguments: dict[str, Any], *, run_id: str, user_id: str, workspace_id: str | None = None) -> str:
        return await self._execute(
            source=arguments["code"], language="python",
            run_id=run_id, user_id=user_id, workspace_id=workspace_id,
            timeout_seconds=int(arguments.get("timeout_seconds", 30)),
        )

    async def bash(self, arguments: dict[str, Any], *, run_id: str, user_id: str, workspace_id: str | None = None) -> str:
        return await self._execute(
            source=arguments["command"], language="bash",
            run_id=run_id, user_id=user_id, workspace_id=workspace_id, timeout_seconds=30,
        )
