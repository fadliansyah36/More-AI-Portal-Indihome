from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.authorization import customer_principal
from app.routers.conversations import repository

router = APIRouter(prefix="/api/v1/customer/knowledge", tags=["customer-knowledge"])


@router.get("/documents")
async def list_knowledge_documents(
    request: Request,
    workspace_id: UUID | None = None,
    status: str | None = Query(default=None, pattern=r"^(processing|ready|failed|archived)$"),
    limit: int = Query(default=50, ge=1, le=100),
    user: dict[str, Any] = Depends(customer_principal),
):
    """List only the authenticated owner's knowledge documents; never expose chunk vectors."""
    filters = {
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,title,workspace_id,source_type,source_ref,content_sha256,status,metadata,created_at,updated_at",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if workspace_id:
        filters["workspace_id"] = f"eq.{workspace_id}"
    if status:
        filters["status"] = f"eq.{status}"
    rows = await repository(request).select("knowledge_documents", filters)
    return {"items": rows, "count": len(rows)}


@router.get("/documents/{document_id}")
async def get_knowledge_document(
    document_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    rows = await repository(request).select("knowledge_documents", {
        "id": f"eq.{document_id}",
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,title,workspace_id,source_type,source_ref,content_sha256,status,metadata,created_at,updated_at",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Knowledge document not found")
    chunk_rows = await repository(request).select("knowledge_chunks", {
        "document_id": f"eq.{document_id}",
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,chunk_index,token_count,created_at",
        "order": "chunk_index.asc",
        "limit": "500",
    })
    return {"document": rows[0], "chunks": chunk_rows, "chunk_count": len(chunk_rows)}


@router.post("/documents/{document_id}/archive")
async def archive_knowledge_document(
    document_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Soft archive an owned document; keep immutable source/chunk history for audit."""
    rows = await repository(request).update(
        "knowledge_documents",
        {
            "id": f"eq.{document_id}",
            "owner_user_id": f"eq.{user['id']}",
            "status": "in.(ready,failed)",
        },
        {"status": "archived"},
    )
    if not rows:
        existing = await repository(request).select("knowledge_documents", {
            "id": f"eq.{document_id}",
            "owner_user_id": f"eq.{user['id']}",
            "select": "id,status",
            "limit": "1",
        })
        if not existing:
            raise HTTPException(404, "Knowledge document not found")
        if existing[0].get("status") == "archived":
            return {"id": str(document_id), "status": "archived"}
        raise HTTPException(409, "Knowledge document cannot be archived in its current state")
    return {"id": str(document_id), "status": "archived"}
