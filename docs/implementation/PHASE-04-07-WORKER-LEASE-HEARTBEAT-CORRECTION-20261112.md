# MoreAI Phase 04–09 Continuation — Worker Lease Heartbeat Correction (2026-11-12)

## Scope and baseline
- Repository: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`.
- Baseline worker runtime blob: inspected immediately before change.
- Implementation commit: `5dcfda51dfa69b4c321348959ff00e58cf2585e0`.
- Prior Customer route reconciliation: `21201caaec53be5b80bdc5e3e2ec07c802d54289`.

## Implemented
- Updated `apps/worker/app/runtime.py` heartbeat scheduling to derive its interval from the configured run lease: `max(1s, min(30s, lease_seconds / 3))`.
- This removes the unsafe fixed 30-second renewal interval for deployments configured with lease durations shorter than 90 seconds. The worker now attempts renewal within one third of its configured lease, with a 1-second lower bound.
- Existing fail-closed behavior on heartbeat transport failure or lease loss remains unchanged: local dispatch is cancelled and stale workers do not write terminal state.

## Supabase evidence (read-only)
- Inspected canonical project `uunfgimtokhucegqbpce`.
- Confirmed workspace RPC inventory currently includes `moreai_workspace_get_file`, `moreai_workspace_begin_write`, `moreai_workspace_commit_write`, and `moreai_workspace_abort_write`.
- Confirmed `agent_workspace_files` persists latest file metadata and pending CAS reservation fields. The inspected schema does not expose a separate workspace file version-history table, so a safe history/restore API cannot be inferred from latest-version metadata alone.
- Confirmed durable run, checkpoint, event, approval-pause, and approval tables exist. This schema presence is not proof of all recovery/resume transitions working.

## Remaining gaps
- Phase 04: workspace list/read/delete/history/restore API and full upstream Flow/server/session parity remain incomplete; browser egress and sandbox release gates remain closed.
- Phase 07: retry/dead-letter/reaper/approval-decision-resume-enqueue/outbox replay acceptance still requires implementation reconciliation and authorized evidence.
- Phase 08: worker registry still only activates Manus and Planning; complete upstream agent/provider/tool/flow parity and retrieval-index RAG lifecycle are outstanding.
- Phase 06: API contract and per-domain authorization matrix remain incomplete.
- Phase 09: screen-by-screen real API binding for Customer, Partner, Captive Portal, EduTech and Super Admin remains incomplete. EduTech's dedicated persistence model is not present in the inspected public schema.
- Phase 10/11: not executed. The standing instruction against real testing/staging remains in force.

## Verification and deployment
- No tests, lint, typecheck, build, runtime worker, provider call, browser QA, staging, migration, or deployment was run.
- No Supabase schema/data was modified.
- This commit is a source correction, not Phase 07 acceptance and not a production-readiness claim.

## Phase status
- Phase 04 IN PROGRESS
- Phase 05 COMPLETE per existing tracker (no schema change in this continuation)
- Phase 06 IN PROGRESS
- Phase 07 IN PROGRESS
- Phase 08 IN PROGRESS
- Phase 09 IN PROGRESS
- Phase 10 BLOCKED pending explicit test authorization and safe verification environment
- Phase 11 NOT STARTED

## Next implementation order
Continue Phase 04 workspace CRUD/version history/restore and upstream server/session parity; then Phase 07 approval resume/retry/recovery/outbox semantics; then Phase 08 upstream provider/agent/tool/flow and RAG/accounting parity; then Phase 06 contracts/authorization; then Phase 09 existing-screen integration. Do not enter Phase 10/11 until testing authorization is granted.
