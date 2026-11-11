# Phase 07A — Durable Event Outbox Acceptance (database schema gate)
Date: 2026-11-11
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`

## Scope
Reconcile the existing event/outbox schema, implement a single monotonic per-run event stream, idempotent append, publisher leasing, at-least-once Broadcast delivery, acknowledgement, bounded retry and dead-letter.

## Source and schema changes
- Extended the canonical `public.outbox_events`; no parallel outbox table was created.
- Added `public.agent_run_event_counters` with per-run row locking.
- Added event_key and run_sequence uniqueness for agent-run outbox events.
- Added worker_id and lease_expires_at fencing fields.
- Added server-only RPCs: `moreai_worker_append_run_event`, `moreai_worker_claim_event_outbox`, `moreai_worker_ack_event_outbox`, `moreai_worker_retry_event_outbox`.
- Replaced checkpoint/finish RPC bodies to append through the same sequence counter before checkpoint/terminal state transition.
- Added a follow-up lease-fencing migration for outbox retry; expired workers cannot mutate a reclaimed event.
- Worker app runs `DurableEventOutboxPublisher` alongside the durable execution loop; publisher uses Supabase Realtime private Broadcast and acknowledges only after HTTP success.

## Live Supabase evidence
Canonical project: `uunfgimtokhucegqbpce`.
- Applied migration `moreai_durable_run_event_outbox_phase_07a`, recorded as version `20261111091531`.
- Applied migration `moreai_outbox_retry_lease_fencing` (source migration: `20261111100000_moreai_outbox_retry_lease_fencing.sql`).
- Read-only post-apply inspection confirmed counter/outbox columns exist.
- Read-only function catalog inspection confirmed all six RPC signatures exist.
- ACL inspection confirmed anon/authenticated cannot execute these RPCs and service_role can.
- No synthetic agent_run or outbox records were inserted into production for testing. No live event was claimed, published, retried, acknowledged, or cancelled in production.

## Delivery semantics and remaining acceptance evidence
- Event append is transactional with durable replay and outbox creation.
- Per-run sequence allocation is serialized using the counter row lock; idempotency is scoped by aggregate/run + event_key.
- Publisher claims rows with SKIP LOCKED, expires leases, retries with exponential backoff and dead-letters after 12 attempts.
- Broadcast delivery is at-least-once. Clients must deduplicate on event_id/sequence. Durable GET/SSE event history remains the replay source.
- **Not yet runtime-accepted:** no worker process is confirmed deployed/running against this migration; no end-to-end publish/subscribe, retry/dead-letter, process restart or cancellation recovery proof has been run. This needs an isolated staging run with disposable test tenant/run, not production synthetic traffic.

## Security advisor
After the migration, Security Advisor still reports five RLS-enabled tables without policies (`agent_tool_approvals`, `network_gateway_nonces`, `network_verification_method_catalog`, `partner_access_code_redemptions`, `partner_access_codes`) and leaked-password protection disabled. These are tracked security findings and are not hidden by the Phase 07A result. Review each table's server-only access contract before adding explicit deny policies; enable leaked-password protection through Auth configuration.

## Verification limits
- Migration application and schema/ACL introspection passed.
- No valid production event append/publish test was performed to avoid inserting or mutating real production activity.
- No local lint/typecheck/build or GitHub Actions execution was available in this connector pass.
- This is a database schema acceptance increment, not full Phase 07 acceptance.

## Next work
1. Provision isolated staging tenant/run and run worker process-level append → publish → ack, replay, retry, dead-letter, cancellation and restart recovery tests.
2. Complete SWE workspace metadata/version/lease/CAS/CRUD and object snapshot recovery.
3. Continue upstream backend parity against the pinned source map: Flow/server/session, full LLM provider layer, memory/RAG, all tools and orchestration.
4. Complete Phase 06 domain API/governance and Phase 09 UI API connections only with screenshot baseline evidence.
5. Phase 10–11 remain blocked until all required automated and security gates pass.
