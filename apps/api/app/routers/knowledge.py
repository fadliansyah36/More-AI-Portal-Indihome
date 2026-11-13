from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from app.authorization import customer_principal
from app.routers.conversations import repository
from app.pagination import decode_timestamp_id_cursor, encode_timestamp_id_cursor, timestamp_id_filter

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from fastapi import File, Form, UploadFile
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/customer/knowledge", tags=["customer-knowledge"])




class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    title: str
    workspace_id: UUID | None = None
    source_type: str
    source_ref: str | None = None
    content_sha256: str | None = None
    status: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class KnowledgeUploadInfoResponse(BaseModel):
    filename: str
    size_bytes: int
    mime_type: str


class KnowledgeUploadResponse(BaseModel):
    document: KnowledgeDocumentResponse
    status: str
    reused: bool
    upload: KnowledgeUploadInfoResponse


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentResponse]
    count: int


class KnowledgeChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    token_count: int | None = None
    created_at: datetime


class KnowledgeDocumentDetailResponse(BaseModel):
    document: KnowledgeDocumentResponse
    chunks: list[KnowledgeChunkResponse]
    chunk_count: int
    total_chunk_count: int
    next_after_chunk_index: int | None = None


class KnowledgeDocumentStateResponse(BaseModel):
    id: UUID
    status: str
    ingestion_state: str | None = None


MAX_KNOWLEDGE_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_KNOWLEDGE_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
KNOWLEDGE_BUCKET = "moreai-knowledge-private"


def _storage_headers(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    key = settings.supabase_service_role_key
    return {"apikey": key, "Authorization": f"Bearer {key}"}


async def _validate_workspace_access(request: Request, workspace_id: UUID, user_id: str) -> None:
    rows = await repository(request).select("workspaces", {
        "id": f"eq.{workspace_id}",
        "status": "eq.active",
        "select": "id,owner_user_id",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Workspace not found")
    if rows[0].get("owner_user_id") != user_id:
        # Active membership is required for non-owner workspace access.
        memberships = await repository(request).select("workspace_members", {
            "workspace_id": f"eq.{workspace_id}",
            "user_id": f"eq.{user_id}",
            "status": "eq.active",
            "select": "workspace_id",
            "limit": "1",
        })
        if not memberships:
            raise HTTPException(404, "Workspace not found")


@router.post("/documents/upload", status_code=202, response_model=KnowledgeUploadResponse)
async def upload_knowledge_document(
    request: Request,
    file: UploadFile = File(...),
    workspace_id: UUID | None = Form(default=None),
    title: str | None = Form(default=None, max_length=500),
    user: dict[str, Any] = Depends(customer_principal),
):
    """Accept native multipart file bytes; never accept a client-supplied Storage URL."""
    settings = request.app.state.settings
    if not settings.supabase_data_ready or not settings.supabase_service_role_key:
        raise HTTPException(503, "Knowledge storage is not configured")
    mime = (file.content_type or "").split(";", 1)[0].strip().lower()
    if mime not in ALLOWED_KNOWLEDGE_TYPES:
        raise HTTPException(415, "Only PDF, JPEG, PNG and WEBP files are supported")
    filename = Path(file.filename or "upload").name
    if not filename or len(filename) > 255 or filename in {".", ".."}:
        raise HTTPException(422, "Invalid file name")
    if workspace_id:
        await _validate_workspace_access(request, workspace_id, user["id"])

    content = await file.read(MAX_KNOWLEDGE_UPLOAD_BYTES + 1)
    if not content:
        raise HTTPException(422, "Uploaded file is empty")
    if len(content) > MAX_KNOWLEDGE_UPLOAD_BYTES:
        raise HTTPException(413, "Maximum upload size is 25 MiB")
    if mime == "application/pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(415, "File content does not match PDF type")
    if mime == "image/jpeg" and not content.startswith(b"\xff\xd8\xff"):
        raise HTTPException(415, "File content does not match JPEG type")
    if mime == "image/png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(415, "File content does not match PNG type")
    if mime == "image/webp" and (len(content) < 12 or content[:4] != b"RIFF" or content[8:12] != b"WEBP"):
        raise HTTPException(415, "File content does not match WEBP type")

    digest = hashlib.sha256(content).hexdigest()
    existing = await repository(request).select("knowledge_documents", {
        "owner_user_id": f"eq.{user['id']}",
        "workspace_id": "is.null" if workspace_id is None else f"eq.{workspace_id}",
        "source_type": "eq.file",
        "content_sha256": f"eq.{digest}",
        "status": "in.(processing,ready,failed)",
        "select": "id,title,workspace_id,source_type,status,content_sha256,metadata,created_at,updated_at",
        "order": "created_at.desc",
        "limit": "1",
    })
    if existing:
        return {
            "document": existing[0],
            "status": existing[0].get("status"),
            "reused": True,
            "upload": {"filename": filename, "size_bytes": len(content), "mime_type": mime},
        }
    document_id = str(uuid4())
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)[:180]
    storage_path = f"{user['id']}/{document_id}/{safe_name}"
    title_value = (title or Path(filename).stem).strip()
    if not title_value:
        raise HTTPException(422, "Document title cannot be empty")

    repo = repository(request)
    # Validate the workspace before creating metadata or uploading bytes.
    metadata = {
        "ingestion_state": "uploading",
        "mime_type": mime,
        "original_filename": filename,
        "size_bytes": len(content),
        "storage_bucket": KNOWLEDGE_BUCKET,
        "storage_path": storage_path,
        "sha256": digest,
        "page_count": None,
        "ocr_status": "pending" if mime.startswith("image/") else "not_applicable",
    }
    document = await repo.insert("knowledge_documents", {
        "id": document_id,
        "owner_user_id": user["id"],
        "workspace_id": str(workspace_id) if workspace_id else None,
        "title": title_value,
        "source_type": "file",
        "source_ref": storage_path,
        "content_sha256": digest,
        "status": "processing",
        "metadata": metadata,
    })
    try:
        response = await request.app.state.http.post(
            f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{KNOWLEDGE_BUCKET}/{storage_path}",
            content=content,
            headers={
                **_storage_headers(request),
                "Content-Type": mime,
                "x-upsert": "false",
            },
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise HTTPException(502, "Private file storage rejected the upload")
        await repo.update(
            "knowledge_documents",
            {"id": f"eq.{document_id}", "owner_user_id": f"eq.{user['id']}", "status": "eq.processing"},
            {"metadata": {**metadata, "ingestion_state": "queued", "uploaded_at": datetime.now(timezone.utc).isoformat()}},
        )
        updated_rows = await repo.select("knowledge_documents", {
            "id": f"eq.{document_id}", "owner_user_id": f"eq.{user['id']}",
            "select": "id,title,workspace_id,source_type,status,content_sha256,metadata,created_at,updated_at",
            "limit": "1",
        })
        if not updated_rows:
            raise HTTPException(502, "Uploaded document metadata could not be reloaded")
    except Exception:
        # Keep the durable row for diagnosis/retry; do not expose storage credentials or response bodies.
        await repo.update(
            "knowledge_documents",
            {"id": f"eq.{document_id}", "owner_user_id": f"eq.{user['id']}"},
            {"status": "failed", "metadata": {**metadata, "ingestion_state": "upload_failed", "error_code": "storage_upload_failed"}},
        )
        raise
    return {
        "document": updated_rows[0],
        "status": "processing",
        "reused": False,
        "upload": {"filename": filename, "size_bytes": len(content), "mime_type": mime},
    }


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_knowledge_documents(
    request: Request,
    response: Response,
    workspace_id: UUID | None = None,
    status: str | None = Query(default=None, pattern=r"^(processing|ready|failed|archived)$"),
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=512),
    user: dict[str, Any] = Depends(customer_principal),
):
    """List only the authenticated owner's knowledge documents; never expose chunk vectors."""
    decoded = decode_timestamp_id_cursor(cursor)
    filters = {
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,title,workspace_id,source_type,source_ref,content_sha256,status,metadata,created_at,updated_at",
        "order": "created_at.desc,id.desc",
        "limit": str(limit + 1),
    }
    if workspace_id:
        filters["workspace_id"] = f"eq.{workspace_id}"
    if status:
        filters["status"] = f"eq.{status}"
    cursor_filter = timestamp_id_filter(decoded, "created_at")
    if cursor_filter:
        filters["or"] = cursor_filter
    rows = await repository(request).select("knowledge_documents", filters)
    has_more = len(rows) > limit
    rows = rows[:limit]
    if has_more and rows:
        response.headers["X-Next-Cursor"] = encode_timestamp_id_cursor(rows[-1], "created_at")
    response.headers["X-Pagination-Mode"] = "keyset"
    return {"items": rows, "count": len(rows)}


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentDetailResponse)
async def get_knowledge_document(
    document_id: UUID,
    request: Request,
    response: Response,
    limit: int = Query(default=100, ge=1, le=200),
    after_chunk_index: int | None = Query(default=None, ge=0),
    user: dict[str, Any] = Depends(customer_principal),
):
    repo = repository(request)
    rows = await repo.select("knowledge_documents", {
        "id": f"eq.{document_id}",
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,title,workspace_id,source_type,source_ref,content_sha256,status,metadata,created_at,updated_at",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Knowledge document not found")
    chunk_filters = {
        "document_id": f"eq.{document_id}",
        "owner_user_id": f"eq.{user['id']}",
        "select": "id,chunk_index,token_count,created_at",
        "order": "chunk_index.asc",
        "limit": str(limit + 1),
    }
    if after_chunk_index is not None:
        chunk_filters["chunk_index"] = f"gt.{after_chunk_index}"
    chunk_rows = await repo.select("knowledge_chunks", chunk_filters)
    has_more = len(chunk_rows) > limit
    chunk_rows = chunk_rows[:limit]
    next_after = chunk_rows[-1]["chunk_index"] if has_more and chunk_rows else None
    if next_after is not None:
        response.headers["X-Next-Cursor"] = str(next_after)
    response.headers["X-Pagination-Mode"] = "keyset"
    total_count = await repo.rpc("moreai_customer_knowledge_chunk_count", {
        "p_user_id": user["id"],
        "p_document_id": str(document_id),
    })
    if isinstance(total_count, bool) or not isinstance(total_count, int):
        raise HTTPException(502, "Knowledge chunk count returned an invalid database response")
    return {
        "document": rows[0],
        "chunks": chunk_rows,
        "chunk_count": len(chunk_rows),
        "total_chunk_count": total_count,
        "next_after_chunk_index": next_after,
    }


@router.post("/documents/{document_id}/retry", status_code=202, response_model=KnowledgeDocumentStateResponse)
async def retry_knowledge_document(
    document_id: UUID,
    request: Request,
    user: dict[str, Any] = Depends(customer_principal),
):
    """Requeue a failed owner-scoped file from its already-private Storage object."""
    repo = repository(request)
    rows = await repo.select("knowledge_documents", {
        "id": f"eq.{document_id}",
        "owner_user_id": f"eq.{user['id']}",
        "source_type": "eq.file",
        "status": "eq.failed",
        "select": "id,workspace_id,metadata",
        "limit": "1",
    })
    if not rows:
        raise HTTPException(404, "Failed knowledge file not found")
    metadata = rows[0].get("metadata") if isinstance(rows[0].get("metadata"), dict) else {}
    if metadata.get("storage_bucket") != KNOWLEDGE_BUCKET or not isinstance(metadata.get("storage_path"), str):
        raise HTTPException(409, "Private source object is unavailable for reprocessing")
    workspace_id = rows[0].get("workspace_id")
    if workspace_id:
        await _validate_workspace_access(request, UUID(str(workspace_id)), user["id"])
    updated = await repo.update(
        "knowledge_documents",
        {
            "id": f"eq.{document_id}",
            "owner_user_id": f"eq.{user['id']}",
            "source_type": "eq.file",
            "status": "eq.failed",
        },
        {
            "status": "processing",
            "ingestion_attempt": 0,
            "ingestion_lease_until": None,
            "ingestion_error_code": None,
            "metadata": {
                **metadata,
                "ingestion_state": "queued",
                "retry_after": None,
                "error_code": None,
                "requeued_at": datetime.now(timezone.utc).isoformat(),
            },
        },
    )
    if not updated:
        raise HTTPException(409, "Knowledge file state changed; refresh and retry")
    return {"id": str(document_id), "status": "processing", "ingestion_state": "queued"}


@router.post("/documents/{document_id}/archive", response_model=KnowledgeDocumentStateResponse)
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
