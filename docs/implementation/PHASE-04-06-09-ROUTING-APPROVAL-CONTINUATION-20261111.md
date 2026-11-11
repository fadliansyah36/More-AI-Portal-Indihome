# MoreAI Phase 04 / 06–09 — Routing, Role APIs & Approval Lifecycle Continuation

Date: 2026-11-11  
Repository: fadliansyah36/More-AI-Portal-Indihome  
Branch: main (direct commits only)  
Baseline: 1cdd4358b9465c67234c0a28037d9018f85513a7  
Target: 705775e2d9fd65c7efd5911e3190e31d12f938b3

## Scope completed in this increment

### 1. Public entry and direct role routes

- Root `/` now opens the existing MoreAI Splash screen by default.
- `/splash` and `/onboarding` render the same existing app component at their own direct URL.
- Added direct Customer paths: `/customer`, `/customer/login`, `/customer/register`.
- Added direct Partner paths: `/partner`, `/partner/login`.
- Workflow paths `/workflow` and `/workflow-progress`, plus legacy `/login` and `/register`, render the shared MoreAI app rather than redirecting to a query route.
- The app navigation now pushes explicit Customer/Partner paths. Root `/` still supports `?view=...` for legacy internal navigation and only defaults to Splash when no view query exists.
- Public entry/auth views do not render the workspace navbar. Unauthenticated Customer workspace routes resolve to Customer Login; Partner routes resolve to Partner Login.
- Existing Splash → Onboarding → Login → Register journey is retained. Customer Login/Register remain Supabase Auth flows; Partner Login still requires active server-authorized Partner membership.

### 2. Role-specific API origins

- `lib/api/client.ts` now supports:
  - `NEXT_PUBLIC_MOREAI_API_URL` — shared FastAPI origin/fallback.
  - `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` — optional Customer API origin.
  - `NEXT_PUBLIC_MOREAI_PARTNER_API_URL` — optional Partner API origin.
- Customer calls use `/api/v1/customer/*`; Partner calls use `/api/v1/partner/*`. Both default to the same FastAPI origin when role-specific origins are not configured; authorization remains server-side and tenant-scoped.
- FastAPI supports exact CORS allowlisting through server-only `MOREAI_CORS_ALLOWED_ORIGINS` when the two role APIs use different origins.
- `.env.example` and `apps/api/README.md` document these settings. No service-role, provider or worker secret was added to browser variables.

### 3. Worker approval pause/resume and single-use consumption

- `WorkerRpcClient.wait_for_tool_approval` creates/reuses an owner + run + tool + canonical-argument-hash scoped approval request.
- The worker polls the persisted decision while maintaining its lease, detects run cancellation/lease loss, and calls `moreai_consume_tool_approval` before execution.
- The SQL request RPC reuses a still-valid approved record, so a worker restart between approval and consumption does not discard the user's decision.
- `PolicyEnforcedToolRegistry` enforces the approval gate centrally before invoking any handler whose policy requires approval.
- The durable Manus runtime exposes Bash/Python definitions only when the sandbox adapter is registered.
- Customer Workflow view now lists pending approvals and offers owner-scoped Approve / Deny controls through the typed API client.
- Approval persistence is no longer just a draft: migration `moreai_tool_approval_lifecycle` was applied to canonical Supabase project `uunfgimtokhucegqbpce`. The table exists with RLS enabled and migration history records version `20261111061443`.

### 4. Sandbox boundary improvement

- Docker execution source is streamed over stdin; the previous host filesystem bind mount has been removed.
- Existing restrictions remain: digest-pinned image, non-root UID, read-only root, no network, dropped capabilities, no-new-privileges, seccomp, PID/CPU/memory/output/time limits and ephemeral `/tmp`.
- Registration requires both `MOREAI_SANDBOX_ENABLED=true` and `MOREAI_SANDBOX_RELEASE_GATE_PASSED=true`, plus a digest-pinned `MOREAI_SANDBOX_IMAGE`. The two enablement flags remain false in `.env.example`.
- Bash/Python execution is therefore not activated in production by this commit. No browser tool is registered.

## Supabase schema result

- Confirmed canonical project ref: `uunfgimtokhucegqbpce`, status ACTIVE_HEALTHY, PostgreSQL 17.
- Before applying the migration, inspected public tables and migration history. `agent_runs` exists; `agent_tool_approvals` did not exist; existing public tables have RLS enabled.
- Applied additive approval lifecycle migration. No reset, truncate, destructive DDL or existing table recreation was performed.
- Post-apply catalog inspection confirmed `public.agent_tool_approvals` exists with RLS enabled; migration history contains `moreai_tool_approval_lifecycle` at version `20261111061443`.
- The actual worker-to-Supabase RPC execution has not been runtime-tested.

## Commits on main

- `2853a16` — Splash default and role route resolution.
- `edcfd5f`, `ce23114`, `2fcdeee`, `1993d42`, `1345174`, `603a834` — direct route entries.
- `ee03225` — Customer/Partner API origin separation.
- `1aff40a` — explicit FastAPI CORS allowlist.
- `0049933`, `9ee6d0e`, `0256108` — auth boundary and navigation routing fixes.
- `e5a6f36`, `c4dc58d`, `153639b`, `367f406`, `afd8b2a`, `07bc8e2`, `a023173`, `7889f9d`, `3a63070`, `4f31b80`, `5ebe1b7` — shared app rendered at direct route paths.
- `debecee` — remove host bind mount from Docker runner.
- `2189d45`, `fb0452b`, `f29638c`, `5212fa2`, `ebaa323`, `ce21605`, `8a1c9e8`, `dd11b09`, `95179b9`, `cfae287`, `396fa56` — approval worker/dispatcher/sandbox wiring.
- `175f4e7` — Customer Workflow approval controls.
- `a217439`, `705775e` — phase/parity documentation.

## Explicit remaining work — not marked complete

### Phase 04
- Browser isolation is not complete: DNS pinning at the network interception layer, rebinding resistance, per-redirect and subresource revalidation, tenant domain allowlists and safe download scanning remain.
- Isolated file workspace, file read/write/edit tools and artifact lifecycle remain.
- The Docker runner is not a deployed sandbox supervisor. Threat-model, escape, SSRF, tenant-boundary and artifact-scan gates have not passed.
- Remaining OpenManus agent, flow, workflow, tool and upstream server/session/stream parity remains partial.

### Phase 06
- Full domain API contracts and complete OpenAPI parity remain incomplete. Existing API modules cover identity, Customer conversations/runs/events/approvals, Partner tenants/context/locations/members, catalog and artifact metadata only.

### Phase 07
- Durable recovery/checkpoints exist, but full lease fencing tokens across claim/heartbeat/checkpoint/finish, concurrency proof, stale-worker fencing and all retry/recovery edge cases remain open.

### Phase 08
- Full upstream provider/model, agent, flow, planner, workflow, tool and orchestration parity remains incomplete. Only the currently integrated subset is registered; other tools remain unavailable or default-deny.

### Phase 09
- Still requires real APIs and UI integration for Wi-Fi Management; captive portal and OTP; vouchers, wallet/credits/ledger; analytics; EduTech; notifications; profile and security settings; Partner locations, staff, gateways, vouchers, sessions and analytics.
- No static/demo business values or simulated success may be reintroduced to fill these gaps.

### Phase 10–11
- Phase 10 remains BLOCKED; Phase 11 remains NOT STARTED. No release or deployment is authorized until their evidence gates pass.

## Verification and deployment

- Per the existing product-owner constraint to defer tests/live LLM calls, no unit/integration/E2E tests, lint, typecheck, build, browser smoke, screenshot regression, Docker execution or live provider calls were run.
- Supabase migration application and catalog/migration-history verification were performed; this is schema verification, not worker runtime proof.
- Vercel project inspection/deployment was not performed. The connected Vercel account's team scope returned 403 and generated a one-time team authorization link; owner approval is still required. No deployment was triggered.
- No Phase 04, 06, 07, 08 or 09 phase acceptance is claimed by this report.
