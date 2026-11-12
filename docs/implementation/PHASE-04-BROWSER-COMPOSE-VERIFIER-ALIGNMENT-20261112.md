# Phase 04 — Browser Isolation Deployment Contract Alignment
Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Scope
Reconcile the duplicate browser Compose definitions and network acceptance helper so they describe the same isolated supervisor/egress-proxy topology. This is a source/configuration integration fix; it does not activate the browser runtime.

## Changes
- Updated `apps/sandbox/docker-compose.browser.yml` to match the canonical `apps/sandbox/compose.browser.yml` service names, Dockerfile, ports policy, environment contract, resource limits and networks.
- Updated `apps/sandbox/scripts/verify-browser-network-isolation.sh` to default to the canonical Compose file, use `browser-egress-proxy`, and assert the actual `browser_isolated` + `browser_egress` network topology.
- Removed stale references in the verifier to `browser_private`, `egress-proxy`, and the old compose contract.

## Commits
- Compose compatibility: `d3b02c3d16d10cbcbfe3bc5cc9b8252f80ad7b9f`
- Isolation verifier: `85073f812422aaa29f0fc144ed2f8adbeebd5283`

## Security and execution boundary
- Browser supervisor remains without a published host port and is attached only to the internal `browser_isolated` network.
- Only `browser-egress-proxy` joins the isolated and public-egress networks.
- Explicit allowlist and 32+ character service/proxy tokens remain mandatory.
- This patch does not start containers, expose a service, or enable browser tools in the worker.

## Verification
No shell scripts, Docker Compose config, containers, tests, lint, typecheck, build, staging, migration or deployment were run, in accordance with the current execution constraint. The verifier source was aligned by inspection only; no network acceptance is claimed.

## Remaining Phase 04 work
- Connect the supervisor client into the OpenManus dispatcher with fail-closed behavior.
- Validate DNS pinning/rebinding, redirect revalidation, private/reserved address rejection, and controlled downloads in the running isolated service.
- Complete workspace file CRUD and upstream Flow/server/session capability parity.

## Next phase
Continue Phase 04 integration (supervisor/dispatcher and Flow/session parity), then Phase 07 durable lifecycle, Phase 08 full agent/tool/provider parity, Phase 06 API contract closure, and Phase 09 complete Customer screen integration. Phase 10/11 remain gated.
