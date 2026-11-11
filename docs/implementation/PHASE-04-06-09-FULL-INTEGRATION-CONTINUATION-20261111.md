# MoreAI Phase 04 / 06–09 Integration Continuation — 2026-11-11

## Execution target
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main` (direct-main policy; no new branch)
- Canonical Supabase: `uunfgimtokhucegqbpce`
- Upstream: `YunQiAI/OpenManusWeb` pinned at `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`
- Product UI preserved; no upstream UI was introduced.

## Changes implemented

### Phase 04 — sandbox and approval boundary
- Added `BrowserRequestGuard` in `apps/sandbox/app/browser_security.py` for per-request URL validation, HTTPS/port/domain allowlisting, public-IP checks, redirect-chain revalidation and conservative per-host DNS pinning to detect changed DNS answers within a browser session.
- Added an injectable resolver for deterministic DNS rebinding tests.
- Browser guard is a reusable security boundary only. It is **not yet connected to an actual Playwright/Chromium route interception layer or egress proxy**, so it does not by itself stop a browser from making requests outside the guard. Browser tool remains unavailable/default-deny.
- Docker runner remains digest-pinned, stdin-fed, no host bind mounts, no network, read-only root, non-root UID, dropped capabilities, no-new-privileges, seccomp, PID/CPU/memory/time/output limits and ephemeral tmpfs.
- Reconciled stale tests with current implementation: centralized approval gate is enforced by `PolicyEnforcedToolRegistry`; Docker runner tests now assert no host bind mount and provide stdin behavior.
- High-risk tool policy tests now reflect the intended pending-approval state: tool definition may be advertised only when enabled, but dispatcher must obtain an approval callback and reject execution if the callback is absent or does not consume approval.
- Approval migration `20261111050000_moreai_tool_approval_lifecycle` is confirmed in live Supabase migration history as version `20261111061443`; table `agent_tool_approvals` exists with RLS enabled. Security advisor reports RLS enabled with no policies for this table; this is intentional server-only deny (no anon/authenticated table grants), but remains an advisor finding to document/resolve explicitly with a deny policy if required by the release policy.

### Phase 06 — FastAPI contracts
Added authenticated, customer-principal scoped read contracts:
- `GET /api/v1/customer/wallet`
- `GET /api/v1/customer/wallet/ledger` (bounded limit and timestamp cursor)
- `GET /api/v1/customer/usage` (bounded limit and timestamp cursor)
- `GET /api/v1/customer/entitlements` (active/current server-resolved entitlements)
- `GET /api/v1/customer/quotas` (user-scoped quota policy and usage)
Added authenticated, partner tenant/location scoped read contracts:
- `GET /api/v1/partner/sessions` (returns only non-PII network session metadata; no user ID/IP/device claims)
- `GET /api/v1/partner/campaigns`
- `GET /api/v1/partner/campaigns/{campaign_id}/rewards` (verifies campaign ownership and location scope before returning reward metadata)
- No DDL was needed; routes reuse verified live Supabase tables and explicit server-side ownership/tenant filters.

### Phase 09 — existing frontend integration
- Extended `lib/api/client.ts` with typed Customer wallet, ledger, usage, entitlement and quota contracts, plus Partner session, campaign and campaign-reward calls.
- `components/views/benefit-credit-view.tsx` now reads wallet balance, entitlements, quota, usage and ledger from FastAPI. Removed hardcoded 8,500/100,000 balances, seeded history and simulated top-up/benefit activation. When APIs return no records, it renders empty state; top-up no longer mutates a local balance and explicitly reports the payment backend is not available.
- `components/views/partner-live-sessions-view.tsx` now reads active sessions and tenant context from Partner API. Removed fabricated guest/device/IP/bandwidth/session values and local fake disconnect behavior. It only renders fields that exist in the live schema/API.
- These are justified UI-file changes to replace demo values/actions with real API reads while retaining the existing MoreAI component styling and page structure. A production screenshot/browser comparison for these specific authenticated screens is still pending.

## Commits
- `a66c98e0d55989195432763c52bda30ca8643b6c` — browser per-request guard
- `2e919991665e3a6f67a399c3d6ab7f5fee5ef575` — deterministic DNS resolver injection
- `082d79a3243ad9c04185f0792f355bec1f9a7303` — sandbox security test fixes
- `8c5f648d0a0d071d6fc1191a993b39adac606758` — engine policy test alignment
- `2af97a5c286b4a5afef5e2588518e699095707bd` — Customer wallet/usage/entitlement/quota APIs
- `bc86383dcac41eec230ad7dc9556351ce86ccc79` — Partner sessions/campaign/reward APIs
- `6b1a35d5fd9b68772dd254b257757d94a717baa8` — typed frontend API client
- `e14332f9bbd5c3a822f7baed4535489fedda254f` — unauthenticated domain-route regression tests
- `e20d6b26a4b5f7d1284bd35c11a4d639ec1a00be` — Benefit Credit UI live API binding
- `126bc7cf5bf9c39b3a68f0fd3ad90c568c179979` — unused import cleanup
- `db423d62e63b14de564ee353d9ccd57ce28b593e` — Partner Live Sessions UI live API binding

## Verification evidence
- Phase 04 security/API/worker/engine CI run [42975296881](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975296881): SUCCESS — `worker-contract`, `sandbox-policy`, `api-contract`, and `engine-policy` all passed.
- Earlier engine and sandbox checks also passed at [42975028221](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975028221) and [42975028258](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975028258).
- Phase 00 build/lint/browser regression for the latest UI/API commit `db423d62` is pending at [42975495322](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975495322); no pass is claimed yet.
- Live Supabase migration inventory confirms `20261111061443_moreai_tool_approval_lifecycle`; live table inventory confirms `agent_tool_approvals` with RLS enabled. Security advisor still reports 5 RLS-enabled/no-policy tables (including `agent_tool_approvals`) and leaked-password protection disabled.
- No LLM/provider keys were used. No paid provider call, real provider E2E, authenticated production browser E2E, worker runtime activation, Docker runtime execution or production deployment was performed.

## Remaining gates and blockers
- Phase 04 remains IN PROGRESS: browser route/subresource interception and DNS pin enforcement at the actual socket/egress layer; redirect/download scanner service; isolated file workspace; process/worker supervisor deployment; remaining upstream ReAct/SWE/flow/session/log-monitor/server parity.
- Phase 06 remains IN PROGRESS: remaining PRD endpoint map (profile mutations/session management, files signed URLs, subscriptions/payment/webhooks, network verification/session lifecycle, admin APIs, full Partner operations, notifications/analytics/EduTech) and full pagination/idempotency contracts.
- Phase 07 remains IN PROGRESS: worker/outbox event publisher, durable event delivery/replay completeness, artifact storage adapter and production worker deployment/health.
- Phase 08 remains IN PROGRESS: remaining upstream tool adapters (search, file/editor, terminate, browser, Bash/Python), provider retry/circuit-breaker/tool-call streaming parity and runtime routing/entitlement configuration. Production worker remains fail-closed.
- Phase 09 remains IN PROGRESS: other static/demo screens remain, including Wi-Fi/session management, Partner vouchers/operations, profile/security settings and several dashboard metrics. They must be connected to existing real domain APIs or clearly show unavailable/empty state; no simulated action should remain.
- Production Vercel still has no confirmed public FastAPI origin in `NEXT_PUBLIC_MOREAI_API_URL` (or role-specific API origins). Do not point these at the frontend hostname or invent a backend URL.
- Phase 10 remains BLOCKED until an actual deployed FastAPI + worker + sandbox + Supabase path can be tested with an authenticated account. Provider-key tests are intentionally excluded per product-owner constraint.
- Phase 11 remains NOT STARTED. Do not deploy production or enable worker/sandbox flags before all release gates and evidence pass.

## Next execution order
1. Complete browser supervisor and egress interception with a deployed, isolated browser runtime; keep browser disabled until SSRF/rebinding/redirect/subresource/download tests pass.
2. Complete remaining OpenManus backend parity and safe tool adapters; prove checkpoint/recovery/approval/atomic consumption end-to-end.
3. Complete remaining FastAPI PRD domains and typed client methods, then bind every existing static screen to these APIs.
4. Obtain/confirm actual FastAPI deployment origin and deploy API/worker/sandbox with fail-closed settings; configure Vercel origins and CORS.
5. Run authenticated no-provider E2E for Auth → FastAPI → worker → Supabase → SSE/UI, tenant isolation, cancellation, retry, idempotency, artifacts and quota/ledger; then complete Phase 10/11 evidence.
