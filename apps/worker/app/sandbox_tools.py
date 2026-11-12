from __future__ import annotations

import asyncio
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
        self.http = http

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
        timeout_seconds: int = 30,
    ) -> str:
        if not isinstance(run_id, str) or not run_id or not isinstance(user_id, str) or not user_id:
            raise PermissionError("sandbox_run_identity_required")
        if not isinstance(source, str) or not source or len(source.encode("utf-8")) > 8_000_000:
            raise ValueError("sandbox_source_size_invalid")
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
        ):
            raise RuntimeError("sandbox_supervisor_response_invalid")
        return json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    async def python_execute(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        return await self._execute(
            source=arguments["code"], language="python",
            run_id=run_id, user_id=user_id,
            timeout_seconds=int(arguments.get("timeout_seconds", 30)),
        )

    async def bash(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        return await self._execute(
            source=arguments["command"], language="bash",
            run_id=run_id, user_id=user_id, timeout_seconds=30,
        )
