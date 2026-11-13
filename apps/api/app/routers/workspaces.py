from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Query, Header, Response
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository
from app.pagination import decode_timestamp_id_cursor, encode_timestamp_id_cursor, timestamp_id_filter

router = APIRouter(prefix="/api/v1/customer/workspaces", tags=["customer-workspaces"])


class CustomerWorkspaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_user_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerWorkspaceListResponse(BaseModel):
    items: list[CustomerWorkspaceResponse]
    count: int


class CustomerWorkspaceFileResponse(BaseModel):
    id: UUID
    path: str
    version: int
    storage_path: str | None = None
    sha256: str | None = None
    size_bytes: int | None = None
    updated_at: datetime
    deleted_at: datetime | None = None


class CustomerWorkspaceFileListResponse(BaseModel):
    items: list[CustomerWorkspaceFileResponse]
    count: int


class CustomerWorkspaceFileLifecycleResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    path: str
    version: int
    deleted_at: datetime | None = None
    status: Literal["deleted", "restored"]


class CustomerWorkspaceFileVersionResponse(BaseModel):
    id: UUID
    path: str
    version: int
    storage_path: str
    sha256: str
    size_bytes: int
    committed_at: datetime
    current: bool = False


class CustomerWorkspaceFileVersionListResponse(BaseModel):
    items: list[CustomerWorkspaceFileVersionResponse]
    count: int
    current_version: int


class CustomerWorkspaceSignedDownloadResponse(BaseModel):
    file_id: UUID
    version: int
    url: str
    expires_in: int


class CustomerWorkspaceMemberResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role_id: UUID | None = None
    status: str
    invited_by: UUID | None = None
    joined_at: datetime | None = None
    created_at: datetime


class CustomerWorkspaceMemberListResponse(BaseModel):
    items: list[CustomerWorkspaceMemberResponse]
    count: int


class CustomerWorkspaceRunResponse(BaseModel):
    id: UUID
    conversation_id: UUID | None = None
    status: str
    attempt: int
    max_attempts: int
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    available_at: datetime | None = None
    heartbeat_at: datetime | None = None
    cancel_requested_at: datetime | None = None
    last_checkpoint_key: str | None = None


class CustomerWorkspaceMemberRemovalResponse(BaseModel):
    member_id: UUID
    status: Literal["removed"]


class CustomerWorkspaceRunListResponse(BaseModel):
    items: list[CustomerWorkspaceRunResponse]
    count: int


class CustomerWorkspaceArchiveResponse(BaseModel):
    workspace: CustomerWorkspaceResponse
    archived: bool


class WorkspaceFileUploadResponse(BaseModel):
    workspace_id: UUID
    file_id: UUID
    path: str
    version: int
    storage_path: str
    sha256: str
    size_bytes: int
    updated_at: datetime
    replayed: bool


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:64] or "workspace"
    return f"{base}-{uuid4().hex[:10]}"


async def _workspace_access(repo, workspace_id: UUID, user_id: str) -> dict[str, Any]:
    rows = await repo.select("workspaces", {
        "id": f"eq.{workspace_id}",
        "status": "eq.active",
        "select": "id,name,slug,owner_user_id,status,created_at,updated_at",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Workspace not found")
    workspace = rows[0]
    if workspace.get("owner_user_id") != user_id:
        members = await repo.select("workspace_members", {
            "workspace_id": f"eq.{workspace_id}",
            "user_id": f"eq.{user_id}",
            "status": "eq.active",
            "select": "id",
            "limit": "1",
        })
        if not members:
            raise HTTPException(404, "Workspace not found")
    return workspace


@router.get("", response_model=CustomerWorkspaceListResponse)
async def list_customer_workspaces(
    request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    decoded = decode_timestamp_id_cursor(cursor)
    repo = repository(request)
    cursor_timestamp = decoded[0] if decoded else None
    cursor_id = decoded[1] if decoded else None
    result = await repo.rpc("moreai_customer_workspaces_page", {
        "p_user_id": user["id"],
        "p_limit": limit,
        "p_cursor_updated_at": cursor_timestamp,
        "p_cursor_id": cursor_id,
    })
    if not isinstance(result, list):
        raise HTTPException(502, "Workspace pagination returned an invalid database response")
    rows = result
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "updated_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": rows, "count": len(rows)}


@router.post("", status_code=201, response_model=CustomerWorkspaceResponse)
async def create_customer_workspace(
    body: WorkspaceCreate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Workspace name cannot be empty")
    return await repository(request).insert("workspaces", {
        "name": name,
        "slug": _slug(name),
        "owner_user_id": user["id"],
        "status": "active",
    })


@router.get("/{workspace_id}/files", response_model=CustomerWorkspaceFileListResponse)
async def list_workspace_files(
    workspace_id: UUID, request: Request,
    response: Response,
    include_deleted: bool = Query(default=False),
    path: str | None = Query(default=None, max_length=512),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    decoded = decode_timestamp_id_cursor(cursor)
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    filters = {
        "workspace_id": f"eq.{workspace_id}",
        "select": "id,path,version,storage_path,sha256,size_bytes,updated_at,deleted_at",
        **({} if include_deleted else {"deleted_at": "is.null"}),
        "order": "updated_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = timestamp_id_filter(decoded, "updated_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    if path is not None:
        filters["path"] = f"eq.{path}"
    rows = await repo.select("agent_workspace_files", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "updated_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": rows, "count": len(rows)}


@router.get("/{workspace_id}/files/{file_id}/versions", response_model=CustomerWorkspaceFileVersionListResponse)
async def list_workspace_file_versions(
    workspace_id: UUID, file_id: UUID, request: Request,
    response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    decoded = decode_timestamp_id_cursor(cursor)
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    current = await repo.select("agent_workspace_files", {
        "id": f"eq.{file_id}",
        "workspace_id": f"eq.{workspace_id}",
        "select": "id,path,version,storage_path,sha256,size_bytes,updated_at,deleted_at",
        "limit": "1",
    })
    if not current:
        raise HTTPException(404, "Workspace file not found")
    file = current[0]
    filters = {
        "workspace_id": f"eq.{workspace_id}",
        "path": f"eq.{file['path']}",
        "select": "id,path,version,storage_path,sha256,size_bytes,committed_at",
        "order": "committed_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = timestamp_id_filter(decoded, "committed_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    history = await repo.select("agent_workspace_file_versions", filters)
    has_more = len(history) > limit
    history = history[:limit]
    if cursor is None and file.get("deleted_at") is None and file.get("version", 0) > 0 and file.get("storage_path") and file.get("sha256"):
        history.append({
            "id": str(file["id"]), "path": file["path"], "version": file["version"],
            "storage_path": file["storage_path"], "sha256": file["sha256"],
            "size_bytes": file["size_bytes"], "committed_at": file["updated_at"], "current": True,
        })
        history.sort(key=lambda row: (row.get("committed_at") or "", row.get("id") or ""), reverse=True)
    if len(history) > limit:
        has_more = True
        history = history[:limit]
    if has_more and history:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(history[-1], "committed_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": history, "count": len(history), "current_version": file["version"]}

@router.post("/{workspace_id}/files/{file_id}/delete", response_model=CustomerWorkspaceFileLifecycleResponse)
async def delete_customer_workspace_file(
    workspace_id: UUID,
    file_id: UUID,
    request: Request,
    expected_version: int = Query(ge=0, le=9_223_372_036_854_775_807),
    user: dict[str, Any] = Depends(customer_principal),
):
    await _workspace_access(repository(request), workspace_id, user["id"])
    result = await repository(request).rpc("moreai_customer_workspace_delete_file", {
        "p_user_id": user["id"],
        "p_workspace_id": str(workspace_id),
        "p_file_id": str(file_id),
        "p_expected_version": expected_version,
    })
    if not isinstance(result, dict):
        raise HTTPException(502, "Workspace file deletion returned an invalid database response")
    return result


@router.post("/{workspace_id}/files/{file_id}/restore", response_model=CustomerWorkspaceFileLifecycleResponse)
async def restore_customer_workspace_file(
    workspace_id: UUID,
    file_id: UUID,
    request: Request,
    expected_version: int = Query(ge=1, le=9_223_372_036_854_775_807),
    user: dict[str, Any] = Depends(customer_principal),
):
    from urllib.parse import quote, urlsplit

    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    rows = await repo.select("agent_workspace_files", {
        "id": f"eq.{file_id}",
        "workspace_id": f"eq.{workspace_id}",
        "select": "id,user_id,path,version,storage_path,sha256,size_bytes,deleted_at,pending_token",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Workspace file not found")
    file = rows[0]
    if file.get("version") != expected_version:
        raise HTTPException(409, "Workspace file version changed; refresh and retry")
    if file.get("deleted_at") is None:
        raise HTTPException(409, "Workspace file is not deleted")
    if file.get("pending_token") is not None:
        raise HTTPException(409, "Workspace file has a write in progress")
    _customer_workspace_path(str(file.get("path") or ""))
    source_path = file.get("storage_path")
    checksum = file.get("sha256")
    size_bytes = file.get("size_bytes")
    file_user_id = str(file.get("user_id") or "")
    expected_prefix = file_user_id + "/workspaces/" + str(workspace_id) + "/versions/"
    if (
        not isinstance(source_path, str)
        or not source_path.startswith(expected_prefix)
        or source_path.startswith("/")
        or ".." in source_path.split("/")
        or not isinstance(checksum, str)
        or not re.fullmatch(r"[0-9a-f]{64}", checksum)
        or not isinstance(size_bytes, int)
        or size_bytes < 0
        or size_bytes > _MAX_CUSTOMER_WORKSPACE_UPLOAD
    ):
        raise HTTPException(409, "Deleted workspace file has no valid committed object to restore")

    settings = request.app.state.settings
    if not settings.supabase_data_ready or not settings.supabase_service_role_key:
        raise HTTPException(503, "Workspace Storage is not configured")
    bucket = os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts")
    base_url = settings.supabase_url.rstrip("/")
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": "Bearer " + settings.supabase_service_role_key,
    }
    bucket_response = await request.app.state.http.get(
        base_url + "/storage/v1/bucket/" + quote(bucket, safe=""),
        headers=headers,
        timeout=8.0,
    )
    if bucket_response.status_code >= 400 or not isinstance(bucket_response.json(), dict) or bucket_response.json().get("public") is not False:
        raise HTTPException(503, "Workspace Storage bucket must exist and be private")

    async def read_private_object(object_path: str) -> Any:
        signed_response = await request.app.state.http.post(
            base_url + "/storage/v1/object/sign/" + quote(bucket, safe="") + "/" + quote(object_path, safe="/"),
            json={"expiresIn": 60},
            headers={**headers, "Content-Type": "application/json"},
            timeout=12.0,
        )
        if signed_response.status_code >= 400:
            raise HTTPException(502, "Could not create a private workspace object read link")
        signed_payload = signed_response.json()
        signed_path = signed_payload.get("signedURL") or signed_payload.get("signedUrl")
        if not isinstance(signed_path, str) or not signed_path:
            raise HTTPException(502, "Storage did not return a signed object read path")
        base_parts = urlsplit(base_url)
        signed_parts = urlsplit(signed_path)
        if signed_parts.scheme or signed_parts.netloc:
            if signed_parts.scheme != "https" or signed_parts.netloc.lower() != (base_parts.netloc or "").lower():
                raise HTTPException(502, "Storage returned a signed object URL outside the configured Supabase origin")
            signed_url = signed_path
        else:
            if not signed_path.startswith("/") or signed_path.startswith("//") or "\\" in signed_path:
                raise HTTPException(502, "Storage returned an invalid signed object path")
            signed_url = base_url + "/storage/v1" + signed_path
        object_response = await request.app.state.http.get(signed_url, timeout=30.0)
        if object_response.status_code >= 400:
            raise HTTPException(502, "Private workspace object could not be read")
        return object_response

    source_response = await read_private_object(source_path)
    content = source_response.content
    actual_digest = hashlib.sha256(content).hexdigest()
    if len(content) != size_bytes or actual_digest != checksum:
        raise HTTPException(409, "Stored workspace object failed its recorded size or SHA-256 integrity check")

    next_version = expected_version + 1
    restored_path = (
        file_user_id + "/workspaces/" + str(workspace_id)
        + "/versions/" + str(next_version) + "/" + str(file["path"])
    )
    upload_response = await request.app.state.http.post(
        base_url + "/storage/v1/object/" + quote(bucket, safe="") + "/" + quote(restored_path, safe="/"),
        content=content,
        headers={
            **headers,
            "Content-Type": source_response.headers.get("content-type", "application/octet-stream"),
            "x-upsert": "false",
        },
        timeout=30.0,
    )
    if upload_response.status_code == 409:
        destination_response = await read_private_object(restored_path)
        if hashlib.sha256(destination_response.content).hexdigest() != checksum or len(destination_response.content) != size_bytes:
            raise HTTPException(409, "A different object already occupies the next workspace version path")
    elif upload_response.status_code >= 400:
        raise HTTPException(502, "Restored workspace object could not be written to private Storage")

    result = await repo.rpc("moreai_customer_workspace_restore_file", {
        "p_user_id": user["id"],
        "p_workspace_id": str(workspace_id),
        "p_file_id": str(file_id),
        "p_expected_version": expected_version,
        "p_storage_path": restored_path,
        "p_sha256": checksum,
        "p_size_bytes": size_bytes,
        "p_bucket": bucket,
    })
    if not isinstance(result, dict):
        raise HTTPException(502, "Workspace file restoration returned an invalid database response")
    return result


@router.post("/{workspace_id}/files/{file_id}/signed-download", response_model=CustomerWorkspaceSignedDownloadResponse)
async def create_workspace_file_download(
    workspace_id: UUID, file_id: UUID, request: Request,
    version: int | None = None,
    user: dict[str, Any] = Depends(customer_principal),
):
    from urllib.parse import quote
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    rows = await repo.select("agent_workspace_files", {
        "id": "eq." + str(file_id), "workspace_id": "eq." + str(workspace_id),
        "select": "id,path,version,storage_path,sha256,size_bytes,deleted_at", "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Workspace file not found")
    current = rows[0]
    if current.get("deleted_at") is not None and version is None:
        raise HTTPException(404, "Workspace file not found")
    selected = current
    if version is not None and (
        version != current.get("version") or current.get("deleted_at") is not None
    ):
        history = await repo.select("agent_workspace_file_versions", {
            "workspace_id": "eq." + str(workspace_id), "path": "eq." + current["path"],
            "version": "eq." + str(version),
            "select": "version,storage_path,sha256,size_bytes", "limit": "1",
        })
        if not history:
            raise HTTPException(404, "Workspace file version not found")
        selected = history[0]
    storage_path = selected.get("storage_path")
    expected_segment = "/workspaces/" + str(workspace_id) + "/versions/"
    if not isinstance(storage_path, str) or expected_segment not in storage_path or storage_path.startswith("/") or ".." in storage_path.split("/"):
        raise HTTPException(403, "Workspace object path is outside the workspace scope")
    settings = request.app.state.settings
    if not settings.supabase_data_ready or not settings.supabase_service_role_key:
        raise HTTPException(503, "Workspace Storage is not configured")
    base_url = settings.supabase_url.rstrip("/")
    headers = {"apikey": settings.supabase_service_role_key, "Authorization": "Bearer " + settings.supabase_service_role_key}
    bucket = os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts")
    bucket_response = await request.app.state.http.get(base_url + "/storage/v1/bucket/" + quote(bucket, safe=""), headers=headers, timeout=8.0)
    if bucket_response.status_code >= 400 or not isinstance(bucket_response.json(), dict) or bucket_response.json().get("public") is not False:
        raise HTTPException(503, "Workspace Storage bucket must exist and be private")
    response = await request.app.state.http.post(
        base_url + "/storage/v1/object/sign/" + quote(bucket, safe="") + "/" + quote(storage_path, safe="/"),
        json={"expiresIn": 60}, headers={**headers, "Content-Type": "application/json"}, timeout=12.0,
    )
    if response.status_code >= 400:
        raise HTTPException(502, "Could not create workspace download link")
    payload = response.json()
    signed_path = payload.get("signedURL") or payload.get("signedUrl")
    if not isinstance(signed_path, str) or not signed_path:
        raise HTTPException(502, "Storage did not return a signed download path")
    # Storage is a trusted server-side dependency, but never forward an arbitrary
    # absolute URL to the browser. A compromised/misconfigured Storage response
    # must not turn this endpoint into an external navigation or token-leak vector.
    base_parts = urlsplit(base_url)
    signed_parts = urlsplit(signed_path)
    if signed_parts.scheme or signed_parts.netloc:
        if (
            signed_parts.scheme != "https"
            or signed_parts.netloc.lower() != (base_parts.netloc or "").lower()
            or signed_parts.username is not None
            or signed_parts.password is not None
        ):
            raise HTTPException(502, "Storage returned a signed URL outside the configured Supabase origin")
        signed_url = signed_path
    else:
        if (
            not signed_path.startswith("/")
            or signed_path.startswith("//")
            or "\\" in signed_path
            or any(ord(char) < 32 for char in signed_path)
        ):
            raise HTTPException(502, "Storage returned an invalid signed download path")
        signed_url = base_url + "/storage/v1" + signed_path
    return {"file_id": str(file_id), "version": selected.get("version", version), "url": signed_url, "expires_in": 60}


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=160)


@router.patch("/{workspace_id}", response_model=CustomerWorkspaceResponse)
async def update_customer_workspace(
    workspace_id: UUID, body: WorkspaceUpdate, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Rename an owned workspace; shared members retain read access but cannot mutate its identity."""
    repo = repository(request)
    workspace = await _workspace_access(repo, workspace_id, user["id"])
    if workspace.get("owner_user_id") != user["id"]:
        raise HTTPException(403, "Only the workspace owner can rename this workspace")
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Workspace name cannot be empty")
    rows = await repo.update(
        "workspaces",
        {"id": f"eq.{workspace_id}", "owner_user_id": f"eq.{user['id']}", "status": "eq.active"},
        {"name": name},
    )
    if not rows:
        raise HTTPException(404, "Workspace not found")
    return rows[0]


@router.post("/{workspace_id}/archive", response_model=CustomerWorkspaceArchiveResponse)
async def archive_customer_workspace(
    workspace_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Soft-archive an owned workspace; preserve immutable file versions and audit history."""
    repo = repository(request)
    workspace = await _workspace_access(repo, workspace_id, user["id"])
    if workspace.get("owner_user_id") != user["id"]:
        raise HTTPException(403, "Only the workspace owner can archive this workspace")
    active_runs = await repo.select("agent_runs", {
        "workspace_id": f"eq.{workspace_id}",
        "status": "in.(queued,pending,running,awaiting_approval,waiting_approval)",
        "select": "id", "limit": "1",
    })
    if active_runs:
        raise HTTPException(409, "Workspace has active agent runs; cancel or finish them before archiving")
    rows = await repo.update(
        "workspaces",
        {"id": f"eq.{workspace_id}", "owner_user_id": f"eq.{user['id']}", "status": "eq.active"},
        {"status": "archived"},
    )
    if not rows:
        raise HTTPException(409, "Workspace is not active or cannot be archived")
    return {"workspace": rows[0], "archived": True}


@router.get("/{workspace_id}/members", response_model=CustomerWorkspaceMemberListResponse)
async def list_customer_workspace_members(
    workspace_id: UUID, request: Request, response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    decoded = decode_timestamp_id_cursor(cursor)
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    filters = {
        "workspace_id": f"eq.{workspace_id}",
        "status": "in.(invited,active,suspended)",
        "select": "id,workspace_id,user_id,role_id,status,invited_by,joined_at,created_at",
        "order": "created_at.asc,id.asc",
        "limit": str(limit + 1),
    }
    if decoded:
        # Ascending order uses the inverse keyset predicate.
        timestamp, identifier = decoded
        filters["or"] = f"(created_at.gt.{timestamp},and(created_at.eq.{timestamp},id.gt.{identifier}))"
    rows = await repo.select("workspace_members", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "created_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": rows, "count": len(rows)}


@router.delete("/{workspace_id}/members/{member_id}", response_model=CustomerWorkspaceMemberRemovalResponse)
async def remove_customer_workspace_member(
    workspace_id: UUID, member_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Owner-only membership revocation; historical workspace artifacts remain untouched."""
    repo = repository(request)
    workspace = await _workspace_access(repo, workspace_id, user["id"])
    if workspace.get("owner_user_id") != user["id"]:
        raise HTTPException(403, "Only the workspace owner can remove members")
    member = await repo.select("workspace_members", {
        "id": f"eq.{member_id}",
        "workspace_id": f"eq.{workspace_id}",
        "status": "in.(invited,active,suspended)",
        "select": "id,user_id,status",
        "limit": "1",
    })
    if not member:
        raise HTTPException(404, "Workspace member not found")
    if str(member[0].get("user_id")) == str(user["id"]):
        raise HTTPException(409, "Workspace owner cannot remove their own membership")
    rows = await repo.update(
        "workspace_members",
        {"id": f"eq.{member_id}", "workspace_id": f"eq.{workspace_id}", "status": "in.(invited,active,suspended)"},
        {"status": "removed"},
    )
    if not rows:
        raise HTTPException(409, "Workspace membership changed; refresh and retry")
    return {"member_id": str(member_id), "status": "removed"}


@router.get("/{workspace_id}/runs", response_model=CustomerWorkspaceRunListResponse)
async def list_customer_workspace_runs(
    workspace_id: UUID, request: Request, response: Response,
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """List the caller's durable agent runs associated with an accessible workspace."""
    decoded = decode_timestamp_id_cursor(cursor)
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    filters = {
        "workspace_id": f"eq.{workspace_id}",
        "user_id": f"eq.{user['id']}",
        "select": "id,conversation_id,status,attempt,max_attempts,created_at,started_at,finished_at,available_at,heartbeat_at,cancel_requested_at,last_checkpoint_key",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    cursor_filter = timestamp_id_filter(decoded, "created_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    rows = await repo.select("agent_runs", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "created_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": rows, "count": len(rows)}


_MAX_CUSTOMER_WORKSPACE_UPLOAD = 2_000_000
_WORKSPACE_PATH = re.compile(r"^[A-Za-z0-9._ -]+(?:/[A-Za-z0-9._ -]+)*$")


def _customer_workspace_path(value: str) -> str:
    if (
        not value or len(value) > 512 or value.startswith("/")
        or "\\" in value or "\x00" in value
        or any(part in {"", ".", ".."} for part in value.split("/"))
        or not _WORKSPACE_PATH.fullmatch(value)
    ):
        raise HTTPException(422, "Workspace path contains unsupported characters")
    return value


@router.post("/{workspace_id}/files", status_code=201, response_model=WorkspaceFileUploadResponse)
async def upload_customer_workspace_file(
    workspace_id: UUID,
    request: Request,
    path: str = Header(alias="X-Workspace-Path", max_length=512),
    expected_version: str = Header(alias="If-Match", min_length=1, max_length=24),
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=12, max_length=128),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Commit a customer upload as a new immutable workspace version using CAS."""
    normalized_path = _customer_workspace_path(path)
    if not expected_version.isascii() or not expected_version.isdecimal() or len(expected_version) > 19:
        raise HTTPException(400, "If-Match must contain the expected non-negative workspace file version")
    current_version = int(expected_version)
    if current_version > 9_223_372_036_854_775_806:
        raise HTTPException(422, "Workspace version is outside the supported range")

    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    content = await request.body()
    if not content or len(content) > _MAX_CUSTOMER_WORKSPACE_UPLOAD:
        raise HTTPException(413, "Workspace files must contain between 1 byte and 2 MB")

    mime_type = request.headers.get("content-type", "application/octet-stream").split(";", 1)[0].strip().lower()
    if not re.fullmatch(r"[a-z0-9.+-]+/[a-z0-9.+-]+", mime_type):
        raise HTTPException(400, "Content-Type is invalid")

    settings = request.app.state.settings
    if not settings.supabase_data_ready or not settings.supabase_service_role_key:
        raise HTTPException(503, "Workspace Storage is not configured")
    bucket = os.getenv("MOREAI_WORKSPACE_BUCKET", "moreai-artifacts")
    base_url = settings.supabase_url.rstrip("/")
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": "Bearer " + settings.supabase_service_role_key,
    }
    bucket_response = await request.app.state.http.get(
        base_url + "/storage/v1/bucket/" + quote(bucket, safe=""),
        headers=headers,
        timeout=8.0,
    )
    if bucket_response.status_code >= 400:
        raise HTTPException(503, "Workspace Storage bucket is unavailable")
    bucket_payload = bucket_response.json()
    if not isinstance(bucket_payload, dict) or bucket_payload.get("public") is not False:
        raise HTTPException(503, "Workspace Storage bucket must be private")

    next_version = current_version + 1
    storage_path = (
        user["id"] + "/workspaces/" + str(workspace_id)
        + "/versions/" + str(next_version) + "/" + normalized_path
    )
    object_url = (
        base_url + "/storage/v1/object/" + quote(bucket, safe="")
        + "/" + quote(storage_path, safe="/")
    )
    checksum = hashlib.sha256(content).hexdigest()
    upload_response = await request.app.state.http.post(
        object_url,
        content=content,
        headers={
            **headers,
            "Content-Type": mime_type,
            "x-upsert": "false",
        },
        timeout=30.0,
    )
    uploaded_by_this_request = upload_response.status_code < 400
    if upload_response.status_code == 409:
        # Idempotent retries may find the immutable object already present.
        # Reuse it only when the stored bytes exactly match this request.
        existing = await request.app.state.http.get(object_url, headers=headers, timeout=20.0)
        if existing.status_code >= 400 or len(existing.content) != len(content) or hashlib.sha256(existing.content).hexdigest() != checksum:
            raise HTTPException(409, "Workspace version object already exists with different content")
    elif upload_response.status_code >= 400:
        raise HTTPException(502, "Workspace Storage upload failed")

    try:
        result = await repo.rpc("moreai_customer_workspace_commit_upload", {
            "p_user_id": user["id"],
            "p_workspace_id": str(workspace_id),
            "p_path": normalized_path,
            "p_expected_version": current_version,
            "p_idempotency_key": idempotency_key,
            "p_storage_path": storage_path,
            "p_sha256": checksum,
            "p_size_bytes": len(content),
        })
    except Exception:
        # The RPC response may be lost after PostgreSQL commits. Never delete an
        # immutable object on an ambiguous commit result; a retry with the same
        # idempotency key can replay the committed result, and orphan cleanup is
        # handled separately from this request path.
        raise

    if not isinstance(result, dict) or result.get("file_id") is None or result.get("version") != next_version:
        raise HTTPException(502, "Workspace upload commit returned an invalid result")
    return result
