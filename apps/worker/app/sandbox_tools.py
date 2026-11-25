from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import re
from uuid import uuid4
from urllib.parse import urlsplit
from typing import Any

import httpx


class IsolatedSandboxToolAdapter:
    """Authenticated client for disposable, network-disabled workspace execution."""

    def __init__(
        self, *, service_url: str, service_token: str, http: httpx.AsyncClient,
        api_url: str, internal_token: str, worker_id: str,
        allow_private_http: bool = False, workspace_tools=None,
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
        if len(internal_token) < 32 or not api_url.startswith(("https://", "http://api:8000")):
            raise ValueError("computer_action_api_internal_auth_required")
        self.service_url = service_url.rstrip("/")
        self.service_token = service_token
        self.http = http
        self.api_url = api_url.rstrip("/")
        self.internal_token = internal_token
        self.worker_id = worker_id
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", self.worker_id):
            raise ValueError("sandbox_worker_id_invalid")
        self.workspace_tools = workspace_tools

    def _internal_headers(self) -> dict[str, str]:
        return {"X-MoreAI-Worker-Token": self.internal_token}

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

    async def _finish_receipt(
        self, *, receipt_id: str, run_id: str, user_id: str,
        status: str, result: dict | None = None, error_code: str | None = None,
    ) -> None:
        response = await self.http.post(
            f"{self.api_url}/api/v1/customer/computer/internal/actions/{receipt_id}/finish",
            json={
                "run_id": run_id, "user_id": user_id, "worker_id": self.worker_id, "status": status,
                "result": result, "error_code": error_code,
            },
            headers=self._internal_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        response.raise_for_status()

    async def _cancel_remote(self, request_id: str, run_id: str, user_id: str) -> None:
        try:
            await asyncio.shield(self.http.post(
                f"{self.service_url}/v1/cancel",
                json={"request_id": request_id, "run_id": run_id, "user_id": user_id},
                headers={"Authorization": f"Bearer {self.service_token}"},
                timeout=httpx.Timeout(5.0, connect=2.0),
            ))
        except Exception:
            return

    async def _execute(
        self, *, source: str, language: str, run_id: str, user_id: str,
        workspace_id: str | None, timeout_seconds: int = 30,
        tool_call_id: str | None = None,
    ) -> str:
        if not isinstance(run_id, str) or not run_id or not isinstance(user_id, str) or not user_id:
            raise PermissionError("sandbox_run_identity_required")
        if not workspace_id or self.workspace_tools is None:
            raise PermissionError("sandbox_workspace_binding_required")
        if language not in {"bash", "python"}:
            raise ValueError("sandbox_language_not_supported")
        if not isinstance(source, str) or not source or len(source.encode("utf-8")) > 8_000_000:
            raise ValueError("sandbox_source_size_invalid")

        # Workspace files persist in canonical Supabase Storage; the execution
        # container is disposable and never receives network access or secrets.
        snapshot, baseline = await self.workspace_tools.export_execution_snapshot(
            user_id=user_id, workspace_id=workspace_id,
        )
        encoded_snapshot = {
            path: base64.b64encode(raw).decode("ascii")
            for path, raw in snapshot.items()
        }
        await self.check_ready()

        request_identity = json.dumps({
            "language": language, "source": source,
            "workspace_id": workspace_id, "timeout_seconds": timeout_seconds,
        }, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        request_hash = hashlib.sha256(request_identity.encode()).hexdigest()
        action_identity = tool_call_id if isinstance(tool_call_id, str) and tool_call_id else request_hash
        action_key = hashlib.sha256(f"{run_id}:{action_identity}".encode()).hexdigest()
        claim = await self.http.post(
            f"{self.api_url}/api/v1/customer/computer/internal/actions/claim",
            json={
                "run_id": run_id, "user_id": user_id, "workspace_id": workspace_id,
                "worker_id": self.worker_id, "action_key": action_key, "request_hash": request_hash,
                "action_type": language,
            },
            headers=self._internal_headers(),
            timeout=httpx.Timeout(12.0, connect=3.0),
        )
        claim.raise_for_status()
        receipt = claim.json()
        receipt_id = receipt.get("receipt_id")
        if not isinstance(receipt_id, str):
            raise RuntimeError("computer_action_receipt_claim_invalid")
        if receipt.get("can_execute") is not True:
            if receipt.get("status") in {"succeeded", "failed"} and isinstance(receipt.get("result"), dict):
                return json.dumps(receipt["result"], ensure_ascii=False, separators=(",", ":"))
            raise RuntimeError("computer_action_replay_blocked_by_receipt_" + str(receipt.get("status") or "unknown"))

        request_id = action_key[:32]
        action_submitted = False
        try:
            action_submitted = True
            response = await self.http.post(
                f"{self.service_url}/v1/execute",
                json={
                    "request_id": request_id, "run_id": run_id, "user_id": user_id,
                    "language": language, "source": source,
                    "timeout_seconds": timeout_seconds,
                    "workspace_files": encoded_snapshot,
                },
                headers={"Authorization": f"Bearer {self.service_token}"},
                timeout=httpx.Timeout(timeout_seconds + 10.0, connect=3.0),
            )
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

            returned_files: dict[str, bytes] = {}
            returned_total = 0
            for file_path, encoded in result["workspace_files"].items():
                if not isinstance(file_path, str) or not isinstance(encoded, str):
                    raise RuntimeError("sandbox_supervisor_workspace_response_invalid")
                raw = base64.b64decode(encoded, validate=True)
                returned_total += len(raw)
                if returned_total > 2_000_000:
                    raise RuntimeError("sandbox_supervisor_workspace_response_too_large")
                returned_files[file_path] = raw

            changes = {"saved": [], "deleted": [], "saved_count": 0, "deleted_count": 0}
            success = result["exit_code"] == 0 and not result["timed_out"]
            if success:
                changes = await self.workspace_tools.apply_execution_snapshot(
                    run_id=run_id, user_id=user_id, workspace_id=workspace_id,
                    before=snapshot, baseline=baseline, after=returned_files,
                )

            result.pop("workspace_files", None)
            result["workspace_changes"] = changes
            result["workspace_writeback"] = "committed" if success else "discarded_execution_failed"
            serialized = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
            if len(serialized.encode("utf-8")) > 160_000:
                raise RuntimeError("computer_action_result_exceeds_receipt_limit")
            await self._finish_receipt(
                receipt_id=receipt_id, run_id=run_id, user_id=user_id,
                status="succeeded" if success else "failed", result=result,
            )
            return serialized
        except asyncio.CancelledError:
            await self._cancel_remote(request_id, run_id, user_id)
            try:
                await asyncio.shield(self._finish_receipt(
                    receipt_id=receipt_id, run_id=run_id, user_id=user_id,
                    status="unknown" if action_submitted else "failed",
                    error_code="execution_cancelled",
                ))
            except Exception:
                pass
            raise
        except Exception as exc:
            try:
                await self._finish_receipt(
                    receipt_id=receipt_id, run_id=run_id, user_id=user_id,
                    status="unknown" if action_submitted else "failed",
                    error_code=type(exc).__name__.lower()[:100],
                )
            except Exception:
                pass
            raise

    async def python_execute(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
        workspace_id: str | None = None, tool_call_id: str | None = None,
    ) -> str:
        return await self._execute(
            source=arguments["code"], language="python",
            run_id=run_id, user_id=user_id, workspace_id=workspace_id,
            timeout_seconds=int(arguments.get("timeout_seconds", 30)),
            tool_call_id=tool_call_id,
        )

    async def bash(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
        workspace_id: str | None = None, tool_call_id: str | None = None,
    ) -> str:
        return await self._execute(
            source=arguments["command"], language="bash",
            run_id=run_id, user_id=user_id, workspace_id=workspace_id,
            timeout_seconds=30, tool_call_id=tool_call_id,
        )
