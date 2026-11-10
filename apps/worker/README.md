# MoreAI Worker Boundary

The canonical database already has durable `agent_runs`, `agent_run_steps`, `agent_run_events`, `agent_run_checkpoints`, `outbox_events`, leases and worker RPCs. See `docs/implementation/supabase-schema-reconciliation.json`.

Worker execution must call the existing `moreai_worker_claim_run`, heartbeat/checkpoint and finish/cancel RPC lifecycle. **Do not start a worker that claims jobs until the OpenManus-compatible dispatcher and safe tool runtime are registered.** Otherwise it could consume real user runs without completing them. No worker polling process is enabled by this foundation increment.
