# Phase 04 — Durable run-level approval pause/resume
Date: 2026-11-11

## Implemented
- Added server-only approval pause records linked to existing approvals and a resume_pending marker on agent_runs.
- Atomic pause RPC verifies user and live worker lease, persists approval plus checkpoint, changes run to waiting_approval and releases lease/heartbeat in the same transaction.
- Approval decision RPC locks approval and pause, is idempotent, and requeues the run once for approved/denied outcomes.
- Claim RPC excludes pending approvals, expires stale approvals into a resumable expired outcome, and preserves attempt count for approval continuations while incrementing fresh attempts normally.
- Worker gate now raises a dedicated pause signal; WorkerRuntime does not mark the run failed/cancelled and stops heartbeat after pause.
- Existing one-time consume RPC still binds run/user/tool/argument hash.

## Security
- RLS enabled with explicit deny policies for anon/authenticated on pause records; service_role only.
- Privileged RPCs revoked from public/anon/authenticated and granted to service_role.
- No UI changes, no production business data writes.

## Verification limits
No staging, runtime tests, tests, build/lint/typecheck, provider calls or deployment per instruction. Migration 20261111140000_moreai_run_level_approval_pause_resume was applied successfully to canonical Supabase project uunfgimtokhucegqbpce. Read-only schema verification confirmed resume_pending, the pause table, all three RPC signatures, RLS enabled and the server-only deny policy. Runtime behavior remains unverified because worker execution/testing was not run. Phase 04 remains in progress pending migration application and runtime acceptance.
