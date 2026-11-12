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
