from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/artifacts", tags=["artifacts"])
MAX_ARTIFACT_BYTES = 2_000_000
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,179}$")


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


@router.get("")
async def list_artifacts(request: Request, user: dict[str, Any] = Depends(customer_principal)):
    """Return only artifact metadata owned by the authenticated principal."""
    return await repository(request).select("artifacts", {
        "user_id": f"eq.{user['id']}",
        "select": "id,storage_path,mime_type,size_bytes,checksum_sha256,metadata,created_at",
        "order": "created_at.desc",
        "limit": "200",
    })


@router.post("", status_code=201)
async def upload_artifact(
    request: Request,
    filename: str = Header(alias="X-Filename", max_length=180),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Upload raw bytes to private owner-scoped Storage, then persist metadata."""
    if not _SAFE_FILENAME.fullmatch(filename) or filename in {".", ".."}:
        raise HTTPException(400, "Filename contains unsupported characters")
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
            "storage_path": storage_path,
            "mime_type": mime_type,
            "size_bytes": len(content),
            "checksum_sha256": checksum,
            "metadata": {"filename": filename},
        })
    except Exception:
        # Compensate the object write if metadata persistence fails.
        await request.app.state.http.delete(object_url, headers=headers, timeout=15.0)
        raise


@router.post("/{artifact_id}/signed-download")
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
