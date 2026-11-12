from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import re
from typing import Any

import httpx

from app.client import WorkerRpcClient


class SupabaseKnowledgeTools:
    """Tenant-scoped text ingestion and pgvector retrieval for durable OpenManus runs."""

    def __init__(self, client: WorkerRpcClient, http: httpx.AsyncClient):
        self.client = client
        self.http = http

    def _embedding_config(self) -> tuple[str, str, str]:
        base_url = os.getenv("MOREAI_EMBEDDING_BASE_URL", "").rstrip("/")
        model = os.getenv("MOREAI_EMBEDDING_MODEL", "")
        secret_name = os.getenv("MOREAI_EMBEDDING_SECRET_ENV", "MOREAI_EMBEDDING_API_KEY")
        if not base_url.startswith("https://") or not model:
            raise RuntimeError("knowledge_embedding_provider_not_configured")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,100}", secret_name):
            raise RuntimeError("knowledge_embedding_secret_reference_invalid")
        api_key = os.getenv(secret_name)
        if not api_key:
            raise RuntimeError("knowledge_embedding_secret_missing")
        return base_url, model, api_key

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or len(texts) > 64:
            raise ValueError("knowledge_embedding_batch_out_of_range")
        base_url, model, api_key = self._embedding_config()
        try:
            response = await self.http.post(
                f"{base_url}/embeddings",
                json={"model": model, "input": texts},
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                timeout=60.0,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise RuntimeError("knowledge_embedding_provider_unavailable") from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list) or len(data) != len(texts):
            raise RuntimeError("knowledge_embedding_response_shape_invalid")
        ordered = sorted(data, key=lambda item: int(item.get("index", 0)))
        vectors: list[list[float]] = []
        for item in ordered:
            vector = item.get("embedding") if isinstance(item, dict) else None
            if not isinstance(vector, list) or len(vector) != 1536:
                raise RuntimeError("knowledge_embedding_dimension_must_be_1536")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in vector):
                raise RuntimeError("knowledge_embedding_vector_invalid")
            vectors.append([float(value) for value in vector])
        return vectors

    @staticmethod
    def _chunks(content: str, size: int = 2400, overlap: int = 250) -> list[str]:
        normalized = re.sub(r"\s+", " ", content).strip()
        if not normalized:
            raise ValueError("knowledge_content_empty")
        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            if end < len(normalized):
                boundary = normalized.rfind(" ", start + size // 2, end)
                if boundary > start:
                    end = boundary
            chunk = normalized[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(normalized):
                break
            start = max(start + 1, end - overlap)
        if len(chunks) > 500:
            raise ValueError("knowledge_document_exceeds_500_chunks")
        return chunks

    async def knowledge_ingest(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
        workspace_id: str | None = None,
    ) -> str:
        title = arguments.get("title")
        content = arguments.get("content")
        if not isinstance(title, str) or not title.strip() or len(title) > 500:
            raise ValueError("knowledge_title_invalid")
        if not isinstance(content, str) or not 1 <= len(content) <= 1_000_000:
            raise ValueError("knowledge_content_must_be_1_to_1000000_chars")
        chunks = self._chunks(content)
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        existing = await self.client.select("knowledge_documents", {
            "owner_user_id": f"eq.{user_id}",
            "workspace_id": "is.null" if workspace_id is None else f"eq.{workspace_id}",
            "content_sha256": f"eq.{digest}",
            "select": "id,title,status",
            "limit": "1",
        })
        if existing:
            if existing[0].get("status") == "ready":
                return json.dumps({
                    "document_id": existing[0]["id"], "title": existing[0]["title"],
                    "chunks": 0, "reused": True,
                }, ensure_ascii=False)
            raise RuntimeError("knowledge_document_with_same_content_is_not_ready")
        vectors: list[list[float]] = []
        for offset in range(0, len(chunks), 64):
            vectors.extend(await self._embed(chunks[offset:offset + 64]))
        document = await self.client.insert("knowledge_documents", {
            "owner_user_id": user_id,
            "workspace_id": workspace_id,
            "title": title.strip(),
            "source_type": "text",
            "content_sha256": digest,
            "status": "processing",
            "metadata": {"ingested_by_run": run_id, "chunk_count": len(chunks)},
        })
        try:
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True)):
                await self.client.insert("knowledge_chunks", {
                    "document_id": document["id"],
                    "owner_user_id": user_id,
                    "workspace_id": workspace_id,
                    "chunk_index": index,
                    "content": chunk,
                    "embedding": "[" + ",".join(format(value, ".9g") for value in vector) + "]",
                    "token_count": None,
                    "metadata": {"source": "agent_ingest"},
                })
            await self.client.update(
                "knowledge_documents",
                {"id": f"eq.{document['id']}", "owner_user_id": f"eq.{user_id}", "status": "eq.processing"},
                {"status": "ready"},
            )
        except Exception:
            await self.client.update(
                "knowledge_documents",
                {"id": f"eq.{document['id']}", "owner_user_id": f"eq.{user_id}"},
                {"status": "failed"},
            )
            raise
        return json.dumps({
            "document_id": document["id"], "title": title.strip(),
            "chunks": len(chunks), "reused": False,
        }, ensure_ascii=False)


    async def process_uploaded_document(self, document: dict[str, Any]) -> int:
        """Lease-backed PDF/image extraction, OCR, page-aware chunking and vector persistence."""
        from io import BytesIO
        from PIL import Image
        import pytesseract
        from pypdf import PdfReader
        import pypdfium2 as pdfium

        document_id = str(document.get("id") or "")
        owner_id = str(document.get("owner_user_id") or "")
        metadata = document.get("metadata") if isinstance(document.get("metadata"), dict) else {}
        bucket = metadata.get("storage_bucket")
        storage_path = metadata.get("storage_path")
        mime = metadata.get("mime_type")
        if not document_id or not owner_id or not isinstance(storage_path, str):
            raise ValueError("knowledge_ingestion_metadata_invalid")
        raw = await self.client.download_storage_object(str(bucket), storage_path)
        pages: list[tuple[int, str]] = []
        page_count = 0
        ocr_status = "not_applicable"
        ocr_pages: list[int] = []
        if mime == "application/pdf":
            reader = PdfReader(BytesIO(raw), strict=True)
            if getattr(reader, "is_encrypted", False):
                raise ValueError("knowledge_pdf_encrypted")
            if len(reader.pages) > 500:
                raise ValueError("knowledge_pdf_page_limit_exceeded")
            page_count = len(reader.pages)
            # pypdf extracts embedded text; PDFium renders only pages without useful
            # text so scanned PDFs are OCRed without rasterizing every page.
            pdf_document = pdfium.PdfDocument(raw)
            try:
                for index, page in enumerate(reader.pages, start=1):
                    text = page.extract_text() or ""
                    if len(text.strip()) >= 30:
                        pages.append((index, text))
                        continue
                    pdf_page = pdf_document[index - 1]
                    try:
                        width_pt, height_pt = pdf_page.get_size()
                        scale = min(1.5, (40_000_000 / max(1.0, width_pt * height_pt)) ** 0.5)
                        if width_pt * height_pt * scale * scale > 40_000_000:
                            raise ValueError("knowledge_pdf_page_pixel_limit_exceeded")
                        bitmap = pdf_page.render(scale=max(0.5, scale))
                        image = bitmap.to_pil().convert("RGB")
                        try:
                            ocr_text = await asyncio.to_thread(
                                pytesseract.image_to_string, image, lang="eng+ind",
                            )
                        finally:
                            image.close()
                            bitmap.close()
                        if ocr_text.strip():
                            pages.append((index, ocr_text))
                            ocr_pages.append(index)
                    finally:
                        pdf_page.close()
            finally:
                pdf_document.close()
        elif mime in {"image/jpeg", "image/png", "image/webp"}:
            probe = Image.open(BytesIO(raw))
            probe.verify()
            with Image.open(BytesIO(raw)) as source_image:
                if source_image.width < 1 or source_image.height < 1 or source_image.width * source_image.height > 40_000_000:
                    raise ValueError("knowledge_image_pixel_limit_exceeded")
                image = source_image.convert("RGB")
            try:
                text = await asyncio.to_thread(pytesseract.image_to_string, image, lang="eng+ind")
            finally:
                image.close()
            ocr_status = "completed" if text.strip() else "no_text_detected"
            if text.strip():
                ocr_pages.append(1)
                pages.append((1, text))
            page_count = 1
        else:
            raise ValueError("knowledge_file_type_unsupported")

        if mime == "application/pdf":
            ocr_status = "completed" if ocr_pages else "not_required"
        if not pages:
            raise ValueError("knowledge_extraction_empty_or_ocr_unavailable")

        indexed_chunks: list[tuple[str, dict[str, Any]]] = []
        for page_number, page_text in pages:
            normalized = re.sub(r"\s+", " ", page_text).strip()
            start = 0
            while start < len(normalized):
                end = min(len(normalized), start + 2400)
                if end < len(normalized):
                    boundary = normalized.rfind(" ", start + 1200, end)
                    if boundary > start:
                        end = boundary
                chunk = normalized[start:end].strip()
                if chunk:
                    indexed_chunks.append((chunk, {
                        "source": "file_ingestion",
                        "source_page": page_number,
                        "char_start": start,
                        "char_end": end,
                        "ocr": page_number in ocr_pages,
                    }))
                if end >= len(normalized):
                    break
                start = max(start + 1, end - 250)
        if not indexed_chunks or len(indexed_chunks) > 500:
            raise ValueError("knowledge_document_chunk_limit_exceeded")

        vectors: list[list[float]] = []
        chunks = [item[0] for item in indexed_chunks]
        for offset in range(0, len(chunks), 64):
            vectors.extend(await self._embed(chunks[offset:offset + 64]))

        # Idempotent recovery: a reclaimed job rebuilds the chunk set from source bytes.
        await self.client.delete_knowledge_chunks(document_id, owner_id)
        for index, ((chunk, source_metadata), vector) in enumerate(zip(indexed_chunks, vectors, strict=True)):
            await self.client.insert("knowledge_chunks", {
                "document_id": document_id,
                "owner_user_id": owner_id,
                "workspace_id": document.get("workspace_id"),
                "chunk_index": index,
                "content": chunk,
                "embedding": "[" + ",".join(format(value, ".9g") for value in vector) + "]",
                "token_count": None,
                "metadata": source_metadata,
            })
        await self.client.update(
            "knowledge_documents",
            {"id": f"eq.{document_id}", "owner_user_id": f"eq.{owner_id}", "status": "eq.processing"},
            {"metadata": {
                **metadata, "ingestion_state": "indexed",
                "chunk_count": len(indexed_chunks), "page_count": page_count,
                "ocr_status": ocr_status,
            }, "page_count": page_count},
        )
        return page_count

    async def knowledge_search(
        self, arguments: dict[str, Any], *, run_id: str, user_id: str,
        workspace_id: str | None = None,
    ) -> str:
        query = arguments.get("query")
        limit = arguments.get("limit", 8)
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 2000:
            raise ValueError("knowledge_query_invalid")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
            raise ValueError("knowledge_match_limit_out_of_range")
        [vector] = await self._embed([query.strip()])
        rows = await self.client.rpc("moreai_match_knowledge_chunks", {
            "p_user_id": user_id,
            "p_workspace_id": workspace_id,
            "p_query_embedding": "[" + ",".join(format(value, ".9g") for value in vector) + "]",
            "p_match_count": limit,
            "p_document_ids": None,
        })
        if not isinstance(rows, list):
            raise RuntimeError("knowledge_search_response_invalid")
        safe_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            safe_rows.append({
                "chunk_id": row.get("chunk_id"),
                "document_id": row.get("document_id"),
                "title": row.get("title"),
                "content": row.get("content"),
                "similarity": row.get("similarity"),
                "metadata": row.get("metadata") if isinstance(row.get("metadata"), dict) else {},
            })
        return json.dumps({"results": safe_rows, "count": len(safe_rows)}, ensure_ascii=False)
