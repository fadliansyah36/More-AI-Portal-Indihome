# OpenFuse source governance and MoreAI capability integration

Date: 2026-11-18  
Upstream: `CopilotKit/openfuse`  
Pinned commit: `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`  
Pinned tree: `d65cf6fdbb1e58fc7d41c2925508ccc12516bd43`  
Repository tree: 251 entries = 219 blobs + 32 tree nodes; recursive tree is complete (not truncated).  
File-level inventory: `OPENFUSE-PINNED-SOURCE-FILE-MANIFEST-20261118.csv`.

## Governance and provenance

- The pinned commit resolves exactly and the complete recursive Git tree was read.
- OpenFuse has no root `AGENTS.md` at this commit. Its root `LICENSE` is MIT, copyright 2026 OpenFuse contributors; Git blob `0e1238724a08528992a39ef43c63f899432a282c`, 1,078 bytes. The recursive tree exposed no additional LICENSE/NOTICE paths. This does not automatically clear licenses of transitive dependencies, fonts, models, media or external services.
- Root dependency manifest pins pnpm 11.19.0 and requires Node >=22. Root dependencies include `@ag-ui/*` 0.0.59, `@copilotkit/runtime` 1.70.1, `@e2b/desktop` 2.4.0, `@electric-sql/pglite` ^0.3.14, `@hono/node-server` ^1.19.0, `@modelcontextprotocol/sdk` ^1.30.0, `@tanstack/ai` family, `hono` ^4.11.4, `pg` ^8.16.3 and `zod` ^4.1.0. Browser worker dependency is Playwright 1.62.1. Full lockfile and transitive license/vulnerability reconciliation remain governed by the existing P1 SBOM evidence; no dependency was installed here.
- OpenFuse describes itself as an alpha personal-agent application. Its root README, FEATURES, ROADMAP, SECURITY, COMPUTER, RICH-THREADS and TELEMETRY documents were inspected at the pin.

## File-level disposition

The CSV manifest assigns every one of the 219 blobs a source Git blob SHA, size, category, disposition and MoreAI destination.

| Source class | Files | Decision |
|---|---:|---|
| Mobile/web UI | 54 | Archive/reference only; preserve existing MoreAI customer UI |
| OpenFuse server/API/domain code | 36 | Adapt contracts only; exclude Hono/auth/store/agent authority |
| Browser worker | 22 | Adapt through existing isolated MoreAI browser supervisor |
| Computer runtime | 5 | Defer; single-owner Docker/E2B model is not a hostile multi-tenant boundary |
| Domain contracts + external backend adapter | 6 | Map to existing types; no parallel OpenBot or domain runtime |
| Tests | 57 | Reference only; no tests ported or run in this continuation |
| Docs | 10 | Reference and capability evidence |
| Build/dependency/config | 25 | Preserve provenance; do not install dependencies or replace build setup |
| Deployment infra | 1 | Adapt only through approved MoreAI infrastructure |
| Assets | 2 | Review each asset's rights before reuse |
| License | 1 | Retain upstream MIT notice |

## MoreAI integration already present

The pinned browser worker is already integrated as a separately isolated browser capability, not as an agent runtime:

- `apps/sandbox/Dockerfile.openfuse` fetches and verifies the exact OpenFuse commit, applies the MoreAI profile-delete patch and replaces the worker entrypoint/egress proxy adapter.
- `apps/sandbox/openfuse-overrides/index.ts` and `proxy.ts` keep the worker private and route HTTPS CONNECT through the MoreAI egress proxy.
- `apps/sandbox/openfuse-patches/0001-openfuse-delete-profile.patch` adds an idempotent profile-delete contract gated by the canonical session ownership reconciler.
- `apps/sandbox/app/browser_supervisor.py` authenticates to the worker, checks its actual health/session contract and fails closed when egress enforcement or ClamAV readiness is unavailable.
- `apps/sandbox/app/browser_security.py`, `browser_proxy.py`, `browser_proxy_server.py`, `browser_readiness.py` enforce allowed-domain policy, DNS/IP checks, authenticated CONNECT proxying and readiness.
- `apps/api/app/routers/browser_sessions.py`, `apps/worker` and existing `moreai_browser_*` tables remain the canonical lifecycle, owner, run, receipt, event and artifact path.
- MoreAI's five corrected browser takeover/preview SQL sources are separate forward-only source definitions and remain unapplied.

## Capability mapping and exclusions

1. **Browser / persistent Chromium / takeover / downloads** — reuse the existing OpenFuse worker implementation only behind MoreAI FastAPI, owner-scoped session records, worker token, private network, egress proxy, ClamAV scanning, action receipts and durable Agent Run lifecycle. The worker's shared bearer token is service authentication, never tenant authorization.
2. **Computer / terminal / filesystem / optional E2B desktop** — do not transplant or enable. OpenFuse's Docker computer is single-owner, shares the host kernel and has no hostile-tenant guarantee; its optional E2B desktop has outbound internet, passwordless sudo and publicly reachable VM ports. Current MoreAI code has receipt contracts but this source does not prove a tenant-isolated computer runtime. Keep capability disabled until a separate threat-modelled sandbox boundary is implemented and accepted.
3. **Agent, task worker, plan, leases, retry, checkpoint, cancellation** — map to MoreAI OpenManus plus existing durable worker and `agent_runs`, `agent_run_steps`, `agent_run_events`, `agent_run_checkpoints`, outbox and approvals. Exclude OpenFuse's agent/task authority and database.
4. **Hono API, auth, single-owner identity, PGlite/Postgres store, CopilotKit Intelligence** — exclude. FastAPI, Supabase Auth/Postgres and existing conversation/run persistence remain canonical.
5. **Chat/mobile UI, rich-thread UI, browser/computer panels** — reference only. No competing customer frontend or redesign.
6. **Gmail/Calendar and external connectors** — use MoreAI Connections Center, OAuth token lifecycle, approval and FastAPI connector adapters. OpenFuse OAuth credentials or owner store are not imported.
7. **Action receipts and approvals** — map to existing `agent_tool_approvals`, `moreai_browser_action_receipts`, `moreai_computer_action_receipts` and durable Agent Run audit. Do not create a second action ledger.

## Security and implementation status

- Browser capability source adapter is implemented; source is pinned and file-level provenance is committed.
- Browser deployment is not attested as active. No Docker service was started, no host secrets or image digests were provisioned, and no live browser call was made.
- Computer execution remains explicitly deferred and fail-closed.
- OpenFuse upstream tests were not copied or run. No build, lint, typecheck, staging, provider operation, migration apply or deployment occurred.
- OpenFuse is a capability reference, not an Agent Skill repository. It is not imported into the Skill Registry as a fake skill package.

## Skill resolver provenance hardening

At commit `625cc89855fe26679e9a2363cc4126fddf922b2f`, the worker-side resolver now independently validates source repository + exact pinned commit + entrypoint path before loading instructions. It rejects unpinned Visual/Scenario/Motion source identities, all unlisted `iart-ai/*` repositories, and the Motion repository with unresolved root license (`generative-illustration-skills`). This mirrors the API import allowlist so a malformed or privileged registry row cannot widen the runtime source trust boundary. Existing owner, install, license, publication, permission subset, SBOM file inventory, SHA-256, Git blob SHA and per-run audit checks remain in place.

This is source-level enforcement only. It does not import, publish, install, grant permission to or execute any skill package.
