# P1 OpenFuse Security Review Addendum — 2026-11-14

## Scope and execution constraints

- Target repository: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`.
- Upstream source: `CopilotKit/openfuse`, pinned commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`.
- Review mode: static source inspection only. No dependency installation, script execution, build, lint, typecheck, tests, browser/API/provider probing, staging, Supabase mutation/migration, or deployment.
- This addendum records only the paths and source ranges actually inspected in this increment. A partial file read is explicitly not represented as a full-file review.

## Exact source evidence and dispositions

| Upstream path | Blob SHA | Review extent | Disposition | MoreAI decision |
|---|---|---|---|---|
| `apps/server/src/auth.ts` | `a053d0e9cd9a2ca4af5a5e72a367014f487cf51e` | Full file (read returned complete source) | Reviewed | Do not transplant OpenFuse session/auth owner model. Re-express Supabase JWT verification, principal resolution, tenant scope and revocation through MoreAI FastAPI. HMAC signed-document URL pattern may be adapted only with tenant-bound object authorization, short TTL and audit. |
| `apps/server/src/engine/finance.ts` | `ff92e07452f1bce22fab99da12c32da4c4afae02` | Full file (read returned complete source) | Reviewed | Adapt bounded CSV parser/normalization only. Preserve source currency, import provenance and explicit sign convention. Never treat output as wallet balance, payment rail or immutable ledger. |
| `apps/server/src/computer-routes.ts` | `cfc9191e1e7784b6ddbf2be45bdc8cd81285c34e` | Full file (read returned complete source) | Reviewed | Route handlers delegate owner-scoped operations and validate selected payloads. Rebuild contracts behind FastAPI; derive owner from verified Supabase principal, not client input or OpenFuse middleware. Add MoreAI policy/approval and durable audit receipts. |
| `apps/server/src/computer.ts` | `e0e787ebb6d379d8d4a80e5159d1cc0a8672dd72` | Lines 1–220 only | Partial | Do not approve runtime integration from this excerpt. Initial evidence shows Docker is invoked as argv with `shell:false`, output is bounded, workspace path is constrained, and deployment identity/lease machinery exists. Full lifecycle, backend implementations, stop/timeout/race handling and Docker argument construction still require review. |
| `apps/worker/src/browser.ts` | `2f53e731f7c086a7799f767cdb036ece343a8235` | Lines 1–220 only | Partial | Do not activate worker. Initial evidence: UUID session IDs, bounded sessions/profiles, per-session serialized operations, public-URL validation before navigation and after redirects, persistent browser profile/cookies. Remaining lifecycle, cookie handling, download flow, cleanup and failure recovery need full review. |
| `apps/worker/src/server.ts` | `c3141e8e1069835cf9c315caa587aa79269a2439` | Full file (read returned complete source) | Reviewed | Worker has a single service bearer token (minimum 32 chars), unauthenticated health route, request body cap, UUID session routing and generic error sanitization. This token is not end-user or tenant authorization. Keep worker private; FastAPI must authorize each tenant/session and broker server-to-server calls. |
| `LICENSE` | `0e1238724a08528992a39ef43c63f899432a282c` | Full file (read returned complete source) | Reviewed | Upstream root MIT license. Any copied/substantial portions must retain copyright and permission notice. This root notice does not resolve nested dependency or third-party asset licensing. |

## Security and integration findings

1. **Identity boundary:** `auth.ts` persists a fixed `local-user` owner in OpenFuse's own Store and creates bearer sessions. This cannot be the MoreAI identity model. The MoreAI boundary must validate Supabase access tokens and derive user/workspace/partner scope server-side.
2. **Signed file links:** OpenFuse signs owner + path + expiry using HMAC and a 15-minute expiry. The pattern is potentially reusable, but MoreAI must additionally verify tenant ownership, object identity, allowed operation and immutable audit context. Do not use a client-supplied owner as authority.
3. **Computer execution:** the inspected prefix uses Docker CLI only, `shell:false`, bounded stdout/stderr and workspace path validation. This is not proof that the complete Docker backend is safe. Preserve the hold until full source and deployment/network isolation are reviewed.
4. **Browser worker:** the inspected server uses a global worker token, while browser profiles and cookies persist in worker storage. The worker service token must remain server-only; per-user authorization, session ownership, cookie isolation, secure deletion/retention and network egress controls must be supplied by MoreAI's orchestration boundary.
5. **Finance import:** CSV analysis is not financial account connectivity. Its positive-expense/negative-income convention and no-currency-conversion statement must remain explicit; it must never mutate MoreAI wallet/credit ledgers.
6. **No second runtime authority:** computer/browser execution remains an OpenManus Agent Runtime capability behind MoreAI policy, durable run state, approval and audit—not a separate OpenFuse autonomous agent/session authority.

## Manifest delta

This addendum is an evidence supplement, not a replacement for `docs/implementation/external-source-file-inventory.json` or the SPDX SBOM.

- Fully reviewed in this increment: 4 paths (`auth.ts`, `finance.ts`, `computer-routes.ts`, worker `server.ts`, and root `LICENSE` = 5 paths).
- Partially reviewed in this increment: 2 paths (`computer.ts` and worker `browser.ts`).
- Not reviewed here: remaining OpenFuse server/worker/integration files, all Scenario linked supporting files, Visual Skills binary and unresolved third-party asset rights, and exact-version package metadata.
- No package-license coordinate is upgraded by this addendum; all existing `NOASSERTION` statuses remain unchanged unless separate exact-version evidence is recorded.
- The existing 2,135 `pending-content-review` rows and 1,793 unresolved package@version coordinates remain open.

## P1 gate decision

**P1 remains OPEN. Do not mark P1 complete.** This increment improves evidence for selected OpenFuse security paths but does not satisfy complete OpenFuse review, Visual Skills asset rights, Scenario recursive content review, exact-version dependency licensing, or zero-pending manifest closure.

## Next dependency-ordered work

1. Finish full-file review of `computer.ts`, `computer-backend.ts`, `computer-e2b-desktop.ts`, all computer routes/tools and Docker/E2B lifecycle/configuration.
2. Traverse OpenFuse server routes, auth middleware, browser routes, OAuth, integrations, finance, worker, network/proxy/download and nested package notices until every path has a recorded disposition and review status.
3. Resolve exact-version package licensing for the remaining 1,793 unique package@version coordinates using immutable version metadata/artifacts; do not infer from latest tags.
4. Complete Visual Skills binary/banner/logo provenance and rights; keep marks deferred unless permissions are evidenced.
5. Traverse all 179 Scenario entrypoints and linked references/scripts/assets/tests/metadata/nested licenses to exact per-file dispositions.
6. Reconcile the canonical manifest to zero `pending-content-review` only after evidence exists for every row, then issue a P1 closure report.
7. After P1 closure, resume the earliest incomplete mandatory phase in `AGENTS.md`: Phase 04, then 06/07/08 and Phase 09 according to dependencies.

## Validation and release statement

No tests, builds, installs, staging, database changes, migrations, or deployments were performed, per project instruction. This report is static review evidence only.
