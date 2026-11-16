# MoreAI Read-only Schema Reconciliation — 2026-11-16

Status: **READ-ONLY INSPECTION ONLY**. No SQL writes, migration application, test, staging, deployment or provider request was performed.

## Target
- Supabase project ref: `uunfgimtokhucegqbpce`
- Project name: `MoreAIdb`
- Region: `ap-southeast-2`
- PostgreSQL: `17.11.0.011`
- Project status returned by project listing: `ACTIVE_HEALTHY`
- Public tables: 94
- Migration history returned by Supabase connector: 116 versions; latest observed version `20261116113852` (`moreai_skill_ingestion_pending_until_validation`).

## Existing canonical domains observed in public schema

| Domain | Existing tables | Reconciliation direction |
|---|---|---|
| Agent lifecycle | `agent_definitions`, `agent_runs`, `agent_run_steps`, `agent_run_events`, `agent_run_checkpoints`, `tool_executions` | Sole durable run/step/event/checkpoint authority |
| Memory / RAG | `moreai_customer_memories`, `moreai_customer_memory_preferences`, `knowledge_documents`, `knowledge_chunks`, conversations/messages and run checkpoints/events | Extend existing domains; no second vector store |
| Skills | `moreai_skill_packages`, `moreai_skill_installs`, `moreai_skill_source_files`, `moreai_skill_execution_audit`, `moreai_skill_registry_audit` | Extend existing registry/resolver; do not create parallel registry |
| Browser | `moreai_browser_sessions`, `moreai_browser_session_events`, `moreai_browser_action_receipts`, `moreai_browser_capacity_leases` | Existing session/action/lease ownership is canonical |
| Computer | `moreai_computer_action_receipts`, `agent_workspace_files`, `agent_workspace_file_versions`, `agent_workspace_execution_commits` | Extend existing workspace/supervisor contract |
| Approvals | `agent_tool_approvals`, `agent_run_approval_pauses` | Reuse existing action approval lifecycle |
| Notifications | `notifications`, `notification_preferences`, `outbox_events` | Extend canonical durable inbox/outbox |
| Wallet / quota | `wallet_accounts`, `credit_ledger`, `credit_reservations`, `quota_policies`, `quota_usage`, `user_entitlements` | Preserve immutable ledger/reservation/quota separation |
| Artifacts / files | `artifacts`, workspace files/version tables, conversation attachments | Reuse canonical artifact and signed-download pipeline |
| Connectors | `moreai_connections`, `moreai_oauth_states`, `moreai_connection_audit`, `moreai_connection_actions` | Extend connection lifecycle and action audit |
| Knowledge | `knowledge_documents`, `knowledge_chunks` | Existing document/chunk vector retrieval domain |

## Memory schema finding

Read-only inspection shows:
- `moreai_customer_memory_preferences`: owner key, enabled flag, consent version, consent/disable timestamps.
- `moreai_customer_memories`: `id`, `user_id`, `title`, `content`, `source_type`, `scope`, `expires_at`, `created_at`, `updated_at`.
- `knowledge_documents` / `knowledge_chunks`: owner/workspace scope, source type/reference, content hash, ingestion state/lease, chunk content, vector embedding, token count and metadata.
- Conversation messages and Agent Run checkpoint/event tables already provide canonical conversation and working-state provenance.

The inspected customer-memory row shape does **not** expose a dedicated `memory_type`, source-record relation, confidence, freshness, review state or conflict-resolution metadata. This is a schema observation, not proof that no such semantics exist in JSON metadata, service code, or other existing records. Before P3, inspect the actual memory router/service, migrations, RLS, RPCs and metadata consumers. Do not add a second memory table or migration based only on this column snapshot.

Required P3 mapping remains:
1. Working → Agent Run/Step/Checkpoint/Event.
2. Conversation → Conversation/Message store.
3. Long-term → existing customer memory + explicit consent.
4. Episodic → evidence-linked completed run/artifact history (only add typed records if no canonical representation exists).
5. Semantic → Knowledge documents/chunks and authorized retrieval.
6. Procedural → approved immutable Skill/Workflow versions, never permission grants.

## Skill registry schema finding

`moreai_skill_packages` already stores owner, slug/name/description, source repository/ref/commit/path/blob SHA, content SHA-256, version, license ID/URL/evidence/status, manifest, requested permissions, validation status/report and publication status.

`moreai_skill_source_files` stores relative path, Git blob SHA, SHA-256, media type, byte size and text/binary payload. `moreai_skill_installs` stores owner, package, execution enablement, permission request/status and granted permissions. Separate execution and registry audit tables exist.

This is a substantial canonical foundation for P4. Do not create another registry, version table, source-file store or audit log until service/API/constraints are reconciled. New source ingestion must remain non-executable and unpublished until validation, license evidence and review are complete.

## Browser and computer schema finding

Browser session rows are owner/run scoped and include origin host, lifecycle status, encrypted state, expiry and profile-retention/deletion metadata. Session event history, action receipts with request hashes/status/result expiry, and worker capacity leases exist. Computer receipts are run/user/workspace scoped with idempotency/action hashes and bounded result expiry.

This does not prove a live browser worker, persistent profile volume, safe egress or deployed sandbox is operational. The Worker README continues to make browser capability conditional on private worker readiness/configuration and computer execution conditional on isolated supervisor gates.

## Goals and ideas gap to investigate

The inspected public table list did not expose dedicated tables named for goals or ideas. This does not prove absence of an equivalent scheduler/workflow/outbox representation. Before P9, inspect existing scheduler/cron jobs, workflow/run contracts, notification deduplication, outbox, and any JSON-backed domain representations. Do not add a second scheduler or notification inbox.

## Migration and safety notes

- The observed latest migration history is 116 entries, not 114 as the older tracker snapshot stated. Reconcile the phase tracker on the next documentation update.
- Latest observed migration names include skill publication evidence, skill ingestion pending-until-validation, browser profile retention, browser capacity leases, atomic browser session close, customer memory clear and server-only RLS denials.
- No migration was applied and no database state was changed.
- The read-only table/column inventory is a point-in-time observation. It is not a complete audit of policies, grants, functions, triggers, indexes, storage buckets, vector indexes or data retention.
- No user records or sensitive row contents were queried.

## Next engineering actions

1. Close P1 recursive inventory/SBOM and include the new iArt Motion Skills source; separately pin any selected pack repositories.
2. Complete P2 ADR/capability map against existing OpenManus/worker/API and this actual schema.
3. Inspect existing memory and skill source/service/API contracts before any P3/P4 code or schema changes.
4. Keep P7/P8 capability fail-closed until private worker/sandbox deployment contracts and owner/tenant security gates are met.
5. Continue Phase 09 existing Customer Dashboard integration; Phase 09 remains IN PROGRESS, Phase 10 is NOT ACCEPTED and Phase 11 is BLOCKED per the current tracker. The user has prohibited real testing and staging, so these acceptance gates cannot be represented as passed.
