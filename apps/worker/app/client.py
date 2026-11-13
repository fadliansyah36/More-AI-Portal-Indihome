from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Any

import httpx


from engine.agents.errors import RunPausedForApproval


@dataclass(frozen=True)
class WorkerSettings:
    supabase_url: str
    service_role_key: str
    worker_id: str
    lease_seconds: int = 90
    run_timeout_seconds: int = 1800

    def __post_init__(self):
        if not self.supabase_url.startswith("https://"):
            raise ValueError("SUPABASE_URL must use HTTPS")
        if not 8 <= len(self.worker_id) <= 128:
            raise ValueError("WORKER_ID must contain 8 to 128 characters")
        if not 15 <= self.lease_seconds <= 900:
            raise ValueError("lease_seconds must be between 15 and 900")
        if not 30 <= self.run_timeout_seconds <= 7200:
            raise ValueError("run_timeout_seconds must be between 30 and 7200")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")


class WorkerRpcClient:
    """Server-only client for the existing MoreAI worker SECURITY DEFINER RPCs."""

    def __init__(self, settings: WorkerSettings, client: httpx.AsyncClient):
        self.settings = settings
        self.client = client

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.service_role_key,
            "Authorization": f"Bearer {self.settings.service_role_key}",
            "Content-Type": "application/json",
        }

    async def rpc(self, name: str, payload: dict[str, Any]) -> Any:
        response = await self.client.post(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/rpc/{name}",
            json=payload, headers=self._headers(), timeout=15.0,
        )
        response.raise_for_status()
        return response.json()

    async def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self.client.get(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}",
            params=params, headers=self._headers(), timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    async def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.post(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}",
            json=payload, headers={**self._headers(), "Prefer": "return=representation"}, timeout=15.0,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            raise RuntimeError("Supabase insert returned no record")
        return rows[0]

    async def update(self, table: str, params: dict[str, str], payload: dict[str, Any]) -> list[dict[str, Any]]:
        response = await self.client.patch(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/{table}",
            params=params, json=payload,
            headers={**self._headers(), "Prefer": "return=representation"}, timeout=15.0,
        )
        response.raise_for_status()
        return response.json() if response.content else []

    async def claim_knowledge_ingestion(self, lease_seconds: int = 900) -> dict[str, Any] | None:
        rows = await self.rpc("moreai_worker_claim_knowledge_ingestion", {
            "p_lease_seconds": max(30, min(900, lease_seconds)),
        })
        return rows[0] if isinstance(rows, list) and rows else None

    async def heartbeat_knowledge_ingestion(
        self, document_id: str, owner_user_id: str, current_lease_until: str,
        lease_seconds: int = 900,
    ) -> str | None:
        from datetime import datetime, timedelta, timezone

        try:
            current = datetime.fromisoformat(current_lease_until.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError("knowledge_lease_timestamp_invalid") from exc
        if current.tzinfo is None:
            raise ValueError("knowledge_lease_timestamp_must_be_timezone_aware")
        next_lease = max(current, datetime.now(timezone.utc)) + timedelta(
            seconds=max(30, min(900, lease_seconds))
        )
        response = await self.client.patch(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/knowledge_documents",
            params={
                "id": f"eq.{document_id}",
                "owner_user_id": f"eq.{owner_user_id}",
                "source_type": "eq.file",
                "status": "eq.processing",
                "ingestion_lease_until": f"eq.{current_lease_until}",
            },
            json={"ingestion_lease_until": next_lease.isoformat()},
            headers={**self._headers(), "Prefer": "return=representation"},
            timeout=15.0,
        )
        response.raise_for_status()
        rows = response.json()
        if not isinstance(rows, list) or not rows:
            return None
        return str(rows[0].get("ingestion_lease_until") or next_lease.isoformat())

    async def finish_knowledge_ingestion(
        self, document_id: str, owner_user_id: str, success: bool,
        error_code: str | None = None, page_count: int | None = None,
    ) -> bool:
        result = await self.rpc("moreai_worker_finish_knowledge_ingestion", {
            "p_document_id": document_id,
            "p_owner_user_id": owner_user_id,
            "p_success": success,
            "p_error_code": error_code,
            "p_page_count": page_count,
        })
        return result is True

    async def download_storage_object(self, bucket: str, path: str, max_bytes: int = 26214400) -> bytes:
        if bucket != "moreai-knowledge-private" or not path or path.startswith("/") or ".." in path.split("/"):
            raise ValueError("knowledge_storage_object_path_invalid")
        response = await self.client.get(
            f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{path}",
            headers=self._headers(), timeout=60.0,
        )
        response.raise_for_status()
        if len(response.content) > max_bytes:
            raise ValueError("knowledge_storage_object_exceeds_limit")
        return response.content

    async def delete_knowledge_chunks(self, document_id: str, owner_user_id: str) -> None:
        response = await self.client.delete(
            f"{self.settings.supabase_url.rstrip('/')}/rest/v1/knowledge_chunks",
            params={"document_id": f"eq.{document_id}", "owner_user_id": f"eq.{owner_user_id}"},
            headers=self._headers(), timeout=20.0,
        )
        response.raise_for_status()

    async def list_checkpoints(self, run_id: str) -> dict[str, dict[str, Any]]:
        rows = await self.select("agent_run_checkpoints", {
            "run_id": f"eq.{run_id}",
            "select": "checkpoint_key,state,created_at",
            "order": "created_at.asc",
            "limit": "1000",
        })
        restored: dict[str, dict[str, Any]] = {}
        for row in rows:
            key, state = row.get("checkpoint_key"), row.get("state")
            if isinstance(key, str) and isinstance(state, dict):
                restored[key] = state
        return restored

    async def append_run_event(
        self, run_id: str, event_key: str, event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = await self.rpc("moreai_worker_append_run_event", {
            "p_run_id": run_id,
            "p_worker_id": self.settings.worker_id,
            "p_event_key": event_key,
            "p_event_type": event_type,
            "p_payload": payload or {},
        })
        if not isinstance(result, dict) or not isinstance(result.get("sequence"), int):
            raise RuntimeError("durable_run_event_append_failed")
        return result

    async def claim_event_outbox(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = await self.rpc("moreai_worker_claim_event_outbox", {
            "p_worker_id": self.settings.worker_id,
            "p_limit": max(1, min(100, limit)),
            "p_lease_seconds": 45,
        })
        return rows if isinstance(rows, list) else []

    async def ack_event_outbox(self, event_id: str) -> bool:
        result = await self.rpc("moreai_worker_ack_event_outbox", {
            "p_event_id": event_id, "p_worker_id": self.settings.worker_id,
        })
        return result is True

    async def retry_event_outbox(self, event_id: str, error_code: str) -> str:
        result = await self.rpc("moreai_worker_retry_event_outbox", {
            "p_event_id": event_id, "p_worker_id": self.settings.worker_id,
            "p_error_code": error_code[:80],
        })
        if result not in {"failed", "dead_letter"}:
            raise RuntimeError("outbox_retry_state_invalid")
        return result

    async def publish_run_event(self, event: dict[str, Any]) -> None:
        envelope = event.get("payload")
        if not isinstance(envelope, dict):
            raise ValueError("outbox_event_payload_invalid")
        run_id = envelope.get("run_id") or event.get("aggregate_id")
        event_id = envelope.get("event_id") or event.get("id")
        sequence = envelope.get("sequence")
        if not isinstance(run_id, str) or not isinstance(event_id, str) or not isinstance(sequence, int):
            raise ValueError("outbox_event_identity_invalid")
        response = await self.client.post(
            f"{self.settings.supabase_url.rstrip('/')}/realtime/v1/api/broadcast",
            headers=self._headers(),
            json={"messages": [{
                "topic": f"run:{run_id}",
                "event": "run.event",
                "payload": {
                    "event_id": event_id,
                    "run_id": run_id,
                    "sequence": sequence,
                    "type": envelope.get("event_type"),
                    "payload": envelope.get("event_payload") or {},
                    "created_at": envelope.get("created_at"),
                },
                "private": True,
            }]},
            timeout=10.0,
        )
        response.raise_for_status()

    async def claim_run(self) -> dict[str, Any] | None:
        return await self.rpc("moreai_worker_claim_run", {
            "p_worker_id": self.settings.worker_id,
            "p_lease_seconds": self.settings.lease_seconds,
        })

    async def heartbeat(self, run_id: str) -> dict[str, Any]:
        return await self.rpc("moreai_worker_heartbeat", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_lease_seconds": self.settings.lease_seconds,
        })

    async def checkpoint(self, run_id: str, key: str, state: dict[str, Any]) -> dict[str, Any]:
        return await self.rpc("moreai_worker_checkpoint", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_checkpoint_key": key, "p_state": state,
        })


    async def workspace_get_file(self, user_id: str, workspace_id: str, path: str) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_get_file", {"p_user_id":user_id,"p_workspace_id":workspace_id,"p_path":path})
        if not isinstance(result,dict): raise RuntimeError("workspace_file_metadata_invalid")
        return result

    async def workspace_begin_write(self, run_id: str, user_id: str, workspace_id: str, path: str, expected_version: int) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_begin_write", {"p_run_id":run_id,"p_worker_id":self.settings.worker_id,"p_user_id":user_id,"p_workspace_id":workspace_id,"p_path":path,"p_expected_version":expected_version})
        if not isinstance(result,dict): raise RuntimeError("workspace_write_reservation_invalid")
        return result

    async def workspace_commit_write(self, run_id: str, user_id: str, workspace_id: str, path: str, token: str, version: int, storage_path: str, sha256: str, size_bytes: int) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_commit_write", {"p_run_id":run_id,"p_worker_id":self.settings.worker_id,"p_user_id":user_id,"p_workspace_id":workspace_id,"p_path":path,"p_token":token,"p_version":version,"p_storage_path":storage_path,"p_sha256":sha256,"p_size_bytes":size_bytes})
        if not isinstance(result,dict): raise RuntimeError("workspace_write_commit_invalid")
        return result

    async def workspace_restore_deleted_file(
        self, run_id: str, user_id: str, workspace_id: str, path: str,
        expected_version: int, storage_path: str, sha256: str, size_bytes: int, bucket: str,
    ) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_restore_deleted_file", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_user_id": user_id, "p_workspace_id": workspace_id,
            "p_path": path, "p_expected_version": expected_version,
            "p_storage_path": storage_path, "p_sha256": sha256,
            "p_size_bytes": size_bytes, "p_bucket": bucket,
        })
        if not isinstance(result, dict) or result.get("restored") is not True:
            raise RuntimeError("workspace_restore_deleted_commit_invalid")
        return result

    async def workspace_delete_file(self, run_id: str, user_id: str, workspace_id: str, path: str, expected_version: int) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_delete_file", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_user_id": user_id, "p_workspace_id": workspace_id,
            "p_path": path, "p_expected_version": expected_version,
        })
        if not isinstance(result, dict) or result.get("deleted") is not True:
            raise RuntimeError("workspace_delete_commit_invalid")
        return result

    async def workspace_rename_file(self, run_id: str, user_id: str, workspace_id: str, path: str, new_path: str, expected_version: int) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_rename_file", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_user_id": user_id, "p_workspace_id": workspace_id,
            "p_path": path, "p_new_path": new_path,
            "p_expected_version": expected_version,
        })
        if not isinstance(result, dict) or result.get("renamed") is not True:
            raise RuntimeError("workspace_rename_commit_invalid")
        return result

    async def workspace_commit_execution_snapshot(
        self, run_id: str, user_id: str, workspace_id: str, bucket: str,
        operation_key: str, changes: list[dict[str, Any]], deletes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        result = await self.rpc("moreai_workspace_commit_execution_snapshot", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_user_id": user_id, "p_workspace_id": workspace_id,
            "p_bucket": bucket, "p_operation_key": operation_key,
            "p_changes": changes, "p_deletes": deletes,
        })
        if (
            not isinstance(result, dict) or result.get("atomic") is not True
            or not isinstance(result.get("saved"), list)
            or not isinstance(result.get("deleted"), list)
        ):
            raise RuntimeError("workspace_execution_commit_invalid")
        return result

    async def workspace_abort_write(self, run_id: str, user_id: str, workspace_id: str, path: str, token: str) -> bool:
        return await self.rpc("moreai_workspace_abort_write", {"p_run_id":run_id,"p_worker_id":self.settings.worker_id,"p_user_id":user_id,"p_workspace_id":workspace_id,"p_path":path,"p_token":token}) is True

    async def wait_for_tool_approval(
        self, run_id: str, user_id: str, tool_key: str, arguments: dict[str, Any],
    ) -> bool:
        """Pause execution until an owner decision, then atomically consume one approval."""
        # The durable approval table stores canonical action keys, not every
        # OpenManus adapter name. Keep the original arguments hash so a decision
        # is bound to the exact tool call while mapping the editor to file_edit.
        approval_tool_key = {
            "str_replace_editor": "file_edit",
        }.get(tool_key, tool_key)
        arguments_hash = hashlib.sha256(
            json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        # Persist a minimal, non-sensitive lifecycle marker before the pause RPC
        # releases the worker lease. The hash binds the request to the exact arguments
        # without publishing the arguments themselves.
        await self.append_run_event(
            run_id, f"worker:approval-requested:{arguments_hash}",
            "tool.approval_requested",
            {"tool": approval_tool_key[:80], "arguments_hash": arguments_hash},
        )
        operation = arguments.get("operation") if isinstance(arguments.get("operation"), str) else "edit"
        path = arguments.get("path") if isinstance(arguments.get("path"), str) else "workspace file"
        action_labels = {
            "create": "create", "edit": "edit", "delete": "delete",
            "rename": "rename", "restore_deleted": "restore deleted",
        }
        summary = f"Approval required to {action_labels.get(operation, 'edit')} workspace file {path[:160]}"
        state = await self.rpc("moreai_worker_pause_for_tool_approval", {
            "p_run_id": run_id, "p_user_id": user_id,
            "p_worker_id": self.settings.worker_id, "p_tool_key": approval_tool_key,
            "p_arguments_hash": arguments_hash,
            "p_summary": summary,
            "p_expires_in_seconds": 900,
        })
        if not isinstance(state, dict) or not isinstance(state.get("status"), str):
            raise RuntimeError("tool_approval_pause_failed")
        status = state["status"]
        if status == "pending":
            raise RunPausedForApproval("run_paused_for_tool_approval")
        if status == "approved":
            consumed = await self.rpc("moreai_consume_tool_approval", {
                "p_run_id": run_id, "p_user_id": user_id,
                "p_tool_key": approval_tool_key, "p_arguments_hash": arguments_hash,
            })
            if consumed is True:
                # Decision events are committed atomically by the decision RPC.
                # Only the later one-time consumption event remains worker-observed.
                await self.append_run_event(
                    run_id, f"worker:approval:{arguments_hash}:consumed",
                    "tool.approval_consumed",
                    {"tool": approval_tool_key[:80], "arguments_hash": arguments_hash},
                )
            return consumed is True
        if status in {"denied", "expired", "consumed"}:
            return False
        raise RuntimeError("tool_approval_state_invalid")

    async def finish(
        self, run_id: str, status: str, output: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None, retry_delay_seconds: int = 30,
    ) -> dict[str, Any]:
        if status not in {"succeeded", "failed", "cancelled"}:
            raise ValueError("Only terminal run statuses can be submitted")
        return await self.rpc("moreai_worker_finish_run", {
            "p_run_id": run_id, "p_worker_id": self.settings.worker_id,
            "p_status": status, "p_output": output, "p_error": error,
            "p_retry_delay_seconds": retry_delay_seconds,
        })
