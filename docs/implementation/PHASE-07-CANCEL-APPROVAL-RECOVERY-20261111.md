# Phase 07 — Cancellation of approval-paused runs

- Replaced `moreai_worker_request_cancel` so queued and `waiting_approval` runs become terminal `cancelled` immediately, leases are cleared, pending approval and pause records are denied, and pause checkpoints are marked cancelled.
- Running work remains cooperative cancellation via `cancel_requested_at` and heartbeat/tool-boundary propagation.
- Cancellation event is idempotently written to `agent_run_events` and `outbox_events` using a stable per-run event key.
- Migration: `20261111160000_moreai_cancel_waiting_approval_and_outbox.sql`.
- Runtime and integration verification not performed.
\nMigration `20261111160000_moreai_cancel_waiting_approval_and_outbox.sql` was applied successfully to canonical Supabase. The updated RPC signature was confirmed by read-only catalog inspection. No worker runtime test was run.\n