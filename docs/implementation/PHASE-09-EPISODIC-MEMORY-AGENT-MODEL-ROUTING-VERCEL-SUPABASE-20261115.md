# Phase 09 Continuation — Episodic Memory, Citation Provenance, Agent Model Routing & Production Delivery

Date: 2026-11-15  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Source commit delivered to Vercel: `2381d4ca28fb44dd211ec412c0d04d7cb746a7f3`  
Supabase project: `uunfgimtokhucegqbpce`

## Owner constraints

- Direct commits to `main`.
- No staging environment and no functional tests, browser/API smoke tests, worker execution or provider calls.
- Vercel production build/deployment was requested and performed.
- Supabase migration was explicitly requested and performed.
- No secrets were invented or inserted.
- No application data was bulk-seeded or overwritten.

## Delivered source changes

### Episodic Memory and consent lifecycle

- Added metadata support to the existing Agent message object and Supabase conversation store.
- Successful Agent Run summaries are stored in existing `conversation_messages.metadata`, bounded to prompt/outcome, run/model identity, citations, immutable skill provenance and compact tool outcome labels.
- Retrieval is owner/workspace scoped, limited to eight episodes and injected as untrusted historical context.
- Write and recall require `enabled=true` and consent version `2026-11-14.v1`.
- Retention is controlled by `MOREAI_EPISODIC_MEMORY_RETENTION_DAYS` (default 90, accepted 7–3650 days), with per-record UTC expiry metadata.
- Expiry cleanup is opportunistic during Agent Run memory access and also runs when consent is disabled; it removes episodic metadata only.
- Customer API lists episodes, deletes a single episode and clears all personal/episodic memory while preserving original conversation messages and citation provenance.
- Existing Personal Memory UI was extended to display Agent experiences, outcomes, expiry and delete actions.

### Knowledge Citation Provenance

- Semantic retrieval continues to reuse the existing tenant-scoped Knowledge Library/pgvector RPC; no second vector store was created.
- Citation identity remains bound to source chunk and document UUIDs with exact `[source:<chunk UUID>]` marker validation.
- Final assistant messages persist bounded citations in message metadata.
- Customer conversation detail and keyset message pagination now hydrate validated citations from owner-scoped Agent Run output, with persisted message metadata as fallback.
- Existing Chat citation rendering remains canonical; no duplicate citation UI was introduced.

### Procedural Memory / Skill Resolver

- Existing immutable, hash-verified and license-reviewed Skill Registry/Resolver remains the sole procedural-memory authority.
- Resolved/executed audit inserts are idempotent across worker recovery.
- Successful normal Agent completion records skill execution.
- Episodic provenance stores compact skill snapshots, not raw skill instructions.
- Skill instructions remain untrusted context; permissions and tool authorization remain independent runtime controls.

### Agent Studio model routing and immutable snapshots

- Added owner-configurable `preferred_model_id` to Agent configuration.
- Added stable model IDs to the FastAPI model capability catalog.
- Agent Studio now provides an Auto Model Router option and a model preference selector.
- FastAPI validates that the selected model and provider are enabled.
- Supabase stores the model preference on the Agent configuration and embeds it into the immutable `agent_runs.input.agent_config` snapshot at enqueue time.
- OpenManus passes the immutable preference to the Model Router.
- Model Router only honors a preferred model if it is present in the highest-priority active route policy and satisfies required capabilities. A preference cannot override platform routing policy, provider eligibility, credits or capability constraints.
- Attachment-aware enqueue contract and idempotency validation are preserved. The legacy six-argument overload is removed to avoid ambiguity with the attachment-aware seven-argument RPC.

### Frontend / API contract corrections discovered during Vercel builds

- Corrected Customer Memory JSX fragment closure.
- Routed the legacy EduTech lesson tab through the canonical EduTech workspace.
- Normalized nullable Chat run status.
- Corrected Create view to use the canonical platform catalog media capability client.
- Aligned Agent Run client fields with the FastAPI lifecycle contract.
- Consolidated duplicate `CustomerToolCatalogItem` TypeScript declarations.
- Added the missing UUID import to the model capability response schema.

## Supabase migrations applied

All 12 migrations below returned `success: true` and are present in Supabase migration history:

1. `moreai_skill_intelligence_registry`
2. `moreai_skill_permission_grants`
3. `moreai_skill_source_files_and_audit`
4. `moreai_skill_aware_chat_enqueue`
5. `moreai_skill_atomic_ingestion_and_registry_audit`
6. `moreai_skill_package_review_rpc`
7. `moreai_google_connections_center`
8. `moreai_connection_action_receipts`
9. `moreai_calendar_event_mutation_actions`
10. `moreai_openfuse_persistent_browser_sessions`
11. `moreai_agent_model_preferences`
12. `moreai_agent_model_preferences_attachment_compat`

The model-preference compatibility migration preserves the existing attachment validation, ownership checks, active-conversation requirement, idempotency contract, and attachment linkage while snapshotting the preferred model.

No new database or second memory/vector store was created. Existing Supabase PostgreSQL, Auth, Storage, Realtime, RLS and pgvector architecture remains canonical.

## Vercel production delivery

Both connected Vercel projects reached `READY` on production target from source commit `2381d4ca28fb44dd211ec412c0d04d7cb746a7f3`.

- Customer Frontend project: `more-ai-portal-indihome`
  - Production aliases: `https://www.moreai.web.id`, `https://moreai.web.id`, `https://more-ai-portal-indihome.vercel.app`
  - Deployment ID: `dpl_AoZNYZsiG8kNbFXX9r8jwxkys1dD`
- FastAPI project: `more-ai-api`
  - Production alias: `https://more-ai-api.vercel.app`
  - Deployment ID: `dpl_331XHmu4yhV2AcwTSg4giPindWat`

Frontend Next.js build compiled successfully, passed TypeScript validation and generated all 19 static pages. API deployment reached Vercel `READY`. No runtime health check or functional request was sent.

## Critical production blockers — Agent execution is not live

Read-only production configuration inspection found:

- Vercel API environment has `MOREAI_AGENT_EXECUTION_ENABLED=false`.
- `moreai_worker_capability_snapshots` currently returns no worker heartbeat rows.
- Supabase `llm_providers` / `llm_models` currently return no provider/model registry rows.

Therefore the Customer Dashboard and FastAPI are deployed, and Supabase schema migrations are applied, but Agent Run execution through OpenManus/OpenFuse is not production-operational yet. Enabling the flag without a healthy durable worker and configured provider credentials would only expose failing requests. It was deliberately left disabled.

Vercel is suitable for the customer frontend and FastAPI request boundary, not as a substitute for the persistent durable worker/browser supervisor. The worker and isolated OpenFuse browser/computer supervisor need a persistent container deployment with secure provider credentials, browser egress enforcement, ClamAV and approval/session controls. No provider credentials were fabricated.

## Validation boundary

- No functional tests, browser automation, API smoke tests, provider calls, worker execution, staging or deployment verification via live user flows were performed.
- Vercel production build and deployment state were inspected because production deployment was explicitly requested.
- Supabase migration history was read after migration; this confirms migration records, not application behavior.
- Agent worker heartbeat and provider registry were inspected with read-only SQL.
- Frontend visual regression remains NOT VERIFIED.

## Phase status

**Phase 09 remains IN PROGRESS.** The requested memory, citation, skill lifecycle and Agent Studio model preference source increments are implemented. Full Customer Dashboard action-to-FastAPI closure and OpenFuse browser/computer parity are not yet accepted.

Phase 10 E2E Verification remains NOT ACCEPTED. Phase 11 Release Gate remains BLOCKED.

## Next work package

**Phase 09 continuation — Durable Worker & Provider Readiness + Customer Dashboard API Closure.**

1. Deploy `apps/worker` as a persistent container service and restore worker heartbeat/capability snapshots.
2. Configure enabled LLM providers/models and secrets through secure provider configuration; do not place secrets in source.
3. Keep Agent execution disabled until worker, provider, entitlement and security gates are satisfied.
4. Complete OpenFuse Browser/Computer isolated supervisor lifecycle and customer controls.
5. Close remaining Customer Dashboard actions against typed FastAPI contracts and finish source-to-screen traceability.
6. After the owner authorizes verification, perform Phase 10 functional acceptance and then Phase 11 release gate.
