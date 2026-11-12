# Phase 08 — Tenant-Scoped Knowledge RAG Foundation
Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Implementation delivered
1. Added additive Supabase migration `20261112150000_moreai_knowledge_rag_vector.sql`:
   - `knowledge_documents` and `knowledge_chunks` with owner/workspace scope.
   - pgvector 1536-dimensional embeddings and cosine IVFFlat index.
   - server-only RLS policies and service-role grants.
   - `moreai_match_knowledge_chunks` RPC filters by owner and exact workspace scope before ranking.
2. Added `apps/worker/app/knowledge_tools.py`:
   - OpenAI-compatible embeddings HTTP adapter with HTTPS-only base URL and secret-env indirection.
   - bounded text chunking (2,400 chars with 250-char overlap; max 500 chunks).
   - tenant-scoped text ingestion, SHA-256 content identity, durable chunk writes, ready/failed document state.
   - semantic retrieval through the scoped database RPC; result count capped at 20.
3. Added `knowledge_ingest` and `knowledge_search` to the canonical tool catalog.
4. Wired both tools into `DurableOpenManusRuntime` and the worker registry factory. They are enabled only when embedding base URL and model are configured.
5. Added system guidance to retrieve indexed knowledge when relevant and only ingest when the user explicitly asks.

## Source commits
- Migration: `6e41811204bfb36f6ff1ac095346ca1c46790b4f`
- RAG adapter: `2d08de802a8fcab4b20eab8a28abcb39345f437a`
- Tool catalog: `31449379a67a236336a11a1d1fecf418103a06c3`
- Durable runtime wiring: `0ed2225efe0c8937418008e269815056e5818dac`
- Workspace scope forwarding: `3730f40f51ba1b07c3fe9800ac485fc93a08fcc3`
- Worker registry wiring: `27e8d6cc360f4fd37a53bf3f0745a8612d3fd1e6`
- Runtime retrieval guidance: `e625087f9a7a409dd8e25c41b997f6739f6c450b`

## Runtime configuration contract
Set these worker environment variables to activate semantic knowledge tools:
- `MOREAI_EMBEDDING_BASE_URL`: HTTPS OpenAI-compatible embeddings endpoint base URL (without `/embeddings`).
- `MOREAI_EMBEDDING_MODEL`: provider model key.
- `MOREAI_EMBEDDING_SECRET_ENV`: optional env var name for the secret; defaults to `MOREAI_EMBEDDING_API_KEY`.
- The embedding model must return exactly 1536 finite numeric dimensions per input.

No embedding provider is hardcoded. If configuration is absent, knowledge tools remain unregistered and the rest of the agent runtime continues without falsely advertising them.

## Important limits / next implementation
- This increment indexes explicitly supplied text. Private file/PDF/URL extraction and asynchronous ingestion jobs are still to be connected.
- A deployment must apply the migration and configure the embedding provider before RAG becomes available. No schema migration was executed here.
- Customer-facing knowledge library APIs/UI and permission controls for document management remain Phase 06/09 work.
- Existing conversation memory remains separate from semantic RAG; this work does not replace or corrupt conversation history.

## Verification boundary
No tests, lint, typecheck, build, provider calls, database migration, worker startup, staging or deployment were run. This is committed source implementation, not runtime acceptance.

## Remaining Phase 08
- Complete provider capability routing and provider fallback for embeddings.
- Reconcile all upstream agent definitions and tool adapters against the registry.
- Add durable ingestion jobs for file artifacts and document extraction.
- Connect retrieval context to planning and specialized agents with citations and source attribution.
- Verify all provider/tool/agent workflows after explicit authorization to run verification.
