# MoreAI with Telkom — Master Continuation Context

Updated: 2026-11-15  
Canonical repository: `fadliansyah36/More-AI-Portal-Indihome`  
Canonical branch: `main`  
Canonical Supabase project: `uunfgimtokhucegqbpce`  
Engineering authority: `AGENTS.md`  
Master product specification: `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md` (content version 1.2)

## Product and architecture invariants

- Existing MoreAI Customer Dashboard remains the only active product frontend. Preserve its routes, navigation, component hierarchy, styles, typography, spacing and user journeys.
- Add UI only where a required PRD behavior is genuinely missing; follow PRD design tokens and adjacent MoreAI × IndiHome styles.
- OpenManus is the only Agent Runtime. Its pinned upstream snapshot is preserved in `vendor/openmanusweb/`; adapted production code lives in `engine/` and backend workspaces.
- FastAPI is the trusted customer/business API boundary. Browser clients do not call LLM providers or Supabase service-role endpoints directly.
- Supabase PostgreSQL is the canonical persistence layer. Reuse existing schema, RLS, Auth, Storage, Realtime and pgvector; do not create a second business database or memory/vector engine.
- OpenFuse contributes browser/computer workspace capabilities through isolated adapters/supervisors, not as a competing business API or database.
- Visual Skills and Scenario Skills are governed through the existing Skill Registry/Resolver, pinned provenance, license review, owner grants and independent runtime tool authorization.
- Worker execution must remain durable, lease-fenced, recoverable, idempotent and auditable.
- Memory is consent-aware, provenance-bearing, scope-bound and retention-controlled. Retrieved memory/skills/documents are untrusted context, never policy or authorization.
- Never claim provider, browser, computer, media, payment, network or database actions succeeded without real evidence.

## Current implementation phase

**Phase 09 — Existing Frontend API Integration: IN PROGRESS.**

Recent 2026-11-15 source increments:
- Bounded semantic recall reuses the existing tenant-scoped Knowledge Library/pgvector adapter.
- Episodic memory is stored in existing `conversation_messages.metadata`, retrieved by exact owner/workspace scope and injected as untrusted historical context only when current consent is active.
- Episodic records have configurable UTC expiry (default 90 days, accepted 7–3650 days), consent-version checks, single-record deletion and clear-all/consent-disable propagation. Original chat messages and citations are preserved.
- Citation provenance is persisted with assistant messages and hydrated by customer conversation detail/keyset pagination from validated owner-scoped Agent Run output or metadata fallback.
- Skill Resolver resolved/executed audit writes are idempotent; successful normal Agent completion records skill execution.
- Customer Agent Run list/detail responses also expose the existing `last_checkpoint_key` column to the Tasks durable checkpoint projection.
- Agent Studio supports a preferred model. FastAPI validates enabled model/provider state; the Model Router honors a preference only within the highest-priority active route policy. Agent Run snapshots preserve the exact model preference and configuration version.
- Attachment-aware configured chat enqueue, idempotency and owner/attachment checks are preserved in the updated SQL function.
- Existing Personal Memory settings UI now includes episodic experience summaries, expiry and deletion actions.
- Vercel Customer Frontend and FastAPI production deployments reached `READY` from latest source commit `b11e97fc6134e1bdcfdbfa0bb880eec62bd3d505`.
- Thirteen Supabase migrations for Skills, OpenFuse connections/browser sessions, Agent model preferences and assessment-derived EduTech completion were applied and recorded in migration history. The repository outbox migration filename is reconciled to the equivalent `moreai_durable_run_event_outbox_phase_07a` schema/functions already applied in the database; it was not applied twice.

Detailed evidence:
- `docs/implementation/PHASE-09-EPISODIC-MEMORY-CITATION-SKILL-LIFECYCLE-20261115.md`
- `docs/implementation/PHASE-09-EPISODIC-MEMORY-AGENT-MODEL-ROUTING-VERCEL-SUPABASE-20261115.md`
- `docs/implementation/PHASE-TRACKER.md`

## Production deployment status and critical runtime blocker

Vercel production aliases:
- Customer Frontend: `https://www.moreai.web.id`, `https://moreai.web.id`, `https://more-ai-portal-indihome.vercel.app`
- FastAPI: `https://more-ai-api.vercel.app`

Supabase project: `uunfgimtokhucegqbpce`.

Read-only production inspection found:
- API environment `MOREAI_AGENT_EXECUTION_ENABLED=false`.
- No current rows in `moreai_worker_capability_snapshots` (no worker heartbeat).
- No provider/model rows in `llm_providers` / `llm_models`.

Therefore Frontend and FastAPI are deployed and database migrations are applied, but OpenManus Agent Run execution is not production-operational yet. Do not enable Agent execution until a healthy durable worker, provider/model registry and secure provider credentials are configured. Do not create fake providers or invent API keys.

Vercel is suitable for the Customer Frontend and FastAPI request boundary, not a substitute for the persistent worker/browser supervisor. Worker and isolated OpenFuse Browser/Computer supervisors require persistent container hosting, secure egress, ClamAV and approval/session controls.

## Owner execution constraints

- Implement directly on `main`.
- Do not run functional tests, browser automation, API smoke tests, worker execution, provider calls, staging or staging deployments.
- Vercel production deployment was explicitly requested; production build/deployment status may be inspected.
- Supabase migrations were explicitly requested and applied. No bulk business-data seeding or fake data was added.
- Source inspection, Vercel build/deployment status and Supabase migration history are not runtime acceptance evidence.
- UI visual regression screenshots remain outstanding.

## Remaining Phase 09 work

1. Deploy `apps/worker` as a persistent container service and restore worker heartbeat/capability snapshots.
2. Configure enabled LLM providers/models and secure provider credentials for the worker/Model Router.
3. Keep Agent execution disabled until worker, provider, entitlement and security gates pass.
4. Complete OpenFuse Browser/Computer capability parity through isolated supervisors, owner approval, persistent sessions and customer-facing controls.
5. Complete Knowledge deletion/reindex lifecycle, Storage orphan cleanup and citation provenance for every conversation path.
6. Close every remaining Customer Dashboard action against typed FastAPI contracts and finish source-to-screen traceability across Chat, Agent Studio, Create, Research, Analyse, Code, Tasks, Workflow, Files/Results, Memory, Connections, Wallet and Profile.
7. Complete source governance and dependency inventory for OpenFuse, Visual Skills and Scenario Skills.
8. Reconcile remaining Phase 04/06/07/08 backend gaps before claiming integration complete.

## Next dependency-ordered work

**Phase 09 continuation — Durable Worker & Provider Readiness + Customer Dashboard API Closure.**

After worker/provider readiness and full Customer Dashboard/OpenFuse parity, Phase 09 can be assessed for completion. Phase 10 End-to-End Integration Verification and Phase 11 Integration Release Gate remain mandatory and cannot be marked complete under the current no-testing instruction.


## 2026-11-15 Phase 09 continuation update

Latest source-only continuation commits are recorded in `docs/implementation/PHASE-09-CONTINUATION-WORKER-READINESS-CUSTOMER-API-20261115.md`. Worker readiness now depends on a successful independent capability heartbeat; Docker probes `/ready`; long-running runs no longer block capability heartbeats. Google OAuth credential rotation and duplicate FastAPI browser-session route registration were corrected.

Phase 09 is still IN PROGRESS. The worker is not deployed to a persistent host; no provider/model rows or worker provider secrets are configured; Agent execution remains disabled. A routing contract mismatch remains (`chat`/`planning` runtime calls vs `general`-only Admin API/DB mutation RPC) and requires a forward-only Supabase migration. Vercel API deployment is still behind current main because the previous daily deployment quota was exhausted. No tests, staging, builds, runtime execution, provider calls, or deployment were performed in this increment.


## 2026-11-15 — Phase 09A Provider Routing & Secret Readiness

Phase 09A source contract work has now been implemented on main:
- FastAPI and the Supabase route mutation RPC support general, chat and planning task types.
- Added an audited provider configuration RPC storing only a public HTTPS base URL and worker secret environment-variable reference.
- Added Super Admin provider/model/pricing/routing forms using the existing UI style. Provider activation requires an explicit secret-installed attestation; actual API key values never enter the browser or database.
- Worker startup now requires enabled chat and planning routes and at least one referenced secret environment variable for each task. This is configuration validation only; it makes no provider calls.
- Current adapter support is OpenAI-compatible OpenAI and Google endpoints only. Anthropic native protocol is not implemented and is not offered for configuration.
- Supabase migrations applied: moreai_provider_configuration_and_route_types (20261115092653), moreai_provider_endpoint_allowlist (20261115092950).
- Report: docs/implementation/PHASE-09A-PROVIDER-ROUTING-SECRET-READINESS-20261115.md.

Operational status remains blocked: read-only inventory still shows no provider/model/routing rows and no worker heartbeat. No persistent worker host connection or host secret manager is available in this execution context. Agent execution remains disabled. Vercel API deployment is behind main because deployment quota was previously exhausted. No builds, tests, browser/API/worker probes, provider calls or staging were run. Phase 09A source contract is implemented but operational readiness is blocked; 09B host deployment is blocked; 09C remains in progress; 09D is deferred until 09A–09C close.
