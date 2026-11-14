# 2026-11-14 — Full Customer AI Integration Continuation

Branch: `main`
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Canonical Supabase project: `uunfgimtokhucegqbpce`

## Owner execution constraints
- Implement directly on `main`.
- Do not use staging.
- Do not run tests, lint, typecheck, build, browser/API probes, worker execution, provider calls, or deployment.
- Preserve the existing Customer UI and design tokens; add only missing controls for approved contracts.
- Keep FastAPI as the trusted business API, OpenManus as the sole Agent Runtime, worker as durable execution coordinator, and Supabase as canonical persistence.

## Current source baseline inspected
- `AGENTS.md` remains controlling.
- Master PRD: `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`; sections 35–37 inspected at the six-type memory, OpenFuse capability, source governance, and package sequencing passages.
- Phase 09 acceptance matrix and full-dashboard continuation reviewed.
- Existing Personal Memory panel/API/client/worker adapter inspected.
- Existing OpenManus durable runtime and worker registry factory inspected.
- Existing Customer Chat, Agent Studio, Workflow/Tasks, Knowledge, Files, Create, Wallet and profile integration surfaces are already present in source and have multiple source-only continuations.
- Existing browser/computer adapters are fail-closed behind isolated supervisor, egress enforcement, owner approval and independent release gates. Do not activate by configuration alone.

## Live schema reconciliation (read-only metadata)
- Supabase verbose public schema inventory confirms `moreai_customer_memories` and `moreai_customer_memory_preferences` exist with RLS enabled.
- `moreai_customer_memories` currently constrains `source_type='user_created'` and `scope='personal'`; it has no typed six-memory discriminator, source provenance, confidence, sensitivity, version or review/deletion metadata.
- The inspected schema inventory did not contain `memory_items`, `memory_embeddings`, `memory_sources`, or `memory_consent_events`.
- Existing canonical source domains include conversations/messages, Agent Runs/events/checkpoints, Knowledge documents/chunks, saved Agent configurations and workflow definitions.
- No DDL, SQL mutation, migration apply, data mutation or provider operation was performed.

## Six-type memory contract from PRD
1. Working Memory — existing run-scoped state/checkpoints with TTL; never a user profile.
2. Conversation Memory — existing owner-scoped conversation/messages and derived summaries.
3. Long-term Memory — existing explicitly consented Personal Memory, with user review/correction/retention/deletion.
4. Episodic Memory — derived events/outcomes linked to source Agent Runs/projects/artifacts; requires dedupe, redaction and provenance.
5. Semantic Memory — authorized Knowledge/RAG documents, structured facts and embeddings; source authorization must precede retrieval.
6. Procedural Memory — approved versioned procedures, skill references and workflow templates; cannot grant tool permissions.

### Important implementation consequence
The current Personal Memory table is not a six-type Memory store. Do not simply widen its existing `source_type` or `scope` constraints to simulate six memory types. Do not inject raw Agent Run events or Knowledge chunks as generic memories. A Memory Coordinator must query each canonical source through owner/tenant/workspace authorization, preserve source identity/provenance/confidence/freshness/sensitivity/consent/expiry/version, budget context, and propagate correction/deletion to derived summaries/embeddings. Episodic and procedural source-of-truth gaps must be proven before adding dedicated persistence.

## OpenFuse integration boundary
- Reuse MoreAI's durable Agent Run/Step/Event/Checkpoint/Approval/Artifact lifecycle.
- Browser profiles, browser sessions and computer workspaces require isolated service contracts, owner/tenant binding, SSRF/egress/download controls, lease and quota, action receipts, durable event/checkpoint mapping, same-session human takeover and approval.
- Do not import OpenFuse's Hono API, PGlite persistence, shared access-key identity, or task engine as competing MoreAI authorities.
- Current browser and sandbox tools remain disabled unless independent supervisor and release gates are satisfied.

## External Skills integration boundary
- Visual Skills and Scenario Skills remain subject to P1 content-level license/provenance/dependency/security review.
- Do not wholesale-copy, install, or execute unreviewed skills/assets/scripts.
- Approved skills must become immutable, versioned Skill Registry entries with license/provenance, dependencies/assets, validation/review/publish lifecycle and deterministic resolution by tenant/Agent/tool/policy.
- Skill content is untrusted instruction context. A skill cannot grant tools, permissions, entitlements or approval.
- Scenario model discovery/schema validation/cost preview/job execution/artifact/credit settlement must map to existing MoreAI worker, provider router, Agent Run and accounting systems.

## Current mandatory phase status
- Phase 04 backend parity/security: IN PROGRESS.
- Phase 06 FastAPI/OpenAPI contracts: IN PROGRESS.
- Phase 07 durable worker: IN PROGRESS.
- Phase 08 LLM/tools/orchestration: IN PROGRESS.
- Phase 09 existing Customer Dashboard integration: IN PROGRESS.
- Phase 10 verification: NOT ACCEPTED and not run by owner instruction.
- Phase 11 release gate: BLOCKED.
- P1 external source governance: IN PROGRESS.

The PRD's P0 mandatory Phase 00–11 baseline is not closed. P1–P9 capability packages (including six-type Memory completion, Skill Registry, Visual Skills, Scenario MCP, OpenFuse Browser/Computer) are sequenced after the mandatory baseline. Customer-facing activation controls (P10) require the phase gate or a written product-owner exception with explicit risk/verification plan. The current no-test/no-staging instruction means Phase 10/11 cannot be claimed accepted.

## Next implementation sequence
1. Continue Phase 09 source integration against the Customer action-to-endpoint inventory; prioritize core Chat → durable Agent Run → worker/OpenManus → provider/tool → persisted events/artifacts/usage → UI projection.
2. Continue Phase 04/06/07/08 backend contract and lifecycle closure without activating unverified high-risk capabilities.
3. Close P1 source governance and P2 capability parity/ADRs.
4. Implement P3 six-type Memory Coordinator against existing canonical sources, after schema and authorization reconciliation.
5. Implement P4 Skill Registry/resolver; then P5 Visual Skills and P6 Scenario capability packs.
6. Implement P7 OpenFuse Browser and P8 Computer capability only with isolated supervisor/security controls.
7. Complete remaining P0 Customer integration and obtain owner authorization for Phase 10/11 evidence before claiming release acceptance.

## Verification boundary
No tests, lint, typecheck, build, browser/API/worker runtime checks, provider calls, staging, migration apply, SQL mutation, data mutation or deployment were performed. This is a source/schema metadata reconciliation record, not a completed implementation phase or runtime acceptance.
