from __future__ import annotations

import re
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/workspaces", tags=["customer-workspaces"])


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


@router.get("")
async def list_customer_workspaces(
    request: Request, user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    owned = await repo.select("workspaces", {
        "owner_user_id": f"eq.{user['id']}",
        "status": "eq.active",
        "select": "id,name,slug,owner_user_id,status,created_at,updated_at",
        "order": "updated_at.desc",
        "limit": "100",
    })
    memberships = await repo.select("workspace_members", {
        "user_id": f"eq.{user['id']}",
        "status": "eq.active",
        "select": "workspace_id",
        "limit": "100",
    })
    known = {str(row["id"]) for row in owned}
    member_ids = [str(row["workspace_id"]) for row in memberships if str(row["workspace_id"]) not in known]
    shared = []
    if member_ids:
        shared = await repo.select("workspaces", {
            "id": f"in.({','.join(member_ids)})",
            "status": "eq.active",
            "select": "id,name,slug,owner_user_id,status,created_at,updated_at",
            "order": "updated_at.desc",
            "limit": "100",
        })
    return {"items": owned + shared, "count": len(owned) + len(shared)}


@router.post("", status_code=201)
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


@router.get("/{workspace_id}/files")
async def list_workspace_files(
    workspace_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    rows = await repo.select("agent_workspace_files", {
        "workspace_id": f"eq.{workspace_id}",
        "user_id": f"eq.{user['id']}",
        "select": "id,path,version,storage_path,sha256,size_bytes,updated_at",
        "order": "updated_at.desc",
        "limit": "500",
    })
    return {"items": rows, "count": len(rows)}


@router.get("/{workspace_id}/files/{file_id}/versions")
async def list_workspace_file_versions(
    workspace_id: UUID, file_id: UUID, request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    await _workspace_access(repo, workspace_id, user["id"])
    current = await repo.select("agent_workspace_files", {
        "id": f"eq.{file_id}",
        "workspace_id": f"eq.{workspace_id}",
        "user_id": f"eq.{user['id']}",
        "select": "id,path,version,storage_path,sha256,size_bytes,updated_at",
        "limit": "1",
    })
    if not current:
        raise HTTPException(404, "Workspace file not found")
    file = current[0]
    history = await repo.select("agent_workspace_file_versions", {
        "workspace_id": f"eq.{workspace_id}",
        "user_id": f"eq.{user['id']}",
        "path": f"eq.{file['path']}",
        "select": "id,path,version,storage_path,sha256,size_bytes,committed_at",
        "order": "version.desc",
        "limit": "100",
    })
    if file.get("version", 0) > 0 and file.get("storage_path") and file.get("sha256"):
        history.insert(0, {
            "id": str(file["id"]),
            "path": file["path"],
            "version": file["version"],
            "storage_path": file["storage_path"],
            "sha256": file["sha256"],
            "size_bytes": file["size_bytes"],
            "committed_at": file["updated_at"],
            "current": True,
        })
    return {"items": history, "count": len(history), "current_version": file["version"]}

@router.post("/{workspace_id}/files/{file_id}/signed-download")
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
        "select": "id,path,version,storage_path,sha256,size_bytes", "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Workspace file not found")
    current = rows[0]
    selected = current
    if version is not None and version != current.get("version"):
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
    bucket = "moreai-artifacts"
    bucket_response = await request.app.state.http.get(base_url + "/storage/v1/bucket/" + bucket, headers=headers, timeout=8.0)
    if bucket_response.status_code >= 400 or not isinstance(bucket_response.json(), dict) or bucket_response.json().get("public") is not False:
        raise HTTPException(503, "Workspace Storage bucket must exist and be private")
    response = await request.app.state.http.post(
        base_url + "/storage/v1/object/sign/" + bucket + "/" + quote(storage_path, safe="/"),
        json={"expiresIn": 60}, headers={**headers, "Content-Type": "application/json"}, timeout=12.0,
    )
    if response.status_code >= 400:
        raise HTTPException(502, "Could not create workspace download link")
    payload = response.json()
    signed_path = payload.get("signedURL") or payload.get("signedUrl")
    if not isinstance(signed_path, str) or not signed_path:
        raise HTTPException(502, "Storage did not return a signed download path")
    signed_url = signed_path if signed_path.startswith("https://") else base_url + "/storage/v1" + (signed_path if signed_path.startswith("/") else "/" + signed_path)
    return {"file_id": str(file_id), "version": selected.get("version", version), "url": signed_url, "expires_in": 60}
