# Phase 09 — Knowledge Library Re-index Lifecycle

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Baseline: `e85a1e3b487660dee7acfa640103f86d396b6764`

## Implemented

- Added owner-scoped `POST /api/v1/customer/knowledge/documents/{id}/reindex`, retaining the existing retry route for compatibility.
- Re-index accepts only the authenticated owner's file-backed documents in `ready` or `failed` state and verifies the private Storage bucket/path plus workspace access.
- State transition uses compare-and-set filters, resets the ingestion attempt and lease, and records the re-index request in metadata.
- Knowledge Library now exposes re-index for ready files and retry for failed files, using existing MoreAI styles.
- Reuses the existing worker lease/heartbeat ingestion path: private Storage download, extraction/OCR, embedding and chunk replacement. No duplicate runtime or ingestion queue was introduced.

## Files
- `apps/api/app/routers/knowledge.py`
- `lib/api/knowledge.ts`
- `components/views/knowledge-library-view.tsx`

## Remaining gaps
- Permanent document deletion and retryable orphan Storage cleanup are not included.
- Citation provenance still needs end-to-end linkage from retrieved chunk through Agent Run output and persisted conversation response.
- URL/text document re-index is not introduced; this action is file-source based.
- Worker/provider availability and vector persistence are not runtime-verified.

## Validation boundary
Source-only implementation. No tests, lint, typecheck, build, browser/API/worker probes, provider calls, Supabase mutation, staging or deployment were performed. No runtime acceptance is claimed.

## Next Phase 09 work
1. Distinct episodic, semantic and procedural runtime memory stores and retrieval/write policies, keeping consented Personal Memory separate from conversation history.
2. Knowledge deletion with transactional metadata/chunk cleanup and retryable private Storage cleanup; complete citation provenance.
3. Skill permission review/revocation and server-authoritative execution lifecycle in Agent Studio and Chat.
4. Agent Studio model routing and immutable Agent/skill/tool snapshots used by durable Agent Runs.
5. Reconcile Chat, Tasks, Workflow, Files and Agent Run against the same canonical lifecycle.
6. Update Master Context and acceptance matrix after source reconciliation.

Phase 09 remains IN PROGRESS.
