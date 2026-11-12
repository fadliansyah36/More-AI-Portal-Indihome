# Phase 08 — Durable Knowledge File Ingestion (2026-11-12)

## Scope implemented on main
This increment adds native multipart uploads from the existing Customer Knowledge Library, private Supabase Storage, durable worker ingestion, PDF extraction, image OCR, page-aware chunk metadata and RAG citation propagation.

## Data flow
1. Customer selects a local PDF/JPEG/PNG/WEBP using the browser's native file picker.
2. The existing authenticated FastAPI client sends `multipart/form-data` to `POST /api/v1/customer/knowledge/documents/upload`. No URL is accepted.
3. FastAPI validates principal (Customer), workspace membership, MIME allowlist, file signature, filename, empty file and 25 MiB cap. It computes SHA-256 and stores owner-scoped metadata.
4. FastAPI uploads raw bytes to private bucket `moreai-knowledge-private` using server-only Storage credentials. Browser receives neither Storage URL nor service-role key.
5. A worker claims a processing document through `moreai_worker_claim_knowledge_ingestion` using `FOR UPDATE SKIP LOCKED` and a bounded lease.
6. Worker downloads the private object, extracts each PDF page with pypdf or OCRs raster images with Tesseract, chunks content with page/character offsets, embeds chunks, and persists vectors and source metadata.
7. Worker marks the document ready or retries with bounded exponential delay, up to three attempts. Expired leases are reclaimable after process interruption.
8. RAG retrieval carries chunk metadata through durable checkpoints; final citations include chunk marker, document title, source page and character offsets.

## Files changed
- `apps/api/app/routers/knowledge.py`: multipart endpoint, workspace membership validation, file size/type/signature validation, server-side Storage upload.
- `apps/api/pyproject.toml`: pinned `python-multipart==0.0.20`.
- `lib/api/client.ts`: preserves browser multipart boundary; does not force JSON content type for FormData.
- `lib/api/knowledge.ts`: typed multipart upload method.
- `components/views/knowledge-library-view.tsx`: native device file picker, upload progress/error handling; existing layout preserved.
- `supabase/migrations/20261112170000_moreai_durable_knowledge_file_ingestion.sql`: private Storage bucket, server-only Storage policy, ingestion lease/attempt/page columns and claim/finish RPCs.
- `apps/worker/requirements.txt`: pinned pypdf, Pillow and pytesseract dependencies.
- `apps/worker/Dockerfile`: installs Tesseract OCR runtime.
- `apps/worker/app/client.py`: lease claim/finish, private Storage download and chunk cleanup.
- `apps/worker/app/knowledge_tools.py`: PDF extraction, OCR, page-aware chunking, embedding and idempotent chunk rebuild.
- `apps/worker/app/main.py`: background ingestion dispatch in the existing worker loop.
- `engine/agents/durable_tool_runtime.py`: page and character offsets retained in RAG citation records.
- `components/views/chat-view.tsx`: displays page number alongside source citation.

## Security and recovery notes
- The API accepts bytes only; no URL fetch or arbitrary Storage path input is accepted.
- The Storage bucket is private and denies direct anon/authenticated object access. Service-role access remains server-only.
- Document records and chunks are always owner-scoped. Workspace uploads require owner or active workspace membership.
- Supported types: PDF, JPEG, PNG and WEBP. Max upload size 25 MiB; PDF page limit 500; image pixel limit 40 million; chunk limit 500.
- OCR uses Tesseract in the worker container. Images with no detectable text fail explicitly; the original file remains stored privately for future reprocessing.
- Worker claims are leased and use SKIP LOCKED. Worker interruption leaves a reclaimable processing record. Provider/storage/extraction failures retry with exponential delay and stop after three attempts.
- Chunk rebuilding deletes only existing chunks for the same document and owner, then recreates deterministic chunk indexes and source metadata.

## Migration / runtime state
- Migration is committed but **not applied** to Supabase in this increment.
- Worker dependency/image changes are committed but **not built or deployed**.
- No tests, lint, typecheck, build, API calls, upload, Storage request, OCR execution, DB mutation, staging, or deployment were run, per the current instruction to defer real verification/release.
- Therefore upload/ingestion is source-implemented but not yet runtime accepted. It will not work in production until the migration is reviewed/applied and the updated API/worker are deployed with embedding configuration.

## Known follow-up risks / blockers
- Worker lease heartbeat is not yet renewed during unusually long extraction/embedding operations; lease is 900 seconds and file/chunk caps bound expected work, but a long provider outage can exceed the lease.
- Current RAG chunk citations are page-aware, but PDF character offsets are page-local offsets in normalized extracted text, not exact PDF glyph coordinates.
- Tesseract OCR is available for raster image uploads; scanned-image-only PDF pages are not OCRed yet. A PDF with no embedded text currently fails with `knowledge_extraction_empty_or_ocr_unavailable`.
- Storage cleanup for abandoned upload rows/objects is not yet automated.
- Idempotent client upload keys and resumable/chunked large-file uploads are not implemented; upload is bounded at 25 MiB.
- API endpoint returns a processing document immediately; Customer list refresh can show status. Dedicated polling/Realtime progress UX remains follow-up.

## Next work
1. Add OCR fallback for image-only PDF pages, plus lease heartbeat while processing.
2. Add secure storage object cleanup and explicit reprocess endpoint for failed ingestion.
3. Complete Phase 08 provider capability matrix and upstream agent/Flow/tool parity.
4. Complete Phase 06 route-wide auth/tenant/OpenAPI contract audit.
5. Complete Phase 09 all Customer screens/actions and remove remaining demo data.
6. Phase 10/11 remain blocked pending explicit verification/release permission.
