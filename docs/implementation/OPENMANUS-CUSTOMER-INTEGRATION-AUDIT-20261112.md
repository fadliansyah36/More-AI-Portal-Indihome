# OpenManus ↔ Customer Integration Audit — 2026-11-12

## Decision

The existing Customer frontend is connected to meaningful parts of the OpenManus-derived backend, but the integration is **not full and is not release-accepted**. Network gateway/Wi-Fi/Captive Portal integration is explicitly deferred.

## Architecture retained

One existing Next.js Customer application → FastAPI trusted API → durable OpenManus-derived Runtime/Worker → Supabase PostgreSQL/Storage. The upstream web frontend is not used as a second product UI.

## Confirmed source-level integration

- Pinned pristine upstream source exists at `vendor/openmanusweb`; manifest: `docs/implementation/openmanusweb-source-manifest.json`.
- Atomic chat enqueue creates user message and durable run.
- Worker dispatcher resolves registered Manus/Planning runtimes and restores run checkpoints.
- Durable tool-call loop, planning runtime, model router, OpenAI-compatible provider adapter, metered accounting, conversation history store, workspace/storage adapters, approval pause/resume, run events, SSE stream and outbox publisher exist.
- FastAPI Customer endpoints cover conversations, run listing/detail/steps/events/stream/cancel, workspace files/history/download, artifact, catalog, notifications and learning progress.
- Existing frontend typed API client and Customer views are retained.

## Critical gaps to close before declaring integration full

1. **Upstream server/session parity:** upstream `app/web` behavior is not yet mapped endpoint-by-endpoint to FastAPI. Existing run/SSE endpoints cover only part of job/session/log/thinking/file/websocket semantics.
2. **Workspace lifecycle:** create/list/rename and file listing/download/history/restore exist; archive/delete, membership lifecycle, file CRUD/rename/delete, conflict handling and recovery remain open.
3. **Tool capability parity:** the production registry conditionally registers a subset of upstream tools. Browser and sandbox are fail-closed behind external supervisor/release-gate configuration. Catalog presence does not mean executable integration.
4. **Flow/agent parity:** Manus and durable Planning are registered. All upstream agent types, Flow semantics, planner behavior, tool contracts, prompt/schema behavior and server workflow endpoints still require capability-by-capability reconciliation.
5. **RAG and memory:** conversation history persistence exists, but complete vector/RAG ingestion, retrieval, ranking, citation and tenant isolation have not been proven end-to-end.
6. **Model Router:** routing/fallback/provider and metering code exists, but actual enabled provider configuration, fallback on stream failures, interruption settlement, quota/entitlement and idempotency need runtime verification.
7. **Frontend parity:** existing screens are connected in part; some content catalogs remain local/static. No claim that every Customer screen is fully API-backed is made.

## Phase status

- Phase 04 — IN PROGRESS; server/session, Flow, workspace lifecycle, browser/sandbox security gates remain.
- Phase 07 — IN PROGRESS; durable lifecycle code exists, but retry/timeout/cancel/lease recovery/event replay/outbox acceptance remains.
- Phase 08 — IN PROGRESS; runtime/router/tools/memory adapters exist, but full parity and RAG/provider proof remain.
- Phase 06 — IN PROGRESS; FastAPI/API contracts and authorization coverage remain to be reconciled.
- Phase 09 — IN PROGRESS; all existing Customer views must be mapped and connected to real API behavior.

## Verification

Source inspection only. No test suite, lint, typecheck, frontend build, browser E2E, staging, provider execution or deployment was performed. No runtime acceptance is claimed.

## Next action

Continue Phase 04 only: build the upstream server/Flow/session capability matrix; implement missing durable FastAPI compatibility contracts; complete workspace lifecycle and browser/sandbox security. Only after Phase 04 acceptance proceed Phase 07 → Phase 08 → Phase 06 → Phase 09. Gateway network work remains out of scope until those phases pass.
