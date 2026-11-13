from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
from urllib.parse import quote
from typing import Any

from apps.worker.app.client import WorkerRpcClient


class SupabaseWorkspaceTool:
    """Immutable-version workspace files with lease-fenced compare-and-swap metadata."""

    def __init__(self, client: WorkerRpcClient, *, bucket: str | None = None):
        self.client = client
        self.bucket = bucket or os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts")

    @staticmethod
    def _safe_path(value: Any) -> str:
        if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or "\x00" in value:
            raise ValueError("workspace_path_invalid")
        parts=value.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise ValueError("workspace_path_traversal_denied")
        normalized=posixpath.normpath(value)
        if normalized in (".","..") or normalized.startswith("../") or normalized.startswith("/"):
            raise ValueError("workspace_path_traversal_denied")
        if not re.fullmatch(r"[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*",normalized):
            raise ValueError("workspace_path_characters_denied")
        return normalized

    def _object_url(self, storage_path: str) -> str:
        return f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/object/{quote(self.bucket,safe='')}/{quote(storage_path,safe='/')}"

    def _headers(self, content_type: str="application/octet-stream", upsert: bool=False) -> dict[str,str]:
        key=self.client.settings.service_role_key
        return {"apikey":key,"Authorization":f"Bearer {key}","Content-Type":content_type,"x-upsert":"true" if upsert else "false"}

    async def str_replace_editor(self, arguments: dict[str,Any], *, run_id: str, user_id: str, workspace_id: str|None=None) -> str:
        if not workspace_id: raise RuntimeError("persistent_workspace_requires_workspace_id")
        path=self._safe_path(arguments.get("path"))
        old,new=arguments.get("old_str"),arguments.get("new_str")
        if old is None:
            old = ""
        operation = arguments.get("operation")
        if operation is None:
            operation = "edit" if old else "create"
        if operation not in {"create", "edit", "delete", "rename", "restore_deleted"}:
            raise ValueError("workspace_operation_invalid")
        current=await self.client.workspace_get_file(user_id,workspace_id,path)
        version=current.get("version")
        if isinstance(version,bool) or not isinstance(version,int):
            raise RuntimeError("workspace_version_invalid")
        expected=arguments.get("expected_version",version)
        if isinstance(expected,bool) or not isinstance(expected,int) or expected!=version:
            raise ValueError("workspace_version_conflict")
        storage_path=current.get("storage_path")
        deleted_at = current.get("deleted_at")
        if deleted_at is not None and operation != "restore_deleted":
            raise ValueError("workspace_file_is_deleted_use_restore_deleted")
        if operation == "restore_deleted":
            if deleted_at is None or not storage_path:
                raise ValueError("workspace_deleted_file_not_found")
            bucket = await self.client.client.get(
                f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket, safe='')}",
                headers=self._headers(), timeout=8.0,
            )
            if bucket.status_code >= 400 or not isinstance(bucket.json(), dict) or bucket.json().get("public") is not False:
                raise RuntimeError("workspace_bucket_must_exist_and_be_private")
            expected_sha = current.get("sha256")
            expected_size = current.get("size_bytes")
            if (
                not isinstance(expected_sha, str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
                or isinstance(expected_size, bool)
                or not isinstance(expected_size, int)
                or expected_size < 0
                or expected_size > 2_000_000
            ):
                raise RuntimeError("workspace_restore_metadata_invalid")
            source_prefix = f"{user_id}/workspaces/{workspace_id}/versions/"
            if not storage_path.startswith(source_prefix) or storage_path.startswith("/") or ".." in storage_path.split("/"):
                raise RuntimeError("workspace_restore_source_path_invalid")
            source_response = await self.client.client.get(
                self._object_url(storage_path), headers=self._headers(), timeout=20.0,
            )
            source_response.raise_for_status()
            raw = source_response.content
            if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha:
                raise RuntimeError("workspace_restore_source_integrity_mismatch")

            next_version = version + 1
            restored_path = f"{user_id}/workspaces/{workspace_id}/versions/{next_version}/{path}"
            upload = await self.client.client.post(
                self._object_url(restored_path),
                content=raw,
                headers=self._headers("application/octet-stream", False),
                timeout=25.0,
            )
            if upload.status_code >= 400:
                # An immutable destination may already exist after a lost commit response.
                existing = await self.client.client.get(
                    self._object_url(restored_path), headers=self._headers(), timeout=20.0,
                )
                if (
                    existing.status_code != 200
                    or len(existing.content) != expected_size
                    or hashlib.sha256(existing.content).hexdigest() != expected_sha
                ):
                    upload.raise_for_status()
                    raise RuntimeError("workspace_restore_immutable_object_collision")
            result = await self.client.workspace_restore_deleted_file(
                run_id, user_id, workspace_id, path, version,
                restored_path, expected_sha, expected_size, self.bucket,
            )
            return json.dumps(result,separators=(",",":"))
        if operation == "delete":
            if not storage_path:
                raise ValueError("workspace_file_not_found")
            result = await self.client.workspace_delete_file(
                run_id,user_id,workspace_id,path,version,
            )
            return json.dumps(result,separators=(",",":"))
        if operation == "rename":
            if not storage_path:
                raise ValueError("workspace_file_not_found")
            new_path = self._safe_path(arguments.get("new_path"))
            target = await self.client.workspace_get_file(user_id,workspace_id,new_path)
            if target.get("storage_path") or target.get("version", 0) > 0:
                raise ValueError("workspace_rename_target_exists")
            result = await self.client.workspace_rename_file(
                run_id,user_id,workspace_id,path,new_path,version,
            )
            return json.dumps(result,separators=(",",":"))
        if operation == "create" and storage_path:
            raise ValueError("workspace_create_cannot_overwrite_existing_file")
        if operation == "edit" and not storage_path:
            raise ValueError("workspace_file_not_found")
        if operation == "edit" and (not isinstance(old, str) or not old):
            raise ValueError("workspace_edit_old_str_required")
        if operation == "create" and old not in ("", None):
            raise ValueError("workspace_create_old_str_must_be_empty")
        if not isinstance(new,str):
            raise ValueError("workspace_editor_text_required")
        if len(old.encode())>50000 or len(new.encode())>50000: raise ValueError("workspace_editor_patch_too_large")
        bucket=await self.client.client.get(f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket,safe='')}",headers=self._headers(),timeout=8.0)
        if bucket.status_code>=400 or bucket.json().get("public") is not False: raise RuntimeError("workspace_bucket_must_exist_and_be_private")

        if storage_path:
            response=await self.client.client.get(self._object_url(storage_path),headers=self._headers(),timeout=15.0)
            response.raise_for_status()
            if len(response.content)>2000000: raise ValueError("workspace_file_too_large")
            try: source=response.content.decode("utf-8")
            except UnicodeDecodeError as exc: raise ValueError("workspace_editor_only_supports_utf8_text") from exc
        else:
            source=""
        if operation == "edit":
            if source.count(old)!=1: raise ValueError("workspace_edit_match_must_be_unique")
            updated=source.replace(old,new,1)
        else:
            updated=new
        raw=updated.encode("utf-8")
        if len(raw)>2000000: raise ValueError("workspace_file_too_large")
        reservation=await self.client.workspace_begin_write(run_id,user_id,workspace_id,path,version)
        token, next_version, object_path=reservation.get("token"),reservation.get("version"),reservation.get("storage_path")
        if not isinstance(token,str) or not isinstance(next_version,int) or not isinstance(object_path,str):
            raise RuntimeError("workspace_write_reservation_invalid")
        sha=hashlib.sha256(raw).hexdigest()
        committed=False
        try:
            upload=await self.client.client.post(self._object_url(object_path),content=raw,headers=self._headers("text/plain; charset=utf-8",False),timeout=20.0)
            upload.raise_for_status()
            result=await self.client.workspace_commit_write(run_id,user_id,workspace_id,path,token,next_version,object_path,sha,len(raw))
            committed=True
            return json.dumps({"workspace_id":workspace_id,"path":path,"version":result["version"],"bytes":len(raw),"sha256":sha,"status":"saved"},separators=(",",":"))
        finally:
            if not committed:
                await self.client.workspace_abort_write(run_id,user_id,workspace_id,path,token)


    async def restore_version(self, arguments: dict[str, Any], *, run_id: str, user_id: str, workspace_id: str | None = None) -> str:
        """Restore an immutable historical object by committing its bytes as a new version."""
        if not workspace_id:
            raise RuntimeError("persistent_workspace_requires_workspace_id")
        path = self._safe_path(arguments.get("path"))
        target_version = arguments.get("version")
        if isinstance(target_version, bool) or not isinstance(target_version, int) or target_version < 1:
            raise ValueError("workspace_restore_version_invalid")

        bucket = await self.client.client.get(
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket, safe='')}",
            headers=self._headers(), timeout=8.0,
        )
        if bucket.status_code >= 400 or not isinstance(bucket.json(), dict) or bucket.json().get("public") is not False:
            raise RuntimeError("workspace_bucket_must_exist_and_be_private")

        current = await self.client.workspace_get_file(user_id, workspace_id, path)
        current_version = current.get("version")
        if isinstance(current_version, bool) or not isinstance(current_version, int):
            raise RuntimeError("workspace_version_invalid")
        if target_version >= current_version:
            raise ValueError("workspace_restore_must_target_an_older_version")

        history = await self.client.select("agent_workspace_file_versions", {
            "workspace_id": f"eq.{workspace_id}",
            "path": f"eq.{path}",
            "version": f"eq.{target_version}",
            "select": "version,storage_path,sha256,size_bytes",
            "limit": "1",
        })
        if not history:
            raise ValueError("workspace_restore_version_not_found")
        source_meta = history[0]
        source_path = source_meta.get("storage_path")
        expected_sha = source_meta.get("sha256")
        expected_size = source_meta.get("size_bytes")
        if not isinstance(source_path, str) or not isinstance(expected_sha, str) or not isinstance(expected_size, int):
            raise RuntimeError("workspace_restore_metadata_invalid")
        if expected_size < 0 or expected_size > 2_000_000 or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise RuntimeError("workspace_restore_metadata_invalid")

        source_response = await self.client.client.get(
            self._object_url(source_path), headers=self._headers(), timeout=20.0,
        )
        source_response.raise_for_status()
        raw = source_response.content
        if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha:
            raise RuntimeError("workspace_restore_source_integrity_mismatch")

        reservation = await self.client.workspace_begin_write(
            run_id, user_id, workspace_id, path, current_version,
        )
        token = reservation.get("token")
        next_version = reservation.get("version")
        object_path = reservation.get("storage_path")
        if not isinstance(token, str) or not isinstance(next_version, int) or not isinstance(object_path, str):
            raise RuntimeError("workspace_write_reservation_invalid")
        committed = False
        try:
            upload = await self.client.client.post(
                self._object_url(object_path), content=raw,
                headers=self._headers("application/octet-stream", False), timeout=25.0,
            )
            upload.raise_for_status()
            result = await self.client.workspace_commit_write(
                run_id, user_id, workspace_id, path, token, next_version,
                object_path, expected_sha, len(raw),
            )
            committed = True
            return json.dumps({
                "workspace_id": workspace_id, "path": path,
                "restored_from_version": target_version,
                "version": result["version"], "bytes": len(raw),
                "sha256": expected_sha, "status": "restored_as_new_version",
            }, separators=(",", ":"))
        finally:
            if not committed:
                await self.client.workspace_abort_write(
                    run_id, user_id, workspace_id, path, token,
                )

    async def read_file(
        self,
        arguments: dict[str, Any],
        *,
        run_id: str,
        user_id: str,
        workspace_id: str | None = None,
    ) -> str:
        """Read an owner/member-scoped UTF-8 workspace file with integrity verification."""
        if not workspace_id:
            raise RuntimeError("persistent_workspace_requires_workspace_id")
        path = self._safe_path(arguments.get("path"))
        bucket = await self.client.client.get(
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket, safe='')}",
            headers=self._headers(),
            timeout=8.0,
        )
        if (
            bucket.status_code >= 400
            or not isinstance(bucket.json(), dict)
            or bucket.json().get("public") is not False
        ):
            raise RuntimeError("workspace_bucket_must_exist_and_be_private")

        metadata = await self.client.workspace_get_file(user_id, workspace_id, path)
        storage_path = metadata.get("storage_path")
        expected_sha = metadata.get("sha256")
        expected_size = metadata.get("size_bytes")
        version = metadata.get("version")
        if not isinstance(storage_path, str) or not storage_path:
            raise ValueError("workspace_file_not_found")
        if (
            not isinstance(expected_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
            or isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size < 0
            or expected_size > 2_000_000
            or isinstance(version, bool)
            or not isinstance(version, int)
            or version < 1
        ):
            raise RuntimeError("workspace_file_metadata_invalid")

        response = await self.client.client.get(
            self._object_url(storage_path),
            headers=self._headers(),
            timeout=20.0,
        )
        response.raise_for_status()
        raw = response.content
        if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha:
            raise RuntimeError("workspace_file_integrity_mismatch")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("workspace_read_only_supports_utf8_text") from exc
        return json.dumps(
            {
                "workspace_id": workspace_id,
                "path": path,
                "version": version,
                "content": content,
                "bytes": len(raw),
                "sha256": expected_sha,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )



    async def export_execution_snapshot(
        self, *, user_id: str, workspace_id: str,
        max_files: int = 200, max_bytes: int = 2_000_000,
    ) -> tuple[dict[str, bytes], dict[str, dict[str, Any]]]:
        """Build a bounded, integrity-checked snapshot for one authorized run workspace."""
        rows = await self.client.select("agent_workspace_files", {
            "workspace_id": f"eq.{workspace_id}",
            "deleted_at": "is.null",
            "select": "path,version,storage_path,sha256,size_bytes",
            "order": "path.asc",
            "limit": str(max_files + 1),
        })
        if len(rows) > max_files:
            raise ValueError("workspace_execution_file_count_exceeded")
        snapshot: dict[str, bytes] = {}
        baseline: dict[str, dict[str, Any]] = {}
        total = 0
        prefix = f"{user_id}/workspaces/{workspace_id}/versions/"
        for row in rows:
            path = self._safe_path(row.get("path"))
            # Re-check membership and current metadata through the owner-scoped RPC.
            metadata = await self.client.workspace_get_file(user_id, workspace_id, path)
            storage_path = metadata.get("storage_path")
            expected_sha = metadata.get("sha256")
            expected_size = metadata.get("size_bytes")
            version = metadata.get("version")
            if (
                not isinstance(storage_path, str) or not storage_path.startswith(prefix)
                or storage_path.startswith("/") or ".." in storage_path.split("/")
                or not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
                or isinstance(expected_size, bool) or not isinstance(expected_size, int)
                or expected_size < 0 or expected_size > max_bytes
                or isinstance(version, bool) or not isinstance(version, int) or version < 1
            ):
                raise RuntimeError("workspace_execution_metadata_invalid")
            response = await self.client.client.get(
                self._object_url(storage_path), headers=self._headers(), timeout=20.0,
            )
            response.raise_for_status()
            raw = response.content
            if len(raw) != expected_size or hashlib.sha256(raw).hexdigest() != expected_sha:
                raise RuntimeError("workspace_execution_integrity_mismatch")
            total += len(raw)
            if total > max_bytes:
                raise ValueError("workspace_execution_snapshot_too_large")
            snapshot[path] = raw
            baseline[path] = {
                "version": version, "sha256": expected_sha, "size_bytes": expected_size,
            }
        return snapshot, baseline

    async def apply_execution_snapshot(
        self, *, run_id: str, user_id: str, workspace_id: str,
        before: dict[str, bytes], baseline: dict[str, dict[str, Any]],
        after: dict[str, bytes], max_bytes: int = 2_000_000,
    ) -> dict[str, Any]:
        """Upload immutable objects, then atomically commit all workspace metadata in one RPC."""
        if len(after) > 200 or len(before) > 200:
            raise ValueError("workspace_execution_file_count_exceeded")
        total = 0
        for path, raw in after.items():
            self._safe_path(path)
            if not isinstance(raw, bytes):
                raise ValueError("workspace_execution_file_invalid")
            total += len(raw)
            if len(raw) > 2_000_000 or total > min(max_bytes, 2_000_000):
                raise ValueError("workspace_execution_result_too_large")

        changed = sorted(
            path for path, raw in after.items()
            if path not in before or hashlib.sha256(raw).hexdigest() != hashlib.sha256(before[path]).hexdigest()
        )
        deleted = sorted(path for path in before if path not in after)
        if len(changed) + len(deleted) > 200:
            raise ValueError("workspace_execution_change_count_exceeded")
        if not changed and not deleted:
            return {"saved": [], "deleted": [], "saved_count": 0, "deleted_count": 0, "atomic": True}

        bucket = await self.client.client.get(
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket, safe='')}",
            headers=self._headers(), timeout=8.0,
        )
        if bucket.status_code >= 400 or not isinstance(bucket.json(), dict) or bucket.json().get("public") is not False:
            raise RuntimeError("workspace_bucket_must_exist_and_be_private")

        changes: list[dict[str, Any]] = []
        deletes: list[dict[str, Any]] = []
        operation_material: dict[str, Any] = {
            "run_id": run_id, "user_id": user_id, "workspace_id": workspace_id,
            "changes": [], "deletes": [],
        }

        for path in changed:
            existing = await self.client.select("agent_workspace_files", {
                "workspace_id": f"eq.{workspace_id}",
                "path": f"eq.{path}",
                "select": "deleted_at",
                "limit": "1",
            })
            if existing and existing[0].get("deleted_at") is not None:
                raise ValueError("workspace_execution_cannot_overwrite_deleted_path")
            expected = baseline.get(path, {}).get("version", 0)
            if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
                raise RuntimeError("workspace_execution_baseline_invalid")
            version = expected + 1
            raw = after[path]
            digest = hashlib.sha256(raw).hexdigest()
            storage_path = f"{user_id}/workspaces/{workspace_id}/versions/{version}/{path}"
            object_url = self._object_url(storage_path)
            upload = await self.client.client.post(
                object_url, content=raw,
                headers=self._headers("application/octet-stream", False), timeout=25.0,
            )
            if upload.status_code >= 400:
                # Deterministic immutable paths make retries safe only if an existing
                # object is byte-identical to the intended version.
                existing_object = await self.client.client.get(
                    object_url, headers=self._headers(), timeout=20.0,
                )
                if existing_object.status_code != 200 or hashlib.sha256(existing_object.content).hexdigest() != digest:
                    upload.raise_for_status()
                    raise RuntimeError("workspace_immutable_object_collision")
            changes.append({
                "path": path, "expected_version": expected,
                "storage_path": storage_path, "sha256": digest, "size_bytes": len(raw),
            })
            operation_material["changes"].append({
                "path": path, "expected_version": expected, "sha256": digest,
            })

        for path in deleted:
            expected = baseline.get(path, {}).get("version")
            if isinstance(expected, bool) or not isinstance(expected, int) or expected < 1:
                raise RuntimeError("workspace_execution_delete_baseline_invalid")
            deletes.append({"path": path, "expected_version": expected})
            operation_material["deletes"].append({"path": path, "expected_version": expected})

        operation_key = hashlib.sha256(
            json.dumps(operation_material, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        result = await self.client.workspace_commit_execution_snapshot(
            run_id, user_id, workspace_id, self.bucket, operation_key, changes, deletes,
        )
        return result
