from __future__ import annotations

import hashlib
import io
import os
import re
from typing import Any

from app.client import WorkerRpcClient


class CustomerChatAttachmentLoader:
    """Load owner-scoped private artifacts linked to a durable Chat run."""

    ALLOWED_MIME_TYPES = {
        "text/plain", "text/markdown", "text/csv", "application/json",
        "application/pdf", "image/jpeg", "image/png", "image/webp",
    }
    MAX_FILE_BYTES = 2_000_000
    MAX_EXTRACTED_PER_FILE = 25_000
    MAX_EXTRACTED_TOTAL = 80_000

    def __init__(self, client: WorkerRpcClient):
        self.client = client
        self.bucket = os.getenv("MOREAI_ARTIFACTS_BUCKET", "moreai-artifacts")

    async def load(self, run_id: str, user_id: str) -> list[dict[str, Any]]:
        links = await self.client.select("conversation_message_attachments", {
            "run_id": f"eq.{run_id}",
            "user_id": f"eq.{user_id}",
            "select": "artifact_id,conversation_id",
            "order": "created_at.asc",
            "limit": "10",
        })
        if not links:
            return []
        artifact_ids = sorted({str(row.get("artifact_id") or "") for row in links})
        if len(artifact_ids) != len(links) or any(not item for item in artifact_ids):
            raise ValueError("chat_attachment_link_set_invalid")
        artifacts = await self.client.select("artifacts", {
            "id": f"in.({','.join(artifact_ids)})",
            "user_id": f"eq.{user_id}",
            "select": "id,storage_path,mime_type,size_bytes,checksum_sha256,metadata",
            "limit": "10",
        })
        by_id = {str(row.get("id")): row for row in artifacts if row.get("id")}
        if set(by_id) != set(artifact_ids):
            raise PermissionError("chat_attachment_owner_scope_invalid")

        output: list[dict[str, Any]] = []
        total_chars = 0
        for link in links:
            artifact_id = str(link["artifact_id"])
            row = by_id[artifact_id]
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            if metadata.get("purpose") != "chat_attachment":
                raise PermissionError("chat_attachment_purpose_invalid")
            if str(metadata.get("conversation_id") or "") != str(link.get("conversation_id") or ""):
                raise PermissionError("chat_attachment_conversation_scope_invalid")
            mime_type = str(row.get("mime_type") or "").lower()
            if mime_type not in self.ALLOWED_MIME_TYPES:
                raise ValueError("chat_attachment_mime_type_unsupported")
            size = row.get("size_bytes")
            if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= self.MAX_FILE_BYTES:
                raise ValueError("chat_attachment_size_invalid")
            path = str(row.get("storage_path") or "")
            if (
                not path.startswith(user_id + "/")
                or path.startswith("/")
                or "\\" in path
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                raise PermissionError("chat_attachment_storage_path_invalid")

            raw = await self._download(path)
            if len(raw) != size:
                raise ValueError("chat_attachment_size_mismatch")
            expected_digest = row.get("checksum_sha256")
            if not isinstance(expected_digest, str) or hashlib.sha256(raw).hexdigest() != expected_digest:
                raise ValueError("chat_attachment_checksum_mismatch")
            extracted = self._extract(raw, mime_type)
            remaining = self.MAX_EXTRACTED_TOTAL - total_chars
            extracted = extracted[: min(self.MAX_EXTRACTED_PER_FILE, max(0, remaining))]
            total_chars += len(extracted)
            output.append({
                "artifact_id": artifact_id,
                "filename": str(metadata.get("filename") or "attachment"),
                "mime_type": mime_type,
                "content": extracted,
            })
            if total_chars >= self.MAX_EXTRACTED_TOTAL:
                break
        return output

    async def _download(self, path: str) -> bytes:
        url = (
            f"{self.client.settings.supabase_url.rstrip('/')}/storage/v1/object/"
            f"{self.bucket}/{path}"
        )
        headers = {
            "apikey": self.client.settings.service_role_key,
            "Authorization": f"Bearer {self.client.settings.service_role_key}",
        }
        response = await self.client.client.get(url, headers=headers, timeout=45.0)
        response.raise_for_status()
        if len(response.content) > self.MAX_FILE_BYTES:
            raise ValueError("chat_attachment_download_exceeds_limit")
        return response.content

    @staticmethod
    def _extract(raw: bytes, mime_type: str) -> str:
        if mime_type in {"text/plain", "text/markdown", "text/csv", "application/json"}:
            return raw.decode("utf-8", errors="strict")
        if mime_type == "application/pdf":
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if getattr(reader, "is_encrypted", False) or len(reader.pages) > 50:
                raise ValueError("chat_attachment_pdf_invalid_or_too_many_pages")
            return "\n\n".join((page.extract_text() or "") for page in reader.pages)
        from PIL import Image
        import pytesseract
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            if image.width < 1 or image.height < 1 or image.width * image.height > 25_000_000:
                raise ValueError("chat_attachment_image_pixel_limit_exceeded")
            return pytesseract.image_to_string(image, lang="eng+ind")

