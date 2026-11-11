from __future__ import annotations

import hashlib
import os
import re
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from apps.worker.app.client import WorkerRpcClient


class SupabaseArtifactTool:
    """Persist owner-scoped agent artifacts to a private Supabase Storage bucket."""

    def __init__(self, client: WorkerRpcClient, *, bucket: str | None = None):
        self.client = client
        self.bucket = bucket if bucket is not None else os.getenv("MOREAI_ARTIFACTS_BUCKET", "")

    async def file_saver(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        filename = arguments.get("path")
        content = arguments.get("content")
        mime_type = arguments.get("mime_type", "text/plain")
        if not self.bucket:
            raise RuntimeError("artifact_storage_bucket_not_configured")
        if not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,179}", filename):
            raise ValueError("artifact_filename_invalid")
        if not isinstance(content, str):
            raise ValueError("artifact_content_must_be_text")
        raw = content.encode("utf-8")
        if not raw or len(raw) > 2_000_000:
            raise ValueError("artifact_content_size_invalid")
        if not isinstance(mime_type, str) or not re.fullmatch(r"[a-z0-9.+-]+/[a-z0-9.+-]+", mime_type.lower()):
            raise ValueError("artifact_mime_type_invalid")
        artifact_id = str(uuid4())
        storage_path = f"{user_id}/{artifact_id}/{filename}"
        url = (
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/object/"
            f"{quote(self.bucket, safe='')}/{quote(storage_path, safe='/')}"
        )
        headers = {
            "apikey": self.client.settings.service_role_key,
            "Authorization": f"Bearer {self.client.settings.service_role_key}",
            "Content-Type": mime_type.lower(),
            "x-upsert": "false",
        }
        bucket_response = await self.client.client.get(
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/bucket/{quote(self.bucket, safe='')}",
            headers=headers,
            timeout=8.0,
        )
        if bucket_response.status_code >= 400 or bucket_response.json().get("public") is not False:
            raise RuntimeError("artifact_bucket_must_exist_and_be_private")
        response = await self.client.client.post(url, content=raw, headers=headers, timeout=30.0)
        response.raise_for_status()
        checksum = hashlib.sha256(raw).hexdigest()
        try:
            row = await self.client.insert("artifacts", {
                "id": artifact_id,
                "user_id": user_id,
                "run_id": run_id,
                "storage_path": storage_path,
                "mime_type": mime_type.lower(),
                "size_bytes": len(raw),
                "checksum_sha256": checksum,
                "metadata": {"filename": filename, "run_id": run_id},
            })
        except Exception:
            await self.client.client.delete(url, headers=headers, timeout=15.0)
            raise
        import json
        return json.dumps({
            "artifact_id": row.get("id", artifact_id),
            "filename": filename,
            "size_bytes": len(raw),
            "checksum_sha256": checksum,
            "status": "stored",
        }, ensure_ascii=False, separators=(",", ":"))
