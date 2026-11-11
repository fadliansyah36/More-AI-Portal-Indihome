# MoreAI Direct-main Integration Continuation — 2026-11-11

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Canonical Supabase project: `uunfgimtokhucegqbpce`

## Operating constraints

- Direct commits to `main`; no new branch.
- No staging, deployment, test suite, build, lint, typecheck, browser test, provider call or runtime acceptance test was run in this continuation.
- Existing UI/UX remains protected; no visual component or navigation redesign was included.

## Fresh source and schema inspection

- Re-read the canonical `AGENTS.md` on `main`.
- Inspected FastAPI application/router wiring, Customer/Partner/Admin routes, worker runtime, dispatcher, registry factory, outbox publisher and worker RPC client.
- Inspected the live Supabase project metadata, public table/column/constraint inventory and migration history using read-only connector operations.
- Supabase project reports PostgreSQL 17.11, region `ap-southeast-2`, status `ACTIVE_HEALTHY`.
- The live migration history includes durable run lifecycle, worker lease/recovery/cancellation, event outbox/retry lease fencing, tool approval pause/resume, workspace CAS versioning/expiry recovery, notifications/private artifacts and server-only RLS denials. No SQL migration was applied by this continuation.

## Code changes

### 1. Customer workflow step privacy alignment

File: `apps/api/app/routers/customer.py`

- Changed `GET /api/v1/customer/agent-runs/{run_id}/steps` to return the same metadata-only contract as the canonical `/api/v1/agent-runs/{run_id}/steps` route.
- Removed step `input`, `output`, `error` and `updated_at` from the customer transport response.
- Added bounded `limit` query validation (1–500).
- Commit: `1efe43a0f87b97596ada43126aa9dad6d3781267`.

### 2. Durable event replay bounds

File: `apps/api/app/routers/agent_runs.py`

- Added validated non-negative replay cursor and bounded page size (1–500) to run event replay.
- Added validated wait window (1–120 seconds) and non-negative cursor to the SSE stream.
- Commit: `b2a49909792f1ea17627d91519835d6572a0eb54`.

File: `apps/api/app/routers/customer.py`

- Applied the same bounded replay cursor and SSE wait window to the Customer route.
- Commit: `de60315866ac60558b67c117d5fb9d3b3ada6f65`.

## Runtime architecture findings — still open

- Worker currently runs the durable claim/heartbeat/checkpoint/finish loop and a separate leased outbox publisher.
- Durable event publisher is at-least-once; clients/consumers must deduplicate using event identity and sequence.
- Worker registry currently enables Manus and Planning only. SWE, browser, Bash/Python and workspace editing remain disabled or gated on sandbox/browser supervisor deployment and security acceptance.
- Browser activation is explicitly fail-closed unless service URL/token and egress enforcement are configured.
- API chat submission is fail-closed while agent execution is disabled; it requires provider, entitlement/credit policy and worker runtime configuration.
- Capability map still marks several upstream modules as PARTIAL or BLOCKED; source snapshot presence is not production parity.
- Supabase introspection was read-only. Existing RLS-enabled tables and migrations were inspected; this is not a replacement for a complete policy/RPC audit.

## Explicitly not claimed

No end-to-end integration, live provider execution, sandbox/browser security, worker crash-recovery proof, frontend page-by-page wiring, or Phase 04/06/07/08/09 acceptance is claimed. No runtime tests were performed, by instruction.

## Remaining work, in dependency order

1. Phase 04: finish full OpenManus server/session/Flow lifecycle parity; wire approval pause/resume into dispatcher; complete workspace/SWE adapter; deployable browser supervisor and socket-level egress enforcement.
2. Phase 07: close publisher failure/dead-letter/lease recovery and worker retry/timeout/cancellation lifecycle gaps; maintain idempotent event replay.
3. Phase 08: complete upstream capability mapping for agents, provider retries/circuit breakers, ReAct/tool call semantics, all supported tool adapters, memory/RAG and metering.
4. Phase 06: complete remaining Customer/Partner/Wi-Fi/Captive Portal/Super Admin domain contracts against live schema and permission matrix.
5. Phase 09: wire each existing UI route/component to the typed API client, remove any remaining demo/fallback data, preserve all visual behavior.

Phase 10 and 11 remain blocked until their required runtime and security evidence can be performed under separately authorized conditions.
