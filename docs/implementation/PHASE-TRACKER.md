# MoreAI Implementation Phase Tracker

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 00 | Repository baseline & UI freeze | REVALIDATED — current UI build/lint/server/browser smoke PASS | [Phase 00 run 42965739011](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739011): lint 0 errors, build/server/browser PASS at 360/390/768/1024/1440 px; 3 existing image optimization warnings |
| 01 | Upstream source pin & provenance | COMPLETE | `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` |
| 02 | Monorepo backend workspace foundation | COMPLETE — foundation | `apps/api`, `apps/worker`, `engine`, `packages` |
| 03 | Complete upstream source copy | COMPLETE — hash verified | 111/111 matching Git blob SHA in `vendor/openmanusweb/` |
| 04 | Full backend integration & security hardening | IN PROGRESS — durable approval gate + atomic consume, isolated Docker runner and per-request browser SSRF/DNS pin helper; browser route/egress interception and full upstream parity still blocked | [Phase 04 run 42975296881](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975296881): worker, sandbox, API and engine jobs PASS; browser helper is not yet a deployed browser supervisor |
| 05 | Supabase schema reconciliation | COMPLETE — additive forward-only migrations; no reset/destructive DDL | Live Supabase reports 31 migrations; approval lifecycle migration 20261111061443 and `agent_tool_approvals` verified with RLS enabled and client grants revoked |
| 06 | FastAPI core & OpenAPI contract | IN PROGRESS — Customer wallet/ledger/usage/entitlements/quotas and Partner sessions/campaigns/rewards read contracts added; remaining PRD domains/pagination/idempotency remain | Phase 04 run 42975296881 API contract PASS; live schema reused without DDL |
| 07 | Worker & durable run lifecycle | IN PROGRESS — checkpoint restoration, run-scoped transcript persistence and restart replay implemented | `WorkerRpcClient.list_checkpoints`, `SupabaseConversationMemoryStore.load_run`, durable per-tool settled observation and restart recovery tests PASS |
| 08 | LLM/tool/workflow/orchestration integration | IN PROGRESS — configured provider fallback and metered reservation/settlement implemented; only approved existing chat-completion tool active | Ordered primary/fallback candidates; stream fallback only before first delta; engine tests PASS |
| 09 | Existing Frontend API Integration | IN PROGRESS — Benefit Credit and Partner Live Sessions now consume typed FastAPI endpoints; other demo/static domains remain | [PHASE-04-06-09-FULL-INTEGRATION-CONTINUATION-20261111.md](./PHASE-04-06-09-FULL-INTEGRATION-CONTINUATION-20261111.md); Phase 00 browser/build verification pending run 42975495322 |
| 10 | End-to-end integration verification | BLOCKED | No real-provider authenticated browser → worker → provider E2E; real keys intentionally deferred |
| 11 | Integration release gate | NOT STARTED | No production worker/sandbox activation or release until full parity and acceptance evidence |

## Direct-main execution policy

Implementation is being performed directly on `main` as explicitly requested by the product owner. No new branch is created and the existing historical Phase 04 branch/PR is not used as the work target. Changes are committed in small, reviewable commits; production deployment and worker activation remain prohibited until Phase 11 passes.

## Current Phase 04 next work

1. Implement worker approval pause/resume and atomic single-use consumption; the approval migration/API is only a persisted request/decision contract and is not yet connected to the worker.
2. Integrate the sandbox supervisor with the OpenManus dispatcher. Keep Bash/Python/browser/file tools unavailable until the approval and supervisor gates are actually wired.
3. Implement browser isolation, DNS pinning/rebinding defenses, redirect revalidation, private/reserved IP rejection, controlled downloads and isolated file workspace.
4. Close the source-to-target behavioral parity gaps in `openmanus-backend-capability-map.json`, including agent/flow lifecycle, tool schemas/handlers and upstream server/session/stream functions.
5. Maintain durable recovery, idempotency and tenant boundaries. The current user instruction for this continuation is to skip tests; therefore no new pass evidence is claimed.

## 2026-11-11 frontend route, auth and workflow integration continuation

- Root cause of the Workflow route issue: the product used a single client-side tab state with no direct Next.js route aliases for Workflow/Login/Register/Partner Login. Direct route entry had no durable mapping to the corresponding screen.
- Added route entry points `/workflow`, `/workflow-progress`, `/login`, `/register`, and `/partner/login`, all forwarding into the existing main UI (no second frontend).
- Main navigation now updates browser history and restores the active screen from direct links/history. Supabase Auth session restoration and auth-state changes protect the workspace; unauthenticated visits to protected screens return to Login.
- Customer Login/Register continue to use Supabase Auth. Password recovery now invokes `resetPasswordForEmail` instead of displaying a fabricated success toast.
- Partner Login no longer accepts hardcoded demo credentials or shows fake success. It signs in through Supabase Auth and calls the server-side Partner tenant discovery endpoint. Access is granted in the UI only when an active Partner membership is returned. Partner applicant metadata does not grant authorization; tenant membership remains server-controlled.
- WorkflowProgressView now reads persisted Customer Agent Runs from `GET /api/v1/customer/agent-runs`. The Tasks view now uses actual agent-run history instead of seeded tasks and no longer locally toggles completion. Artifact-result view now reads real artifact metadata from `GET /api/v1/artifacts`; file download is not claimed because a signed-download endpoint is not yet implemented.
- Agent Studio now reads `GET /api/v1/agents`, hides disabled agents, and passes the selected supported agent key (Manus/Planning) into the Customer Chat request. The home greeting reads `GET /api/v1/me` and the fabricated “Partner ISP 100M” badge was removed.
- API boundary remains: browser Supabase access is Auth-only; business data/actions are routed through the typed FastAPI client; Customer and Partner data APIs remain server-side role/tenant checked.
- No tests, lint, build, screenshots, SQL apply, or runtime checks were run in this continuation, per explicit instruction. UI changes therefore have no new regression evidence. Do not treat this increment as phase acceptance.

Remaining Phase 09 work includes real APIs for all Wi-Fi, captive portal, voucher, credit/ledger, analytics, education, notification, account/profile mutation and Partner operations screens. These must not be populated with fabricated fallback data. Phase 04, 06–08, 10 and 11 remain open.

Latest direct-main commits:
- `13f7353d1ed6252f1313f3d47a6ede159b7ed0b3` — hardened tool-call runtime and agent lifecycle.
- `2eda22e07efc38398080dba2c512eb5cef167bf0` — explicit cancelled/exhausted states.
- `11e724242c69d76b152fca7d96441e5ede2d2759` — tool-call runtime tests.
- `59acb70953c6cb6ca5e35cb641e403e4a41248f3` — pinned engine test dependencies.
- `e2eb64c147f2f4a8d5ad92d152c20a4d76e5b6ca` — Phase 04 engine tests in CI.

These commits are implementation increments, not Phase 04 acceptance. CI must pass and remaining integration gaps must be closed before this phase can be signed off.


## 2026-11-11 earlier baseline and schema notes (historical snapshot)

- The earlier memory-schema reconciliation confirmed `conversation_messages.token_input` and `token_output` are NOT NULL; the worker memory insert supplies zero usage values for non-metered memory rows.
- The earlier Files-view lint issue was fixed in the preceding baseline work. The current baseline is now green on run 42965739011; see the latest direct-main continuation below.
- The original note that Customer/Partner separation had not started was true only at that earlier checkpoint. It has since been implemented and verified by the later Phase 04/API CI runs.


## 2026-11-11 initial durable OpenManus tool-call increment (historical snapshot)

- Added `engine/agents/durable_tool_runtime.py`: bounded OpenManus tool-call loop, structured function arguments, deterministic per-round request keys, and durable round/tool intent/settlement checkpoints.
- Worker registry registered this runtime as the Manus implementation; existing worker lease/heartbeat/cancel/checkpoint/finish lifecycle remains the execution owner.
- OpenAI-compatible provider adapter accepts tool definitions and returns structured tool calls; metered gateway includes tool definitions in request hashing and sends them to the provider.
- At that checkpoint only `create_chat_completion` was registered. High-risk Bash/Python/browser/editor/process tools remained default-denied.
- The subsequent direct-main continuation below has since added checkpoint/transcript recovery, provider fallback, server-side Customer/Partner isolation, and the approval-gated isolated sandbox adapter. Real provider/API-key E2E and production sandbox activation remain deferred behind their respective gates.


## 2026-11-11 direct-main continuation — durable recovery, tenant isolation and provider failover

- Current implementation report: [PHASE-04-07-08-09-DURABLE-RECOVERY-TENANT-FAILOVER-20261111.md](./PHASE-04-07-08-09-DURABLE-RECOVERY-TENANT-FAILOVER-20261111.md).
- Durable worker restores `agent_run_checkpoints`, restores run-scoped conversation messages, resumes pending tool calls, reuses settled observations, and returns a checkpointed final output after restart.
- Worker process shutdown now leaves an interrupted lease recoverable; explicit user cancellation remains terminal.
- Customer and Partner API groups are separated. Active Partner membership resolves tenant and role on the server. Existing generic conversations, runs and artifacts routes are Customer-principal gated.
- Customer Chat and Partner Portal now use typed API clients. Partner tenant selection is constrained to active server-authorized memberships. Unsupported QR, package, analytics and onboarding actions are not simulated.
- Provider primary/fallback routes share one maximum-estimate reservation and settle against the selected provider. Streaming failover is allowed only before any delta is emitted.
- Python/Bash isolated Docker adapter and hardened runner are implemented, but production registration remains disabled until the approval/audit contract and deployed supervisor pass the AGENTS.md gate.
- Phase 04 CI run 42965739026: sandbox 7/7, engine 26/26, worker 15/15, API 16/16 — all green.
- Phase 00 run 42965739011: all baseline gates passed — lint 0 errors, build/server/browser smoke passed at 360/390/768/1024/1440; three non-blocking image optimization warnings remain.
- Real provider keys, authenticated production E2E and deployment remain deferred. Phases 04 and 06–09 remain in progress; Phase 10 blocked; Phase 11 not started.


### Latest direct-main commits for this increment

- `895253b7176f25ef76f1f0852376612f25c05d0d` — Partner tenant route authentication regression test.
- `2b28f2cd4ff9742be0cee2d9ce7c6f057ca21f32` — retain LLM reservation when streaming provider usage has been received.
- `d81eb1566f17fc90b598e5106bacdebe22700aab` — SSE checkpoint redaction regression test.
- `b3d7a827056c16ae1260acfbab7d9970fe7f51f3` — redact private tool arguments and observations from run events.
- `27253b21d6503bf33b74ae4bb47cc5805acdf80a` — partner portal API data binding and tenant selection.
- `9feb542cf3fc50320093266fb737110706a3d130` — server-authorized Partner tenant discovery route.
- `c4f649c83614824fec75b0097cd618d47ff1c4f4` — Customer Chat moved to dedicated Customer API.


## 2026-11-11 continuation — approval persistence contract (no tests run)

- Product-owner instruction for this increment: do not run real or other tests. This is recorded as an execution constraint, not a passing verification result.
- Added forward-only migration draft `20261111050000_moreai_tool_approval_lifecycle.sql`: owner/run/tool/argument-hash scoped approval records, expiry, single-use consumption, server-only RPCs and RLS with no direct anon/authenticated table access.
- Added `apps/api/app/routers/tool_approvals.py` with Customer-principal scoped list/request/decision endpoints; registered the router in FastAPI.
- Added typed `customerToolApprovalApi` contracts to `lib/api/client.ts`.
- Updated `openmanus-backend-capability-map.json` to reflect the actual partial state.
- Important: approval persistence and API contracts are authored but the worker does not yet create/pause/resume on pending approval or atomically consume approvals at dispatch. The sandbox tools remain disabled. Migration has not been applied to Supabase.
- No local checkout was available in the execution environment (GitHub clone DNS resolution failed); code writes were made through the GitHub connector directly on `main`. No build, lint, unit, integration, E2E, SQL apply or runtime checks were run.
- Next: implement approval pause/resume + worker atomic consume, then isolated browser supervisor with DNS pinning/redirect checks, and sandbox file workspace. Continue Phase 06–09 only with real backend contracts for every existing UI domain; do not convert unsupported data into static fallbacks.

## 2026-11-11 continuation — public entry, role routing and API-origin separation

- Root `/` now resolves to the existing Splash screen. `/splash` and `/onboarding` are explicit public routes; the Splash CTA continues to onboarding and then authentication.
- Added `/customer`, `/customer/login`, `/customer/register`, `/partner`, `/partner/login` route entries. Existing UI components are reused; no second frontend shell or visual redesign was introduced.
- Customer and Partner workspaces remain isolated by server-side FastAPI route groups: `/api/v1/customer/*` and `/api/v1/partner/*`. Optional independent browser API origins are supported through `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` and `NEXT_PUBLIC_MOREAI_PARTNER_API_URL`, falling back to `NEXT_PUBLIC_MOREAI_API_URL` when not set.
- FastAPI now supports an explicit `MOREAI_CORS_ALLOWED_ORIGINS` allowlist for deployments that configure separate role API origins. Same-origin deployments need no CORS allowlist.
- Unauthenticated Customer workspace routes redirect to Customer Login; Partner workspace routes redirect to Partner Login. Root is public only for Splash/onboarding/auth views; `/?view=partner` and other workspace tabs remain protected.
- Route/API commits on `main`: `2853a16`, `edcfd5f`, `ce23114`, `2fcdeee`, `1993d42`, `1345174`, `603a834`, `ee03225`, `661726d`, `9ee6d0e`, `ec4d599`, `1aff40a`, `46308b7`, `dd1e880`, `0049933`.
- No tests, lint, typecheck, build, browser smoke, screenshots, Supabase migration or deployment were run in this increment. These commits are not Phase 09 acceptance evidence. Vercel project inspection is pending team authorization; no deployment was triggered.
- Phase 04 and 06–08 remain open; this increment does not wire worker approval pause/resume, sandbox/browser isolation, durable lease fencing, or full upstream parity. Phase 09 remains open for all remaining Wi-Fi, captive portal, voucher/credit/ledger, analytics, EduTech, notifications, profile/security and Partner operational domain endpoints. Phase 10 remains BLOCKED; Phase 11 remains NOT STARTED.

## 2026-11-11 continuation — worker approval gate and sandbox boundary hardening

- `WorkerRpcClient.wait_for_tool_approval` now requests an owner/run/tool/argument-hash scoped approval, polls the durable decision while maintaining the worker lease, propagates cancellation, and calls `moreai_consume_tool_approval` for atomic single-use consumption before execution.
- `moreai_request_tool_approval` now reuses an unexpired `approved` record as well as a pending record. This preserves an approved decision if the worker restarts before consuming it. The approval table migration `moreai_tool_approval_lifecycle` was applied to canonical Supabase project `uunfgimtokhucegqbpce`; `agent_tool_approvals` is present with RLS enabled and migration history records version `20261111061443`.
- The tool registry enforces the approval callback centrally before dispatch for any policy decision requiring approval. The durable Manus runtime advertises Bash/Python only when the sandbox adapter is present.
- Bash/Python adapter registration requires both `MOREAI_SANDBOX_ENABLED=true` and `MOREAI_SANDBOX_RELEASE_GATE_PASSED=true`, plus a digest-pinned `MOREAI_SANDBOX_IMAGE`. Both flags remain `false` in `.env.example`; production activation is not enabled.
- Docker runner now streams source over stdin into the isolated container instead of bind-mounting a host source file. It retains no network, read-only root, non-root UID, dropped capabilities, no-new-privileges, seccomp, PID/CPU/memory/output/time limits and ephemeral `/tmp`.
- Important remaining Phase 04 gates: this is a Docker runner adapter, not proof of a deployed sandbox supervisor; browser network interception with DNS pinning/rebinding resistance, redirect-by-redirect enforcement, download scanning, isolated file workspace, and full upstream agent/flow/tool/server parity remain open. Browser tool is not registered.
- No tests, lint, typecheck, build, browser smoke, threat-model tests, Docker execution, SQL apply or deployment were run. The earlier Phase 04 CI run is historical and does not verify this increment. Approval runtime now has the required schema and Customer Workflow UI controls, but worker/Docker runtime behavior has not been executed or verified.
- Relevant direct-main commits include `2189d45`, `fb0452b`, `f29638c`, `5212fa2`, `ebaa323`, `ce21605`, `8a1c9e8`, `dd11b09`, `95179b9`, `cfae287`, `396fa56`, `84ab207`, `debecee`.
- Phases 04 and 06–09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.

## Vercel production routing fix — 2026-11-11

- Vercel team authorization is active; project `more-ai-portal-indihome` is linked to the canonical GitHub repository.
- Production deploy `dpl_37tWK4zTmehTz8FZmQLwicmir6K8` is READY at code commit `3219109f047f1a58a411970fc1c6071b06debb03`.
- Runtime set to Node.js 24.x. Added the canonical Supabase URL and browser publishable key to Production/Preview/Development. No service-role key was added.
- Root Auth initialization fallback fixed to preserve Splash/Onboarding and redirect protected routes to the appropriate Customer/Partner login.
- Vercel build compiled, TypeScript validation completed, and 17/17 static pages generated. Vercel HTTP fetch returned 200 for `/`, `/splash`, `/onboarding`, `/customer/login`, `/customer/register`, `/partner/login`, and `/workflow`.
- Latest one-hour runtime error scan found no errors. No interactive authenticated browser E2E was performed.
- **Important:** `NEXT_PUBLIC_MOREAI_API_URL` and role-specific API origins remain unset because no deployed FastAPI public origin is currently configured in Vercel. The Next.js project does not expose the FastAPI `/api/v1/*` endpoints. Thus route shell deployment is complete, but production workflow data/approval integration remains blocked on FastAPI hosting/origin configuration.
- Detailed evidence: `docs/implementation/VERCEL-DEPLOYMENT-ROUTING-FIX-20261111.md`.


## 2026-11-11 continuation — public/auth navigation isolation and production verification

- Report: [PUBLIC-AUTH-NAV-ISOLATION-OPENMANUS-STATUS-20261111.md](./PUBLIC-AUTH-NAV-ISOLATION-OPENMANUS-STATUS-20261111.md).
- Public/auth entry screens no longer render the private fixed Bottom Navigation Dock; public-page bottom spacing no longer reserves dock space.
- Removed global Customer ↔ Partner mode switching from header/dock. Removed gallery and cross-domain drawer header triggers. MoreAI brand navigation now returns to the active role's own home.
- Files: `app/page.tsx`, `components/navigation/app-navbar.tsx`.
- Phase 00 CI run [42973885825](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42973885825): SUCCESS — lint, build, browser smoke/responsive screenshot job, worker tests and API tests passed. Screenshot evidence artifact id `13834487651`.
- Vercel production deployment `dpl_4kCc46R8WeYE1eQtbuvNV177AUcN` for commit `aecd134544eecb7c9a361c14ca067bb546bddeb2`: READY. HTTP 200 verified for root, onboarding, customer register and login routes.
- This is a navigation-isolation increment only. No authenticated signup/login or Partner membership E2E was run. Existing OpenManus/FastAPI wiring remains partial; `NEXT_PUBLIC_MOREAI_API_URL` and role-specific origins remain unset because the actual public FastAPI URL is not known/configured. Full frontend → FastAPI → OpenManus worker → Supabase integration is not verified.
- Phase 04 and 06–09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED. Next: configure the confirmed FastAPI public origin, then verify API health/OpenAPI/JWT/CORS and continue remaining backend parity/domain contracts before E2E acceptance.


## 2026-11-11 continuation — sandbox SSRF hardening and Customer/Partner API/UI binding

- Full report: [PHASE-04-06-09-FULL-INTEGRATION-CONTINUATION-20261111.md](./PHASE-04-06-09-FULL-INTEGRATION-CONTINUATION-20261111.md).
- Browser per-request guard now supports allowlisted HTTPS/443 requests, redirect-chain checks, public-IP validation and conservative per-host DNS pin/rebinding detection. It is a policy helper, not an integrated browser network interceptor or deployed browser supervisor; browser remains disabled.
- Updated sandbox and engine tests to align with current dispatcher/approval/Docker no-host-mount behavior.
- Phase 04 run [42975296881](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975296881) SUCCESS across worker, sandbox, API and engine contract jobs.
- Added Customer wallet, ledger, usage, entitlement and quota APIs; Partner active sessions, campaigns and reward-catalog APIs. All use existing live Supabase schema and server-side owner/tenant/location filtering; no migration was needed.
- Extended typed API client and connected Benefit Credit + Partner Live Sessions views to live API data; removed seeded wallet/history/guest data and simulated balance/disconnect actions.
- Latest Phase 00 build/lint/browser regression for commit `db423d6` is pending run [42975495322](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975495322). No pass claim until completed.
- Phase 04/06/07/08/09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED. Production deploy/worker activation remain prohibited until release gates pass. FastAPI public origin remains unconfigured in Vercel.


## 2026-11-11 Super Admin and durable runtime packaging continuation

- Added platform role authorization derived from active platform-scoped user_role_assignments and roles table. No user_metadata/client role is trusted.
- Added read-only Super Admin API: context, overview, partner organizations, agent runs and audit logs. All endpoints require Supabase bearer authentication plus an allowed platform role; response fields avoid prompts, outputs and network PII.
- Added dedicated /admin route and Super Admin Control Center. It reads live FastAPI/Supabase data and exposes read-only views; Customer and Partner product routes remain unchanged.
- Added authorization and unauthenticated route tests; Phase 04 CI run 42981030933 SUCCESS (worker-contract, engine-policy, API-contract, sandbox-policy).
- FastAPI /ready now performs live Supabase Auth/PostgREST reachability probes when configured. Phase 00 run 42981030866 was pending; no new frontend build/browser regression evidence is claimed yet.
- Added separate FastAPI and durable worker Dockerfiles plus docker-compose.runtime.yml. Worker is an opt-in long-running container profile; worker execution and sandbox remain fail-closed. This is packaging only, not cloud deployment or runtime proof.
- Deployment quota is intentionally deferred by product owner. No Vercel deployment was attempted.
- Service-role secret has not been supplied to the runtime. API /ready remains degraded until SUPABASE_SERVICE_ROLE_KEY is configured. No LLM provider key or paid provider call used.
- Phase 04, 06–09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED. See FULL-ECOSYSTEM-INTEGRATION-CONTINUATION-20261111.md for exact implementation and remaining blockers.
