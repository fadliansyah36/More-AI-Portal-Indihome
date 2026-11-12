# Phase 04 Increment — PlanningFlow Dependency Handoff & Browser Egress Probe Readiness

Date: 2026-11-12  
Branch: `main`  
Baseline: `fbfda5c1701698c9b45b363a8365e4d9bfb2186d`  
Latest implementation commit: `29ddce091d2b504bd6f3b0f3d8f18049cfe0a171`  
Documentation commits: `154b726ce6051d3a822299579f0ba4d7f9fe679a`, `cfe62543e8500f4b014f6922167ae18f312002b7`, `7776b8eb479a7319f4cd1d47b9188644d03929db`

## Scope implemented

### PlanningFlow dependency propagation

- `engine/agents/planning_runtime.py` now passes outputs from persisted, successfully completed predecessor steps into the dependent step's execution prompt.
- Each execution payload now includes the explicit dependency index list.
- A follow-up correctness fix tracks predecessor outputs in the current execution loop rather than reading the stale pre-run snapshot; restored completed steps also seed the same output map. This ensures the dependent prompt contains the actual output produced during this run or recovered from durable storage.
- Dependency context is assembled only after the runtime confirms every dependency is completed; the existing strict earlier-step validation prevents cycles.
- Serialized dependency handoff is bounded to 20 KB to prevent unbounded prompt growth.
- The step executor receives the expected output plus predecessor results rather than executing every step as an isolated prompt.

### Browser egress acceptance probe prerequisite

- `apps/sandbox/Dockerfile.browser` now installs `curl`.
- The existing `apps/sandbox/scripts/verify-browser-network-isolation.sh` requires curl inside the browser container to prove the positive case (allowlisted HTTPS request through the authenticated proxy). Without it, the acceptance script would always fail the positive probe even if the proxy were functioning.
- No browser network topology or egress policy was relaxed.

## Tests and evidence

- Engine Contract Tests: [run 43171904754](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43171904754) — PASS.
- Follow-up Engine Contract Tests: [run 43172280306](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43172280306) — PASS, including the stronger assertion that the dependent step receives the actual predecessor output.
- Follow-up Phase 04 Sandbox Security Tests: [run 43172280282](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43172280282) — PASS, all four jobs.
- Phase 04 Sandbox Security Tests: [run 43171983972](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43171983972) — PASS, all four jobs: sandbox-policy, engine-policy, api-contract and worker-contract.
- The engine test asserts that the second planning step receives dependency index `0` and the first step's output in its prompt.
- The sandbox CI job verifies policy/readiness unit contracts; it does not execute Docker Compose or the network isolation acceptance script.

## Files changed

- `engine/agents/planning_runtime.py`
- `engine/tests/test_planning_runtime.py`
- `apps/sandbox/Dockerfile.browser`
- `docs/implementation/PHASE-TRACKER.md`
- `docs/implementation/openmanus-backend-capability-map.json`

No Customer UI files were changed. No Supabase schema migration was required.

## Remaining Phase 04 blockers

1. Upstream `app/web` server/session parity is incomplete: endpoint-by-endpoint compatibility for session lifecycle, job/task operations, log parser, thinking/progress tracker and WebSocket semantics remains open. Durable run/session listing and SSE replay cover only part of that surface.
2. SWE workspace lifecycle remains partial: workspace create/rename/archive, membership read/revoke, file list/download/history/restore and approved editing/reading exist, but file upload/create/rename/delete lifecycle and invitation/acceptance/role semantics are not yet closed.
3. Flow parity remains partial: dependency outputs are now handed off, but complete upstream Flow lifecycle, multi-agent semantics, durable pause/resume/replay and factory coverage still require implementation and tests.
4. The browser supervisor is not deployed or connected to a running worker. The Compose file has an internal browser network and a proxy-only egress bridge, but deployment-level service connectivity and acceptance are still outstanding.
5. No live Docker verification has been run for direct IPv4/IPv6 denial, allowlisted HTTPS proxy success, private/metadata/unauthorized host rejection, DNS rebinding at socket level, redirects/subresources, or download scanning. The browser remains disabled by default.

## Deployment and release status

- No staging or production deployment.
- No worker activation.
- No browser supervisor/proxy container activation.
- No authenticated Customer → FastAPI → worker → OpenManus → provider → Supabase E2E.
- Phase 04 remains IN PROGRESS. Phases 07 and 08 must not be treated as unblocked for acceptance until Phase 04's remaining dependency gates are closed. Phase 06 and 09 remain downstream integration work; Phase 10 is not accepted and Phase 11 remains blocked.

## Next implementation sequence

1. Complete durable Flow lifecycle and upstream server/session/log/thinking/WebSocket parity through FastAPI and persisted run/event state.
2. Complete SWE workspace file lifecycle using lease-fenced, immutable-version operations and explicit owner authorization; do not bypass CAS with direct metadata writes.
3. Connect the worker to the browser supervisor over a private authenticated service network and run the actual Compose network isolation verifier on a controlled Docker host.
4. Add live negative/positive browser egress tests and only then enable browser tools behind the release gate.
5. After Phase 04 acceptance, continue Phase 07, then Phase 08, then Phase 06 and Phase 09 in dependency order.
