# Phase 04/07 continuation — Durable Run Deadline and Browser Egress Readiness

Date: 2026-11-12  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Previous implementation baseline: `95fbbf8ff6658011e4cc09bd5b33bccc2ec9b141`  
Source commit for this increment: `0c92bb8b85136e9bc4d12ee7a6246529f50bfdfd`

## Scope

This is an additional implementation increment in Phase 04 and Phase 07. It does not close the complete ordered integration scope.

## Phase 07 — bounded durable run timeout

- Added `run_timeout_seconds` to `WorkerSettings`, bounded from 30 to 7200 seconds; default 1800.
- Wired `MOREAI_RUN_TIMEOUT_SECONDS` in worker bootstrap and documented it in `.env.example`.
- `WorkerRuntime.run_once` now races dispatch against the configured wall-clock deadline, user cancellation and lease loss.
- On timeout, the worker cancels and awaits the dispatch task, checks lease ownership again, appends the idempotent `run.timed_out` event and calls the existing durable finish RPC with error `agent_run_timeout` and a retry delay. The database remains authoritative for attempt/max-attempt and retry scheduling.
- Added `apps/worker/tests/test_run_timeout.py` covering dispatch cancellation, timeout event, retryable finish transition and timeout configuration bounds.

## Phase 04 — browser supervisor readiness

- Extracted a stdlib-only `browser_readiness` helper to avoid importing optional FastAPI/Playwright runtime packages in policy unit tests.
- The browser supervisor readiness response is now `ready` only when the private proxy URL is valid, a sufficiently long proxy token is configured, egress enforcement is enabled and a bounded TCP connection to the proxy succeeds.
- An unreachable proxy produces `degraded`; credentials are not returned.
- Added tests for reachable and unavailable proxy states.
- This health/readiness check complements existing pinned CONNECT proxy and internal Docker network policy. It is not a substitute for running the actual Docker network isolation acceptance script.

## Files changed

- `.env.example`
- `apps/worker/app/client.py`
- `apps/worker/app/main.py`
- `apps/worker/app/runtime.py`
- `apps/worker/tests/test_run_timeout.py` (new)
- `apps/sandbox/app/browser_readiness.py` (new)
- `apps/sandbox/app/browser_service.py`
- `apps/sandbox/tests/test_browser_readiness.py` (new)
- `docs/implementation/PHASE-TRACKER.md`
- `docs/implementation/openmanus-backend-capability-map.json`

## CI evidence

[Phase 04 Sandbox Security Tests — run 43170133933](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43170133933): all four jobs PASS:
- worker-contract — includes durable run timeout regression test;
- api-contract;
- engine-policy;
- sandbox-policy — includes browser readiness tests.

## Remaining blockers

- No worker service was deployed or activated; no real lease-expiry/crash chaos test was performed.
- No browser supervisor/proxy container was deployed; the Docker network-isolation acceptance script and live SSRF/DNS-rebinding tests against the deployed proxy remain outstanding.
- No real LLM provider call or authenticated Customer → FastAPI → worker → provider → Supabase E2E was performed.
- Upstream OpenManus Flow/server/session/WebSocket/log/tracking parity remains incomplete.
- SWE agent runtime and complete workspace create/list/read/edit/restore lifecycle still require end-to-end integration.
- Full provider/model routing health/circuit breaker and all upstream agent/tool adapters remain incomplete.
- Phase 06 complete OpenAPI domain compatibility and live tenant/RLS denial proof remain incomplete.
- Phase 09 all Customer screens remain incomplete; only supported flows currently bound to typed FastAPI APIs are considered integrated.
- Phase 10 is partial; Phase 11 remains blocked. No deployment was performed.

## Next dependency-ordered work

1. Complete Phase 04: upstream Flow base/factory lifecycle, server/session/WebSocket compatibility through authenticated FastAPI, persisted event/log/tracking parity, and SWE workspace CRUD/version/restore.
2. Complete sandbox supervisor deployment integration, forced proxy egress, DNS pin-to-socket proof, subresource/redirect enforcement, download scanning and tenant-scoped domain policy.
3. Complete Phase 07 crash/restart, lease fencing, retry, timeout, cancellation and approval-resume race acceptance against the durable database functions.
4. Complete Phase 08 upstream agent types, LLM streaming/tool-call compatibility, provider health/circuit breaker, tool adapters, memory and RAG citations.
5. Complete Phase 06 generated OpenAPI compatibility, auth/tenant/partner boundaries and mutation idempotency.
6. Finish Phase 09 all existing Customer UI/API workflows without visual redesign or fake data.
7. Only then run Phase 10 authenticated real-provider E2E and Phase 11 release gate. Do not deploy before all required gates pass.
