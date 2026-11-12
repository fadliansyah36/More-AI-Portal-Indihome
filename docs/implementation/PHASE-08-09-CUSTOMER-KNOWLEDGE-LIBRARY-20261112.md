# Phase 08/09 — Customer Knowledge Library API & UI Integration

Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Scope

Connect the existing tenant-scoped Phase 08 RAG document model to authenticated Customer-facing APIs and a usable Knowledge Library screen. This increment does not replace the existing Customer UI or introduce a second application. Network gateway/Wi-Fi work remains out of scope.

## Implemented source

1. Added `apps/api/app/routers/knowledge.py` and mounted it in FastAPI:
   - `GET /api/v1/customer/knowledge/documents` lists only the authenticated owner's documents, with optional workspace/status filters and bounded pagination.
   - `GET /api/v1/customer/knowledge/documents/{document_id}` returns owner-scoped document metadata and chunk metadata; vector values and chunk text are never exposed.
   - `POST /api/v1/customer/knowledge/documents/{document_id}/archive` performs a soft archive for ready/failed owned documents. It preserves source/chunk history and is idempotent for already archived documents.
   - All endpoints use the Customer principal and server-side Supabase repository; the browser never receives service-role credentials.

2. Added `lib/api/knowledge.ts`:
   - Typed Customer knowledge document and chunk metadata.
   - Authenticated list/get/archive methods through the shared FastAPI API client.
   - URL query encoding and bounded limit handling.

3. Added `components/views/knowledge-library-view.tsx`:
   - Real API-backed document listing, status filters, title search, refresh, and soft archive.
   - Empty state explicitly explains that documents appear after the Agent Runtime's `knowledge_ingest` tool succeeds.
   - No fabricated records or fake ingestion completion.

4. Added authenticated route `/customer/knowledge`:
   - Checks the Supabase Auth session and redirects unauthenticated users to the existing Customer login route.
   - Uses the existing Customer design language and returns to the existing Customer app.
   - The existing Files view now links to Knowledge Library; no global redesign was performed.

## Source commits

- API router: `2f3e1cf61d60a3cff736ad2c32ca030b1616ff3d`
- FastAPI router mount: `135ceae49f80406f9fae65f060a8b8eba85fadbe`
- Typed API client: `5a10013d08484875317ee54c0aba6659841348c2`
- Knowledge Library view: `7f4a54cd60ddcd6aeac4b7be792fd49e9ded7351`
- Authenticated Customer route: `5939b92d360461acc916160ccd2791c833c66b06`
- Files screen navigation link: `8034aea4fa64ddcce623cbf4d4306ad3676899bb`

## Database and runtime prerequisites

- The existing additive RAG migration is `supabase/migrations/20261112150000_moreai_knowledge_rag_vector.sql`.
- This source increment did not apply the migration to the connected production Supabase database.
- Worker embedding configuration remains required: `MOREAI_EMBEDDING_BASE_URL`, `MOREAI_EMBEDDING_MODEL`, and a server-only API key resolved by `MOREAI_EMBEDDING_SECRET_ENV`.
- The existing Agent Runtime remains the only ingestion/retrieval execution authority. This UI lists and archives documents; it does not bypass the worker to create embeddings.

## Verification boundary

Per product-owner instruction, no tests, lint, typecheck, build, browser session, real API request, database migration, provider request, staging or deployment was run. Commits confirm source writes only. Runtime behavior, migration availability and provider readiness are unverified. This is an implementation increment, not Phase 08/09 acceptance.

## Remaining work

- Apply the RAG migration only when the owner authorizes the production schema change; confirm extension/schema availability and migration history first.
- Connect document/file extraction and durable ingestion jobs to private workspace artifacts.
- Add document-level workspace membership sharing controls only after the exact access model is reconciled with workspace membership and owner scope.
- Connect retrieval citations/source attribution to Customer Chat and planning output.
- Complete the remaining Phase 04 upstream server/session/Flow/SWE workspace parity, Phase 07 recovery lifecycle, Phase 08 provider/agent/tool parity, Phase 06 API contract coverage, and Phase 09 screen-to-endpoint mapping.
- Phase 10/11 remain blocked/not started because real verification and release acceptance were explicitly excluded.

## Next phase recommendation

Continue Phase 04 backend integration and security hardening as the dependency gate, then Phase 07 durable worker lifecycle, Phase 08 provider/tool/agent completion, Phase 06 contract reconciliation, and Phase 09 remaining Customer screen bindings. Do not mark any phase complete based on this source-only increment.
