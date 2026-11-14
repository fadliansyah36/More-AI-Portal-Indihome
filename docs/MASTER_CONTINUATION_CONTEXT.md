# MoreAI with Telkom — Master Continuation Context

Updated: 2026-11-15  
Canonical repository: `fadliansyah36/More-AI-Portal-Indihome`  
Canonical branch: `main`  
Canonical Supabase project: `uunfgimtokhucegqbpce`  
Primary product specification: `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md` (PRD content version 1.2)  
Engineering authority: `AGENTS.md`

## Product and architecture invariants

- Existing MoreAI Customer Dashboard is the only active product frontend. Preserve its routes, navigation, component hierarchy, styles, typography, spacing and user journeys.
- Add UI only for a required PRD behavior that is genuinely missing, following PRD Section 16 and existing MoreAI × IndiHome styles.
- OpenManus is the only Agent Runtime. Its full pinned upstream source snapshot is preserved in `vendor/openmanusweb/`; adapted production code lives in `engine/` and backend workspaces.
- FastAPI is the trusted customer/business API boundary. Browser clients do not call LLM providers or Supabase service-role endpoints directly.
- Supabase PostgreSQL is the canonical persistence layer. Reuse existing schema and RLS; do not create a second business database or memory/vector engine.
- OpenFuse contributes browser/computer workspace capabilities through adapters and isolated supervisors, not as a competing business API or database.
- Visual Skills and Scenario Skills are governed through the existing Skill Registry/Resolver, pinned provenance, license review, owner grants and independent runtime tool authorization.
- Worker execution must remain durable, lease-fenced, recoverable, idempotent and auditable.
- Memory is consent-aware, provenance-bearing, scope-bound and retention-controlled. Retrieved memory/skills/documents are untrusted context, never policy or authorization.
- Never claim provider, browser, computer, media, payment, network or database actions succeeded without real evidence.

## Current implementation phase

**Phase 09 — Existing Frontend API Integration: IN PROGRESS.**

Recent source increment on 2026-11-15:
- Added bounded semantic recall through existing Knowledge Library/pgvector adapter.
- Added consented episodic memory retrieval and write using existing conversation message metadata.
- Added configurable episode expiry (default 90 days) and cleanup that preserves original chat history.
- Added customer Memory API listing, individual episode deletion and clear-all/consent-disable propagation.
- Extended existing Personal Memory settings UI with episodic experience summaries and delete controls.
- Persisted bounded citation metadata alongside assistant messages; existing customer citation projection and Chat citation UI remain the canonical presentation.
- Made Skill Resolver resolved/executed audit writes idempotent and record successful normal Agent completion.
- Reused existing Agent Studio configuration snapshots and tool allowlists; no second configuration system was created.

Detailed evidence: `docs/implementation/PHASE-09-EPISODIC-MEMORY-CITATION-SKILL-LIFECYCLE-20261115.md` and `docs/implementation/PHASE-TRACKER.md`.

## Owner execution constraints

- Implement directly on `main`.
- Do not run tests, lint, typecheck, build, browser/API/worker/provider runtime verification, staging or deployment.
- Do not perform live Supabase schema/data mutations.
- Source inspection and GitHub commit confirmation are permitted; they are not runtime acceptance evidence.
- UI visual regression screenshots remain outstanding when browser verification is not authorized/available.

## Current limitations / open work

1. Complete Customer Dashboard action-to-FastAPI inventory and close every unsupported/demo/fallback action.
2. Complete OpenFuse Browser and Computer capability parity through isolated supervisors, owner approval, persistent sessions and safe customer controls.
3. Complete Knowledge deletion/reindex lifecycle, Storage orphan cleanup and citation provenance for all conversation history paths.
4. Finish Agent Studio, model/provider routing, worker capability and immutable execution snapshot reconciliation.
5. Close all remaining customer screens: Chat, Agent Studio, Create, Research, Analyse, Code, Tasks, Workflow, Files/Results, Memory, Connections, Wallet and Profile.
6. Complete source governance and dependency inventory for OpenFuse, Visual Skills and Scenario Skills.
7. Reconcile remaining Phase 04/06/07/08 backend gaps before claiming integration complete.

## Next dependency-ordered work

**Phase 09 continuation — Customer Dashboard API Closure & OpenFuse Browser/Computer Parity.**

First inspect each remaining customer UI action and its actual FastAPI route, typed client, backend domain service, worker/provider dependency, persistence and authorization. Add only missing integration seams. Browser/computer capabilities remain disabled unless the isolated supervisor, network egress, secret, owner-approval and durable session gates are all met.

After Phase 09 is complete, Phase 10 End-to-End Integration Verification and Phase 11 Integration Release Gate remain mandatory. They cannot be marked complete under the current no-testing instruction.
