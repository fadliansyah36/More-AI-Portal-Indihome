# Direct-main Integration Continuation — 2026-11-14

## Execution directive
- Target repository: `fadliansyah36/More-AI-Portal-Indihome`
- Target branch: `main`
- Canonical Supabase project: `uunfgimtokhucegqbpce`
- Scope: existing Customer Dashboard integration with OpenManus/OpenFuse capability patterns, six-type Memory, Visual Skills, Scenario Skills, FastAPI and Supabase.
- No staging environment.
- No real tests, build, lint, typecheck, browser, API, provider, worker, SQL execution, migration apply or deployment in this continuation, per owner instruction.

## Baseline reconciliation
- Actual `main` HEAD inspected at start: `3c44510e231d0c3007087bef677fdab0f6fa1529`.
- This differs from the HEAD cited by the 2026-11-12 Customer Workspace continuation (`e309fd093cde6e34b98a69d235098f6cebada833`). All implementation work must use the actual current `main` tree, not the older report baseline.
- `AGENTS.md` re-read before implementation.
- Master PRD file inspected: `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`, blob `b5b8d60c28a523fb0b22f6f44be07b9a1519fc1e`.
- Sections 35–37 are additive capability and source-reconciliation specifications; they do not declare implementation acceptance.

## Code surfaces inspected
- Existing frontend integration seam: `lib/api/client.ts`.
- Existing Customer Chat: `components/views/chat-view.tsx`.
- Existing Personal Memory UI: `components/views/personal-memory-settings.tsx`.
- Existing Knowledge API client: `lib/api/knowledge.ts`.
- FastAPI Customer domain: `apps/api/app/routers/customer.py`.
- FastAPI Knowledge domain: `apps/api/app/routers/knowledge.py`.
- Durable worker runtime and dispatch: `apps/worker/app/runtime.py`, `apps/worker/app/dispatcher.py`.
- OpenManus adapted execution: `engine/agents/durable_tool_runtime.py`.
- Existing memory adapters: `apps/worker/app/memory_store.py`.
- Existing agent/tool composition: `apps/worker/app/registry_factory.py`.

## Confirmed implementation baseline and gaps
1. Existing Customer Chat, typed API client, durable Agent Runs, SSE events, Tasks/Workflow, Files/Artifacts, Knowledge and Personal Memory integrations exist in source.
2. FastAPI remains the trusted business API; browser-side Supabase use must remain Auth-only.
3. Worker currently composes conversation history and consented user-authored Personal Memory. Knowledge/RAG is represented by existing Knowledge tools. This is not yet the complete six-type Memory Coordinator required by PRD 35.6.
4. OpenManus runtime remains the only Agent execution authority. Existing worker currently registers Manus, Planning and ToolCall; unsafe computer/browser execution remains fail-closed behind separate sandbox/browser controls.
5. OpenFuse adoption must map to existing Agent Run/Step/Event/Checkpoint/Approval/Artifact lifecycle. Browser sessions and persistent computer workspaces need explicit isolated service contracts; OpenFuse Hono/PGlite/identity/task persistence must not be imported as competing authorities.
6. Visual Skills and Scenario Skills are not yet approved for wholesale import. The recursive metadata manifest covers 2,393 pinned files, but content-level review, nested-license/attribution review, dependency SBOM and final file disposition remain open.
7. No claim is made that Customer screen coverage, upstream behavioral parity, provider routing, deployed worker health, memory lifecycle, skills or runtime execution is complete.

## Dependency-ordered implementation work
The following sequence preserves mandatory AGENTS.md gates and existing canonical ownership:

### A. P1 source governance closure
- Review source content and nested references by capability family.
- Review root/nested licenses, attribution, assets and transitive dependencies.
- Produce dependency/SBOM evidence without package installation.
- Map each eligible file/capability to existing MoreAI modules.
- Assign final per-file disposition: COPY, ADAPT, ARCHIVE-ONLY, EXCLUDE or DEFER.
- Do not import or execute unreviewed external source.

### B. Phase 04 — OpenManus backend parity and security
- Complete upstream server/session/Flow/log-monitor/API compatibility through FastAPI and durable services.
- Close the remaining tool/domain parity gaps in the capability map.
- Keep browser and computer execution isolated, approval-gated and fail-closed until their independent security boundary exists.

### C. Phase 07 — Durable worker lifecycle
- Close lease fencing, outbox recovery, retry, cancellation, timeout, approval resumption and event replay.
- Preserve idempotency and reconcile uncertain external side effects before retry.

### D. Phase 08 — LLM, tools, orchestration and Memory
- Complete provider/model routing and supported tool behavior without duplicating OpenManus runtime.
- Implement the six-type Memory Coordinator over canonical sources: Working, Conversation, Long-term, Episodic, Semantic and Procedural.
- Preserve consent, tenant/source authorization, provenance, confidence, expiry, correction and deletion propagation.
- Integrate reviewed skills as versioned instructions resolved by the existing runtime; skills never grant tool permission.

### E. Phase 06 — FastAPI contracts
- Complete versioned API contracts, schemas, auth/tenant checks, idempotency, error mapping and API/client alignment.

### F. Phase 09 — Customer Dashboard
- Complete screen-by-screen action/API coverage using the existing frontend client.
- Add only genuinely missing UI behavior, retaining existing visual hierarchy and design tokens.
- Map OpenFuse activity, browser/computer controls, approvals, action receipts, goals and notifications to existing Customer journeys.
- Add reviewed Visual Skills and Scenario Skills experiences within the existing Create/Agent/Workflow surfaces.

### G. Phase 10–11
- Remain blocked/not accepted until owner authorizes verification. No real test or deployment is claimed in this continuation.

## Supabase boundary
Live schema inventory previously identified existing conversations, agent runs/events/checkpoints, tools/approvals, artifacts, workspaces, knowledge, customer memory/preferences, learning, notifications and accounting tables. RLS is enabled on listed public tables, but policy correctness is not implied by that flag. Before any DDL, inspect exact columns, constraints, indexes, policies, triggers, functions, storage policies and migration history. No schema changes or data mutations were made in this continuation.

## UI preservation
No UI files were changed in this continuation. Any later UI change must identify the missing behavior and baseline route, be minimal, use existing components/tokens and preserve current navigation, layout, typography, color, spacing and responsive behavior.

## Verification and deployment
- Tests/build/lint/typecheck: NOT RUN by instruction.
- Real API/browser/provider/worker verification: NOT RUN by instruction.
- Staging: NOT USED.
- Supabase migration apply/data mutation: NOT PERFORMED.
- Deployment: NOT PERFORMED.
- Runtime acceptance: NOT CLAIMED.

## Current status
This continuation is a source and implementation-baseline reconciliation, not a completed implementation phase. P1 remains IN PROGRESS. Phases 04, 06, 07, 08 and 09 remain IN PROGRESS; Phase 10 is NOT ACCEPTED and Phase 11 is BLOCKED.

## Next phase
**P1 Continuation — Content-Level Audit & Final File Parity.** Close source content, licenses, dependency evidence and file-to-module disposition first. Then continue the mandatory Phase 04 → 07 → 08 → 06 → 09 dependency sequence. Report the next phase only when the preceding work has implementation evidence and its actual acceptance criteria are met.
