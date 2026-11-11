from __future__ import annotations

import hashlib
import os
import posixpath
import re
from urllib.parse import quote
from typing import Any

from apps.worker.app.client import WorkerRpcClient


class SupabaseWorkspaceTool:
    """Persistent, tenant-scoped SWE files backed by a private Supabase Storage bucket."""

    def __init__(self, client: WorkerRpcClient, *, bucket: str | None = None):
        self.client = client
        self.bucket = bucket or os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts")

    @staticmethod
    def _safe_path(value: Any) -> str:
        if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or "\x00" in value:
            raise ValueError("workspace_path_invalid")
        normalized = posixpath.normpath(value)
        if normalized in (".", "..") or normalized.startswith("../") or normalized.startswith("/"):
            raise ValueError("workspace_path_traversal_denied")
        if any(part in ("", ".", "..") for part in normalized.split("/")):
            raise ValueError("workspace_path_invalid")
        if not re.fullmatch(r"[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*", normalized):
            raise ValueError("workspace_path_characters_denied")
        return normalized

    def _url(self, user_id: str, workspace_id: str, path: str) -> str:
        storage_path = f"{user_id}/workspaces/{workspace_id}/{path}"
        return (
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/object/"
            f"{quote(self.bucket, safe='')}/{quote(storage_path, safe='/')}"
        )

    def _headers(self, *, content_type: str = "application/octet-stream", upsert: bool = False) -> dict[str, str]:
        key = self.client.settings.service_role_key
        return {
            "apikey": key, "Authorization": f"Bearer {key}",
            "Content-Type": content_type, "x-upsert": "true" if upsert else "false",
        }

    async def str_replace_editor(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str, workspace_id: str | None = None,
    ) -> str:
        import json
        if not workspace_id:
            raise RuntimeError("persistent_workspace_requires_workspace_id")
        path = self._safe_path(arguments.get("path"))
        old = arguments.get("old_str")
        new = arguments.get("new_str")
        if not isinstance(old, str) or not isinstance(new, str):
            raise ValueError("workspace_editor_text_required")
        if len(old.encode()) > 50_000 or len(new.encode()) > 50_000:
            raise ValueError("workspace_editor_patch_too_large")
        url = self._url(user_id, workspace_id, path)
        headers = self._headers()
        bucket = await self.client.client.get(
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket, safe='')}",
            headers=headers, timeout=8.0,
        )
        if bucket.status_code >= 400 or bucket.json().get("public") is not False:
            raise RuntimeError("workspace_bucket_must_exist_and_be_private")
        current = await self.client.client.get(url, headers=headers, timeout=15.0)
        if current.status_code == 404:
            if old:
                raise ValueError("workspace_file_not_found")
            source = ""
        else:
            current.raise_for_status()
            if len(current.content) > 2_000_000:
                raise ValueError("workspace_file_too_large")
            try:
                source = current.content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("workspace_editor_only_supports_utf8_text") from exc
        if old:
            occurrences = source.count(old)
            if occurrences != 1:
                raise ValueError("workspace_edit_match_must_be_unique")
            updated = source.replace(old, new, 1)
        else:
            updated = new
        raw = updated.encode("utf-8")
        if len(raw) > 2_000_000:
            raise ValueError("workspace_file_too_large")
        response = await self.client.client.post(
            url, content=raw, headers=self._headers(content_type="text/plain; charset=utf-8", upsert=True), timeout=20.0,
        )
        response.raise_for_status()
        return json.dumps({
            "workspace_id": workspace_id, "path": path, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "status": "saved",
        }, separators=(",", ":"))
