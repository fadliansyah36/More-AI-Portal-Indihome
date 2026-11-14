from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query, Response
from pydantic import BaseModel

from app.authorization import customer_principal
from app.routers.conversations import repository
from app.pagination import decode_created_at_id_cursor, encode_created_at_id_cursor, created_at_id_filter

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])
MAX_ARTIFACT_BYTES = 2_000_000
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,179}$")


class CustomerArtifactResponse(BaseModel):
    id: UUID
    run_id: UUID | None
    storage_path: str
    mime_type: str | None
    size_bytes: int | None
    checksum_sha256: str | None
    metadata: dict[str, Any]
    created_at: datetime


class CustomerArtifactDownloadResponse(BaseModel):
    artifact_id: UUID
    url: str
    expires_in: int



def _storage_headers(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    if not settings.supabase_data_ready or not settings.artifacts_bucket:
        raise HTTPException(503, "Artifact Storage is not configured")
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


def _storage_url(request: Request, suffix: str) -> str:
    settings = request.app.state.settings
    bucket = quote(settings.artifacts_bucket, safe="")
    return f"{settings.supabase_url}/storage/v1/{suffix.format(bucket=bucket)}"

async def _require_private_bucket(request: Request, headers: dict[str, str]) -> None:
    response = await request.app.state.http.get(
        _storage_url(request, "bucket/{bucket}"),
        headers=headers,
        timeout=8.0,
    )
    if response.status_code == 404:
        raise HTTPException(503, "Configured artifact bucket does not exist")
    if response.status_code >= 400:
        raise HTTPException(503, "Could not verify artifact bucket privacy")
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("public") is not False:
        raise HTTPException(503, "Artifact bucket must be private")



def _validate_owner_path(user_id: str, path: str) -> str:
    if (
        not path or path.startswith("/") or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
        or not path.startswith(f"{user_id}/")
    ):
        raise HTTPException(403, "Artifact storage path is outside the authenticated owner scope")
    return path


@router.get("", response_model=list[CustomerArtifactResponse])
async def list_artifacts(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Return owned artifacts with stable keyset pagination and durable Agent Run links."""
    decoded = decode_created_at_id_cursor(cursor)
    filters = {
        "user_id": f"eq.{user['id']}",
        "select": "id,run_id,storage_path,mime_type,size_bytes,checksum_sha256,metadata,created_at",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = created_at_id_filter(decoded)
    if cursor_filter:
        filters["or"] = cursor_filter
    repo = repository(request)
    rows = await repo.select("artifacts", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_created_at_id_cursor(rows[-1])
    response.headers["X-Pagination-Mode"] = "keyset"
    # Chat attachments are linked atomically through the message/run junction.
    # Resolve only links for this page, rather than scanning a fixed global slice.
    artifact_ids = [str(row["id"]) for row in rows if row.get("id")]
    attachment_links = await repo.select("conversation_message_attachments", {
        "user_id": f"eq.{user['id']}",
        "artifact_id": f"in.({','.join(artifact_ids)})" if artifact_ids else "in.(00000000-0000-0000-0000-000000000000)",
        "select": "artifact_id,run_id",
        "order": "created_at.desc",
        "limit": str(max(1, len(artifact_ids) * 10)),
    }) if artifact_ids else []
    linked_run_by_artifact = {
        str(link["artifact_id"]): str(link["run_id"])
        for link in attachment_links
        if link.get("artifact_id") and link.get("run_id")
    }
    return [
        {
            **row,
            "run_id": row.get("run_id") or linked_run_by_artifact.get(str(row.get("id"))),
        }
        for row in rows
    ]


@router.post("", status_code=201, response_model=CustomerArtifactResponse)
async def upload_artifact(
    request: Request,
    filename: str = Header(alias="X-Filename", max_length=180),
    purpose: str | None = Header(default=None, alias="X-Artifact-Purpose"),
    conversation_id: UUID | None = Header(default=None, alias="X-Conversation-Id"),
    agent_run_id: UUID | None = Header(default=None, alias="X-Agent-Run-Id"),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Upload raw bytes to private owner-scoped Storage, then persist metadata."""
    if not _SAFE_FILENAME.fullmatch(filename) or filename in {".", ".."}:
        raise HTTPException(400, "Filename contains unsupported characters")
    declared_length = request.headers.get("content-length")
    if declared_length:
        try:
            if int(declared_length) > MAX_ARTIFACT_BYTES:
                raise HTTPException(413, "Artifact must contain between 1 byte and 2 MB")
        except ValueError as exc:
            raise HTTPException(400, "Content-Length is invalid") from exc
    if conversation_id is not None and purpose is None:
        raise HTTPException(422, "Conversation-scoped uploads require an explicit artifact purpose")
    content = await request.body()
    if not content or len(content) > MAX_ARTIFACT_BYTES:
        raise HTTPException(413, "Artifact must contain between 1 byte and 2 MB")
    headers = _storage_headers(request)
    await _require_private_bucket(request, headers)
    artifact_id = str(uuid4())
    storage_path = f"{user['id']}/{artifact_id}/{filename}"
    mime_type = request.headers.get("content-type", "application/octet-stream").split(";", 1)[0].strip().lower()
    if not re.fullmatch(r"[a-z0-9.+-]+/[a-z0-9.+-]+", mime_type):
        raise HTTPException(400, "Content-Type is invalid")
    metadata: dict[str, Any] = {"filename": filename}
    if agent_run_id is not None:
        # Explicit run linkage is accepted only for a run owned by this principal.
        await repository(request).owned_record("agent_runs", agent_run_id, user["id"])
        metadata["run_id"] = str(agent_run_id)
    if purpose is not None:
        if purpose != "chat_attachment" or conversation_id is None:
            raise HTTPException(422, "Chat attachments require a conversation and the chat_attachment purpose")
        await repository(request).owned_record("conversations", conversation_id, user["id"])
        allowed_types = {
            "text/plain", "text/markdown", "text/csv", "application/json",
            "application/pdf", "image/jpeg", "image/png", "image/webp",
        }
        if mime_type not in allowed_types:
            raise HTTPException(415, "Chat attachments support text, PDF, JPEG, PNG, and WebP files")
        if mime_type in {"text/plain", "text/markdown", "text/csv", "application/json"}:
            try:
                content.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise HTTPException(415, "Text attachments must use UTF-8 encoding") from exc
        elif mime_type == "application/pdf" and not content.startswith(b"%PDF-"):
            raise HTTPException(415, "PDF signature is invalid")
        elif mime_type == "image/jpeg" and not content.startswith(b"\xff\xd8\xff"):
            raise HTTPException(415, "JPEG signature is invalid")
        elif mime_type == "image/png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(415, "PNG signature is invalid")
        elif mime_type == "image/webp" and not (content.startswith(b"RIFF") and content[8:12] == b"WEBP"):
            raise HTTPException(415, "WebP signature is invalid")
        metadata.update({"purpose": "chat_attachment", "conversation_id": str(conversation_id)})
    object_url = _storage_url(request, "object/{bucket}/" + quote(storage_path, safe="/"))
    response = await request.app.state.http.post(
        object_url, content=content,
        headers={**headers, "Content-Type": mime_type, "x-upsert": "false"},
        timeout=30.0,
    )
    if response.status_code == 409:
        raise HTTPException(409, "Artifact object already exists")
    if response.status_code >= 400:
        raise HTTPException(502, "Artifact Storage upload failed")
    checksum = hashlib.sha256(content).hexdigest()
    try:
        return await repository(request).insert("artifacts", {
            "id": artifact_id,
            "user_id": user["id"],
            "run_id": str(agent_run_id) if agent_run_id else None,
            "storage_path": storage_path,
            "mime_type": mime_type,
            "size_bytes": len(content),
            "checksum_sha256": checksum,
            "metadata": metadata,
        })
    except Exception:
        # Compensate the object write if metadata persistence fails.
        await request.app.state.http.delete(object_url, headers=headers, timeout=15.0)
        raise


@router.post("/{artifact_id}/signed-download", response_model=CustomerArtifactDownloadResponse)
async def create_artifact_download(
    artifact_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Issue a 60-second signed URL only after checking metadata ownership."""
    repo = repository(request)
    record = await repo.owned_record("artifacts", artifact_id, user["id"])
    storage_path = _validate_owner_path(user["id"], str(record.get("storage_path") or ""))
    headers = _storage_headers(request)
    await _require_private_bucket(request, headers)
    response = await request.app.state.http.post(
        _storage_url(request, "object/sign/{bucket}/" + quote(storage_path, safe="/")),
        json={"expiresIn": 60},
        headers={**headers, "Content-Type": "application/json"},
        timeout=12.0,
    )
    if response.status_code >= 400:
        raise HTTPException(502, "Could not create artifact download link")
    payload = response.json()
    signed_path = payload.get("signedURL") or payload.get("signedUrl")
    if not isinstance(signed_path, str) or not signed_path:
        raise HTTPException(502, "Storage did not return a signed download path")
    signed_url = signed_path if signed_path.startswith("https://") else (
        f"{request.app.state.settings.supabase_url}/storage/v1"
        f"{signed_path if signed_path.startswith('/') else '/' + signed_path}"
    )
    return {"artifact_id": str(artifact_id), "url": signed_url, "expires_in": 60}
