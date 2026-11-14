from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

from apps.worker.app.client import WorkerRpcClient


class SupabaseArtifactTool:
    """Persist owner-scoped agent artifacts to a private Supabase Storage bucket."""

    def __init__(self, client: WorkerRpcClient, *, bucket: str | None = None):
        self.client = client
        self.bucket = bucket if bucket is not None else os.getenv("MOREAI_ARTIFACTS_BUCKET", "")

    async def _store_bytes(
        self, *, filename: str, raw: bytes, mime_type: str,
        run_id: str, user_id: str, metadata: dict[str, Any] | None = None,
        artifact_id: str | None = None,
    ) -> str:
        if not self.bucket:
            raise RuntimeError("artifact_storage_bucket_not_configured")
        if (
            not isinstance(filename, str) or len(filename) > 512
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,179}(?:/[A-Za-z0-9][A-Za-z0-9._ -]{0,179})*", filename)
        ):
            raise ValueError("artifact_filename_invalid")
        max_bytes = max(1_000_000, min(150_000_000, int(os.getenv("MOREAI_MEDIA_MAX_ARTIFACT_BYTES", "100000000"))))
        if not raw or len(raw) > max_bytes:
            raise ValueError("artifact_content_size_invalid")
        if not isinstance(mime_type, str) or not re.fullmatch(r"[a-z0-9.+-]+/[a-z0-9.+-]+", mime_type.lower()):
            raise ValueError("artifact_mime_type_invalid")

        artifact_id = str(UUID(artifact_id)) if artifact_id else str(uuid4())
        checksum = hashlib.sha256(raw).hexdigest()
        existing = await self.client.select("artifacts", {
            "id": f"eq.{artifact_id}", "user_id": f"eq.{user_id}",
            "select": "id,storage_path,mime_type,size_bytes,checksum_sha256", "limit": "1",
        })
        if existing:
            row = existing[0]
            if row.get("checksum_sha256") != checksum or row.get("size_bytes") != len(raw):
                raise RuntimeError("artifact_id_checksum_conflict")
            return json.dumps({
                "artifact_id": row.get("id"), "filename": filename,
                "mime_type": row.get("mime_type"), "size_bytes": row.get("size_bytes"),
                "checksum_sha256": checksum, "status": "stored",
            }, ensure_ascii=False, separators=(",", ":"))
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
        response = await self.client.client.post(url, content=raw, headers=headers, timeout=60.0)
        response.raise_for_status()
        safe_metadata = {"filename": filename, "run_id": run_id}
        if isinstance(metadata, dict):
            for key in ("provider", "model", "media_type", "provider_task_id"):
                value = metadata.get(key)
                if isinstance(value, str) and 0 < len(value) <= 160:
                    safe_metadata[key] = value
        try:
            row = await self.client.insert("artifacts", {
                "id": artifact_id,
                "user_id": user_id,
                "run_id": run_id,
                "storage_path": storage_path,
                "mime_type": mime_type.lower(),
                "size_bytes": len(raw),
                "checksum_sha256": checksum,
                "metadata": safe_metadata,
            })
        except Exception:
            await self.client.client.delete(url, headers=headers, timeout=15.0)
            raise
        return json.dumps({
            "artifact_id": row.get("id", artifact_id),
            "filename": filename,
            "mime_type": mime_type.lower(),
            "size_bytes": len(raw),
            "checksum_sha256": checksum,
            "status": "stored",
        }, ensure_ascii=False, separators=(",", ":"))

    async def file_saver(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        filename = arguments.get("path")
        content = arguments.get("content")
        mime_type = arguments.get("mime_type", "text/plain")
        if not isinstance(content, str):
            raise ValueError("artifact_content_must_be_text")
        raw = content.encode("utf-8")
        if len(raw) > 2_000_000:
            raise ValueError("artifact_content_size_invalid")
        return await self._store_bytes(
            filename=filename, raw=raw, mime_type=mime_type,
            run_id=run_id, user_id=user_id,
        )

    async def save_bytes(
        self, *, filename: str, raw: bytes, mime_type: str, run_id: str, user_id: str,
        metadata: dict[str, Any] | None = None, artifact_id: str | None = None,
    ) -> str:
        """Persist bytes to private Storage with optional deterministic idempotency."""
        return await self._store_bytes(
            filename=filename, raw=raw, mime_type=mime_type,
            run_id=run_id, user_id=user_id, metadata=metadata, artifact_id=artifact_id,
        )

    async def binary_saver(self, arguments: dict[str, Any], *, run_id: str, user_id: str) -> str:
        """Persist a provider-generated binary artifact without exposing public Storage URLs."""
        filename = arguments.get("path")
        content_base64 = arguments.get("content_base64")
        mime_type = arguments.get("mime_type")
        if not isinstance(content_base64, str) or not content_base64 or len(content_base64) > 140_000_000:
            raise ValueError("artifact_base64_content_invalid")
        try:
            raw = base64.b64decode(content_base64, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError("artifact_base64_content_invalid") from exc
        return await self.save_bytes(
            filename=filename, raw=raw, mime_type=mime_type,
            run_id=run_id, user_id=user_id,
            metadata=arguments.get("metadata") if isinstance(arguments.get("metadata"), dict) else None,
            artifact_id=arguments.get("artifact_id") if isinstance(arguments.get("artifact_id"), str) else None,
        )
