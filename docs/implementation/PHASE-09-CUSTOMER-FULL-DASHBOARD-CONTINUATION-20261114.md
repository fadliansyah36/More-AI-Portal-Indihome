# Phase 09 — Customer Dashboard Integration Continuation

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Source-only continuation commit: `75848ffb91de0f5264c30a1f6b81a66a5ecfdbe4`

## Objective

Continue reconciling the existing Customer Dashboard with FastAPI, the OpenManus-backed runtime/worker, and canonical Supabase while preserving the protected UI.

## Repository and architecture revalidated

- Main repository default branch is `main`.
- `AGENTS.md` requires OpenManusWeb to remain the authoritative backend source, FastAPI to remain the trusted business API, Supabase PostgreSQL to remain canonical persistence, and the existing Next.js Customer UI to remain the product frontend.
- Browser-side Supabase use is restricted to Auth. Business data, Storage, RPC, Realtime and provider operations must remain server-side behind FastAPI.
- Current acceptance matrix classifies Customer UI integrations as source-connected, partial/gated, or unavailable/fail-closed. Runtime acceptance remains NOT VERIFIED.

## Source correction implemented

File: `components/views/agent-studio-view.tsx`

The selected Agent detail previously rendered a static green `Enabled` badge even if the live worker capability snapshot showed that the runtime was offline. The badge now reflects `runtimeAvailable`:

- `Runtime aktif` when the backend reports an available runtime.
- `Worker offline` when no healthy worker is advertising that runtime.

The existing launch button remains disabled when the runtime is unavailable. No visual redesign, layout/navigation change, global token change, or new frontend shell was introduced.

## Broader Customer Dashboard reconciliation status

The current repository acceptance matrix and action inventory continue to identify these source-level areas:

- Chat: conversation restore, enqueue, attachments, authenticated SSE/replay, cancel, safe retry, citations.
- Agent Studio: runtime catalog, saved Agent configuration, worker capability snapshots and tool allowlists.
- Workflow/Tasks: durable run history, progress, dependency projection, approval decisions, cancellation, retry semantics, events and artifacts.
- Files/Artifacts: owner-scoped workspace/file lifecycle, immutable versions, private artifacts and signed downloads.
- Analyse/Knowledge/RAG: document ingestion, chunk pagination, selected-document retrieval and provenance.
- Personal Memory: consent, owner-scoped CRUD, worker consent filtering and retention purge implementation.
- Create Studio: Chat handoff and file artifact path; image/video generation remain gated on real provider credentials, price/metering, entitlement/quota and artifact configuration.
- Wallet/usage: read-only balance, entitlement, ledger and usage views; checkout/top-up settlement is unavailable without payment provider contracts.
- Partner Wi-Fi/OTP/gateway, OAuth connectors, full device-session revocation and support-ticket provider flows remain partial or unavailable until their real external contracts and credentials exist.

## Known integration boundaries and gaps

1. Model/provider routing is server-side and remains PARTIAL/GATED; the browser must not call provider APIs or expose secrets.
2. Tool catalog visibility is not proof of executable capability. Worker heartbeat, adapter registration, policy, isolation and approval remain authoritative.
3. Manual retry creates a new Agent Run only for safe replayable failed runs. Automatic retry and approval continuation recover the existing durable run/checkpoints. No manual in-place checkpoint rewind is exposed.
4. External payment, OTP/gateway, connector OAuth and support provider flows must fail closed until provider contracts/credentials and security requirements are satisfied.
5. Classroom/teacher governance and some institutional EduTech features remain outside the completed learner curriculum core.
6. A static source audit cannot prove production worker health, LLM credentials, provider billing, RLS denial paths, event replay correctness or end-to-end persistence.

## Verification boundary

Per product-owner instruction, no tests, lint, typecheck, build, browser screenshots, API probes, worker execution, provider calls, staging or deployment were performed. This report records source inspection and a targeted source correction only. It does not claim runtime acceptance or Phase 09 completion.

## Phase status and dependency

Phase 09 remains **IN PROGRESS**. The Customer Dashboard integration must not be marked complete while source-level action/contract gaps and provider-dependent gates remain unresolved. Phase 10 E2E verification and Phase 11 release gate remain dependency-next and are intentionally not executed under the current instruction.

## Tasks lifecycle UI correction — 2026-11-14

- Fixed the Tasks view's projection of terminal Agent Run states. Only `succeeded` is presented as successful completion; failed, cancelled, timed-out and expired runs remain terminal but are not shown with success styling.
- The Active filter now excludes all terminal states; the Selesai filter shows terminal outcomes while preserving their actual status labels.
- Removed nested button markup in the task card so the card itself remains the single interactive detail target.
- Added optional canonical `status` to the TaskItem presentation type.
- Commits: `41d394731bbcc512ca35ebb2cd2c63f64f9740f8`, `e2cff38d614f87dcda1013f777849af8a358717b`.
- Not browser-verified; all runtime acceptance remains NOT VERIFIED.

## Chat model-routing transparency — 2026-11-14

- The FastAPI `/api/v1/models/capabilities` endpoint and typed client were present but the Customer Chat composer did not expose the enabled model registry.
- Added a compact, collapsible **Model & capability tersedia** section to Chat. It reads enabled provider/model names and normalized capability tags from the authenticated catalog endpoint.
- The UI explicitly communicates that actual model selection remains automatic in the backend Model Router, based on task/capability/policy. It does not let a customer bypass provider routing, entitlements or quotas.
- Registry failures are displayed as a non-blocking warning and do not fabricate available models or imply that generation is possible.
- Source commit: `33ea20b19a7bbe4d064ace8da8f9c83c336c9b09`.
- Source-only change; no browser verification, API probe, tests, lint, typecheck or build was performed.

- Follow-up copy correction commit: `83b694b410606d4e9c86d87654c430a87ea8cfc0`. The model registry panel distinguishes enabled provider/model registry entries from per-customer entitlement; actual execution remains subject to entitlement, quota, router and worker policy.
