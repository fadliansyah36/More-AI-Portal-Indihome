# MoreAI — Worker Lease Fencing and Event Replay Cursor

Date: 2026-11-12  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: targeted source implementation in Phase 07 and Phase 06. No runtime acceptance claimed.

## 1. Worker lease ownership safety

Updated `apps/worker/app/runtime.py` to separate user cancellation from lease loss:

- A heartbeat response with `alive=false` marks lease ownership as lost, not as a user cancellation.
- A heartbeat transport failure also fails closed because the worker can no longer prove lease ownership.
- The worker cancels and reaps its local dispatcher after lease loss.
- The stale worker does not append run events or call the finish RPC after lease loss. The current owner or lease-expiry recovery path remains responsible for durable state.
- A final lease-loss check is made after dispatch completion and before terminal writes to narrow the completion/heartbeat race.

Commits:
- `4bf4daebbce10c7ad12d82c4074af8670ce222ae`
- `6f042071ee9e67bcb5750fbc6671ee49e0555ee3`

## 2. Event stream reconnection

Updated `apps/api/app/routers/agent_runs.py`:

- `GET /api/v1/agent-runs/{run_id}/events` and `GET /api/v1/agent-runs/{run_id}/stream` accept the standard `Last-Event-ID` header.
- Header values must be non-negative integers; malformed values return HTTP 400.
- The effective cursor is the maximum of the optional `after` query and `Last-Event-ID`.
- The existing owner check remains in place before event retrieval/streaming.

Commits: `3b592151022d4425dbf9081dad34dcd607944814`, `01ab679f4389d559142c55583e742784b0b22d2a` (advance the database query cursor after each emitted batch).

## 3. Remaining integration gaps

- Lease fencing and recovery still require multi-worker race tests, heartbeat-loss tests, and expiry/reclaim acceptance.
- Approval pause/resume still requires end-to-end proof across approval, denial, expiry, restart and replay.
- Full OpenManus Flow/server/session/tool parity remains incomplete.
- Provider retries/fallback, full RAG retrieval/indexing and complete tool handler coverage remain incomplete.
- Supabase schema/RLS/RPC and FastAPI domain coverage require further PRD-to-live-schema reconciliation.
- Customer, Captive Portal, EduTech, Partner and Super Admin UI workflows remain only partially integrated.
- Phase 10 acceptance and Phase 11 release gate remain blocked/not started.

## 4. Verification boundary

No tests, lint, typecheck, build, OpenAPI generation, migration apply, database writes, worker/provider runtime, browser QA, staging or deployment were run. These commits are implementation changes, not passing acceptance evidence. Existing UI paths and visual components were not changed. High-risk browser/Bash/Python activation remains gated.
