# MoreAI — Browser Egress & Durable Event Lifecycle Increment
Date: 2026-11-11
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Base revision inspected: `f867e4feefab80533d3e08d08d038dcc4ec04b9f`

## Delivered on main

### Browser network topology
- Added `apps/sandbox/Dockerfile.browser` for a separate non-root browser supervisor/proxy image with pinned Python service dependencies and Chromium.
- Added `apps/sandbox/compose.browser.yml` with two networks:
  - `browser_isolated` is a Docker internal network with no default external route.
  - Browser supervisor attaches only to `browser_isolated`.
  - Egress proxy attaches to both `browser_isolated` and `browser_egress`; only this proxy has an external network interface.
- Browser service remains authenticated and uses the DNS-pinned CONNECT proxy; the browser service is not published on a host port by this compose file.
- Containers use read-only root filesystems, tmpfs, dropped capabilities, no-new-privileges, and CPU/memory/PID limits.

### Important security qualification
- This is an authored deployment topology, not a deployed or packet-verified firewall. No Docker host/network namespace was available to prove that direct egress fails. The browser activation gate remains CLOSED. Do not set production browser flags based only on this compose file.
- A production deployment must attach the trusted worker to the private control network, restrict who can join it, verify the browser supervisor cannot route to any external destination, and run negative egress tests from inside the browser container. The proxy's outbound network must itself be controlled and logged.
- The supervisor's readiness response is not a network attestation. Browser remains disabled until deployment evidence exists.

### Phase 07 durable event lifecycle
- Added migration draft `20261111110000_moreai_durable_run_event_outbox.sql`.
- Adds per-run monotonic sequence counters, idempotent outbox keys, bounded JSON payloads, RLS-denied client access, and a service-role-only append RPC.
- Appends each event transactionally to the existing `agent_run_events` replay stream and to the durable outbox.
- Added worker client `append_run_event`.
- Worker lifecycle now emits run.started, run.progress, run.completed, run.failed and run.cancelled. Checkpoint event payloads are allowlisted scalar metadata only; checkpoint bodies/tool arguments/observations are never published.
- Durable Manus tool dispatch emits tool.started, tool.completed and tool.cancelled events with tool identity and round/index metadata, not arguments or tool output.
- Existing Customer run event list/SSE endpoints continue to read `agent_run_events` in ascending sequence order; the new append RPC makes sequence allocation serialized and idempotent per run/event key.

## Not complete / acceptance blockers
1. Migration is a source draft only; it has NOT been applied to Supabase. Worker event publishing therefore must not be enabled in a deployment until schema review, apply, and RPC verification are authorized and completed.
2. No event outbox publisher/consumer delivery loop is implemented. Current outbox is a durable transactional record paired with the replay table; external Realtime fan-out/consumer acknowledgement and dead-letter retry worker remain open.
3. Workspace adapter still has only safe create/edit behavior. List/read/delete, version snapshots, DB-backed path leases, compare-and-swap writes, crash recovery and project Git operations remain open. Storage-only upsert is not safe for concurrent SWE agents.
4. Full upstream OpenManus Flow/server/session/WebSocket parity remains open. Existing MoreAI FlowFactory is currently a small factory boundary, not a complete port of upstream Flow, PlanningFlow, FlowFactory and web server/session semantics.
5. Full backend parity is not yet achieved for upstream memory/RAG/vector retrieval, document ingestion/chunking/embedding lifecycle, long-term memory, all provider clients, browser action parity, terminal/process tools and complete workflow types. Existing conversation memory, durable plan store, metered LLM gateway and selected adapters are partial integrations, not full upstream parity.
6. Phase 06 domain APIs and Super Admin governance remain incomplete. Existing API coverage includes selected Customer/Partner and permission-checked Super Admin read/status operations, but not the full Wi-Fi/captive portal/gateway/voucher/settlement/analytics/notifications/education/security domain set. Further governance actions require permission-specific transactional RPCs, idempotency and immutable audit records.
7. Phase 09 remains blocked by the AGENTS.md screenshot gate. No UI files were edited in this increment.
8. No test, lint, typecheck, build, browser network test, database write/migration, E2E, provider call or deployment was run. No runtime pass is claimed.

## Next phase order
- 07A: review/apply event migration, verify RPC, add outbox publisher/consumer retry/ack and prove replay/cancellation under worker restart.
- 04/08: complete workspace file API + version/lease/CAS; full upstream Flow/server/session and memory/RAG/provider/tool capability map with source-to-adapter evidence.
- 06: reconcile every remaining Master PRD domain with live Supabase schema/RLS before adding forward-only migrations and permission-scoped transactional governance.
- 09: only after exact screen/route baseline and before/after screenshots are available, connect existing screens through typed API methods without visual redesign.
- 10–11: integration and release gates after explicit authorization to run verification and deployment.

## Phase 07A continuation — canonical outbox reconciliation and publisher

Read-only inspection of canonical Supabase project `uunfgimtokhucegqbpce` confirmed:
- `public.agent_run_events` exists with `id, run_id, event_type, sequence, payload, created_at`.
- `public.agent_run_checkpoints` exists.
- `public.outbox_events` already exists with UUID `aggregate_id`, `aggregate_type`, `event_type`, JSON payload, status lifecycle `pending/processing/published/failed/dead_letter`, attempts, available_at, locked_at, published_at and last_error.
- `outbox_events` already has restrictive RLS denying anon/authenticated clients.
- Existing `moreai_worker_checkpoint` and `moreai_worker_finish_run` previously allocated sequence using `max(sequence)+1`, which could race with a new counter. The migration now replaces both functions to append through the same per-run row lock and event counter before releasing the worker lease.

Changes committed:
- The event migration now extends the existing canonical `outbox_events` table rather than creating a competing second outbox.
- Adds event-key and per-run sequence uniqueness, worker lease metadata, transactional append, worker lease ownership checks, and service-role-only RPCs.
- Replaces checkpoint and finish RPCs to use the same serialized event append, preserving checkpoint/finish behavior while eliminating split sequence allocation.
- Adds `moreai_worker_claim_event_outbox`, `moreai_worker_ack_event_outbox`, and `moreai_worker_retry_event_outbox` with SKIP LOCKED leasing, lease expiry recovery, exponential backoff, and dead-letter after 12 attempts.
- Worker client publishes claimed records through the Supabase Realtime Broadcast REST endpoint to private per-run topics; the consumer acknowledges only after the broadcast endpoint succeeds. Delivery is at-least-once; consumers must deduplicate by event_id/sequence.
- Worker starts the publisher alongside the durable agent worker. A lost lease after publish can produce a duplicate broadcast; this is intentional at-least-once behavior.

Important: the live schema inspection was read-only. No migration was applied and no RPC was invoked against production. The source migration still requires review and application before this publisher can function. Existing SSE GET/stream routes remain the authoritative durable replay path; Realtime Broadcast is only the low-latency notification path.
