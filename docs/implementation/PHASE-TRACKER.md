# MoreAI Implementation Phase Tracker

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 00 | Repository baseline & UI freeze | REVALIDATED — current UI build/lint/server/browser smoke PASS | [Phase 00 run 42965739011](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739011): lint 0 errors, build/server/browser PASS at 360/390/768/1024/1440 px; 3 existing image optimization warnings |
| 01 | Upstream source pin & provenance | COMPLETE | `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` |
| 02 | Monorepo backend workspace foundation | COMPLETE — foundation | `apps/api`, `apps/worker`, `engine`, `packages` |
| 03 | Complete upstream source copy | COMPLETE — hash verified | 111/111 matching Git blob SHA in `vendor/openmanusweb/` |
| 04 | Full backend integration & security hardening | IN PROGRESS — durable recovery and approval persistence/API authored; worker approval pause/resume, sandbox supervisor, browser SSRF/DNS rebinding, file isolation and upstream behavioral parity remain | [Phase 04 run 42965739026](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739026): sandbox 7, engine 26, worker 15, API 16 tests all PASS |
| 05 | Supabase schema reconciliation | COMPLETE — existing schema only; no reset/destructive DDL | Live columns verified for checkpoints, conversation messages, partner membership, organizations and locations; no migration needed |
| 06 | FastAPI core & OpenAPI contract | IN PROGRESS — Customer/Partner route groups plus Customer tool-approval list/request/decision routes; full domain contracts and OpenAPI parity remain | Customer context/conversation/run/SSE; Partner tenants/context/locations/members; legacy customer routes protected; API contract tests PASS |
| 07 | Worker & durable run lifecycle | IN PROGRESS — checkpoint restoration, run-scoped transcript persistence and restart replay implemented | `WorkerRpcClient.list_checkpoints`, `SupabaseConversationMemoryStore.load_run`, durable per-tool settled observation and restart recovery tests PASS |
| 08 | LLM/tool/workflow/orchestration integration | IN PROGRESS — configured provider fallback and metered reservation/settlement implemented; only approved existing chat-completion tool active | Ordered primary/fallback candidates; stream fallback only before first delta; engine tests PASS |
| 09 | Existing Frontend API Integration | IN PROGRESS — public entry and role-specific routes added; Customer/Partner API origins are configurable independently; domain screens still need real endpoints | `/` → Splash → `/onboarding` → Customer Login/Register; `/customer/*`; `/partner/*`; typed role-specific API clients and explicit CORS allowlist |
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
