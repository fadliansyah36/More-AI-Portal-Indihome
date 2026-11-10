# Phase 04 Backend Integration & Security Hardening — Execution Report

**Date:** 11 November 2026  
**Repository:** `fadliansyah36/More-AI-Portal-Indihome` / `main`  
**Upstream source:** `YunQiAI/OpenManusWeb` pinned snapshot `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`  
**Supabase project:** `uunfgimtokhucegqbpce` (`MoreAIdb`)  
**Deployment:** Not performed. Production execution flags remain disabled.

## 1. Executive result

Phase 04 is **IN PROGRESS**, not signed off as complete. The source inventory is preserved and mapped; safe Manus/Planning execution foundations, API contracts, worker lifecycle, streaming, LLM routing and transactional metering are implemented. Full OpenManus behavioral parity is not achieved because sandbox-dependent tools, the remaining tool adapters, complete upstream session/WebSocket/log-monitor behavior, and provider/tenant runtime configuration are not available.

| Area | Result |
|---|---|
| Phase 00 baseline | Prior screenshot/browser baseline PASS; latest lint/build PASS, latest browser smoke revalidation pending |
| Phase 04 source-to-engine port | Partial; complete module/capability map retained |
| Phase 05 Supabase reconciliation | Complete with three additive migrations; no reset/destructive DDL |
| Phase 06 FastAPI | Authenticated identity, conversation, catalog, run, cancellation and SSE contracts implemented |
| Phase 07 Worker | Durable RPC lifecycle, registered Manus/Planning dispatcher, durable plan store and checkpoint streaming implemented; worker disabled |
| Phase 08 LLM/orchestration | DB-scoped route resolver, fallback selection, OpenAI-compatible completion/streaming, idempotency, entitlement/quota/credit reservation and settlement implemented; no providers/routes seeded |
| Frontend integration | Auth-only Supabase browser client, FastAPI client and live SSE chat path; other product modules remain unintegrated |
| E2E / release | Blocked by empty runtime configuration and missing isolated sandbox; no deployment |

## 2. Upstream source preservation and capability mapping

- Pristine source snapshot remains under `vendor/openmanusweb/`.
- Pinned upstream SHA: `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`.
- Prior source-copy verification recorded 111/111 matching Git blob SHA entries.
- All upstream Python modules are represented in `openmanus-backend-capability-map.json`; every module is classified as adapted, partially adapted, pending, or intentionally blocked with a security reason.
- Adapted production modules live under `engine/`, `apps/api/` and `apps/worker/`; the upstream frontend is not used as the active MoreAI frontend.

### Agent and orchestration port

Implemented:
- Typed agent run context/result/checkpoint contracts.
- Explicit allowlisted agent registry; unknown agent keys fail closed.
- Gateway-backed Manus text runtime.
- Planning runtime with strict structured plan validation: objective, dependencies, expected output, tool requirement, risk and estimated usage.
- Durable planning steps in `agent_run_steps`; checkpoint manifest and per-step lifecycle.
- Flow factory and durable PlanningFlow contracts.
- Risk and tool requirements outside the enabled safe set fail closed.

Registered worker agents: `manus`, `planning`.

Not registered: SWE and tool/process agents that require a sandbox or approval engine.

## 3. Tool registry and security boundary

The full upstream tool inventory is represented by versioned JSON schemas and metadata in `engine/tools/catalog.py`, including:
- Bash
- Browser automation
- Chat completion
- File saver
- Google search
- Planning
- Python execution
- Generic run dispatch
- String-replacement editor
- Terminate/cancel

The registry is policy-enforced and default-deny. Catalog presence is not execution permission.

Intentionally blocked:
- Bash/Python: no disposable non-root sandbox, seccomp profile, CPU/memory/PID/process-tree limits or no-network enforcement is deployed.
- Browser: no isolated browser supervisor, SSRF/private-address protection, domain allowlist and download scanning service is deployed.
- Workspace editor/file operations: no isolated workspace root and safe artifact adapter is released.
- Google search: provider credentials, attribution and egress policy are not configured.

No unsafe upstream `exec`, global-CWD mutation, unrestricted browser or shell code was enabled.

## 4. FastAPI, session and event lifecycle

Implemented in `apps/api`:
- `GET /health`, `GET /ready`, authenticated `GET /api/v1/me`.
- Conversation list/create/detail and message enqueue routes.
- Agent catalog and tool catalog.
- Agent-run list/detail/cancel/events/stream routes.
- Supabase Auth JWT validation and user/owner-scoped repository queries.
- Correlation IDs and generic internal error responses.
- Server-only Supabase repository; service-role credential never enters browser code.

### Atomic chat enqueue

Migration `20261111030000_moreai_enqueue_chat_run` adds `moreai_enqueue_chat_run`. It validates conversation ownership and atomically inserts the user message, queued agent run and message/run relationship. The RPC is executable by `service_role` only.

### Streaming

The worker writes streamed model chunks as durable run checkpoints. FastAPI SSE resolves checkpoint state and emits terminal run status. The existing Chat UI consumes the authenticated SSE endpoint and renders incremental response text.

SSE is the implemented transport. Full upstream WebSocket compatibility, every session endpoint and complete log/thinking monitor parity remain pending.

## 5. Durable worker and Supabase

Implemented in `apps/worker`:
- Server-only Supabase RPC client for claim, heartbeat, checkpoint and finish.
- Durable structured planning store backed by `agent_run_steps`.
- Stateless worker registry factory.
- Manus and Planning runtime registration.
- Cancellation propagation; cancellation is not misreported as a generic failure.
- Worker startup requires explicit runtime enablement, an enabled LLM routing policy, billing configuration and quota policy.

Worker runtime is **not enabled or deployed**. No production run has been claimed.

## 6. LLM routing, streaming, credits and quota

Implemented:
- DB-driven routing across platform/global, user, workspace and partner scopes.
- Primary and configured fallback model resolution.
- HTTPS provider base URL and server-side secret environment reference validation.
- OpenAI-compatible completion and SSE stream adapter.
- Idempotent LLM request claim.
- Conservative pre-call credit estimate using model pricing and configured maximum output.
- Atomic entitlement + applicable quota-window consumption + wallet credit reservation + LLM request reservation link.
- Actual usage/token/cost recording.
- Quota reconciliation from reserved estimate to actual billable credits at settlement.
- Failed request releases both credit reservation and reserved quota; unknown provider outcome retains reservation to prevent duplicate free execution.

Three forward-only Supabase migrations were applied:
1. `20261111030000_moreai_enqueue_chat_run`
2. `20261111033000_moreai_llm_reserve_with_entitlement_quota`
3. `20261111040000_moreai_llm_quota_settlement_reconciliation`

All three are recorded in `supabase_migrations.schema_migrations`. New SECURITY DEFINER RPCs use an empty search path and service-role-only execution. No table reset, drop, truncate, seed, or RLS relaxation occurred.

### Current Supabase configuration blocker

Read-only inventory shows zero rows in:
- `llm_providers`
- `llm_models`
- `llm_routing_policies`
- `agent_definitions`
- `wallet_accounts`
- `quota_policies`
- `user_entitlements`

Provider secret references and credit conversion values are also not configured. The runtime therefore fails closed and cannot execute a real LLM request. No provider calls or real billing/settlement tests were performed.

## 7. Supabase security reconciliation

Post-migration inspection:
- 52 public base tables.
- RLS enabled on all 52 tables.
- 48 RLS policies.
- 30 migration history records.
- 17 SECURITY DEFINER functions.
- No `anon` or `authenticated` EXECUTE grant among those 17 functions; all are executable by `service_role`.

Existing findings retained:
- Four RLS-enabled tables have no policies and remain default-deny to client roles.
- Leaked password protection remains disabled in Auth settings; it was not changed.
- Unindexed foreign-key and unused-index advisor findings remain for workload/EXPLAIN review.
- No destructive schema operation was performed.

## 8. Frontend access rule and integration

Master PRD section 34 and root `AGENTS.md` now explicitly require:
- Browser → Supabase Auth only (sign-in, sign-up, OAuth, session, sign-out, recovery/MFA).
- Browser → FastAPI for all business data/actions.
- FastAPI → Supabase server-side after JWT verification and tenant/ownership authorization.
- Service-role and provider secrets are server-only.

Implemented frontend:
- Typed `lib/api/client.ts` with bearer session token.
- Authenticated SSE client.
- Chat view creates conversations, atomically enqueues runs, consumes streamed checkpoints and reads terminal status.

Not yet integrated:
- Dashboard analytics, tasks, files/artifacts, agent studio, research, code, credits/wallet, partner/network, admin and other product modules. Existing static/demo data in legacy UI modules still needs to be replaced by API-backed data. This is deliberately not represented as completed.

## 9. Verification

Latest verified workflows:
- [Engine contract tests](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42890612659) — PASS.
- [Latest API and worker tests + frontend baseline](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42891046534) — API tests PASS; worker tests PASS; baseline dependency install, lint and build PASS; application startup did not complete during this run. New revalidation run 42891526705 is queued. Previous five-viewport browser screenshot baseline remains the last completed browser proof.
- Prior browser screenshot baseline: [Phase 00 run](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42883484475) — PASS at 360, 390, 768, 1024 and 1440 px.

No real Supabase Auth user token was supplied to CI, so live authenticated API E2E was not run. No worker deployment, provider call or production deployment occurred.

## 10. Remaining work — Phase 04 is not complete

1. Complete the isolated sandbox service and threat model for Bash/Python/process execution.
2. Complete browser supervisor with SSRF controls, allowlist, isolated contexts and download scanning.
3. Implement and test safe adapters for all remaining catalogued tools, including artifact storage, search, editor and tool-call provider response handling.
4. Finish upstream API/session/WebSocket/log/thinking parity or record explicit accepted SSE replacement ADRs.
5. Add tenant/entitlement/approval and tool-execution end-to-end tests.
6. Populate approved provider/model/routing configuration, server-side provider secrets, user entitlement, quota policies, wallet and credit conversion through reviewed seed/admin procedures.
7. Run a real test-user request through browser → FastAPI → worker → LLM → Supabase ledger/quota → SSE and verify idempotency, cancellation, failure/refund and retry.
8. Complete UI regression for every existing route before frontend rollout.

**Next phase:** continue Phase 04 — sandbox and remaining tool/runtime parity. Do not enable execution or deploy until the release gates above pass.
