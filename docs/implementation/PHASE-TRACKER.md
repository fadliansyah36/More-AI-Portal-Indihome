# MoreAI Implementation Phase Tracker

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 00 | Repository baseline & UI freeze | REVALIDATED — current UI build/lint/server/browser smoke PASS | [Phase 00 run 42965739011](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739011): lint 0 errors, build/server/browser PASS at 360/390/768/1024/1440 px; 3 existing image optimization warnings |
| 01 | Upstream source pin & provenance | COMPLETE | `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` |
| 02 | Monorepo backend workspace foundation | COMPLETE — foundation | `apps/api`, `apps/worker`, `engine`, `packages` |
| 03 | Complete upstream source copy | COMPLETE — hash verified | 111/111 matching Git blob SHA in `vendor/openmanusweb/` |
| 04 | Full backend integration & security hardening | IN PROGRESS — customer workspace list/create and owner/member-scoped file metadata/history APIs added; immutable prior-version metadata is captured by a forward-only migration; SWE read/write and full upstream Flow/server parity remain open; restore is now an approval-gated worker tool that commits prior bytes as a new CAS version | [Phase 04 run 42975296881](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42975296881): worker, sandbox, API and engine jobs PASS; browser helper is not yet a deployed browser supervisor |
| 05 | Supabase schema reconciliation | COMPLETE — additive forward-only migrations; five server-only RLS policies added explicitly; no reset/destructive DDL | Phase 07A migrations plus `moreai_explicit_server_only_rls_denials`; policy catalog verified for all five tables; leaked-password protection remains open |
| 06 | FastAPI core & OpenAPI contract | IN PROGRESS — existing versioned API and owner-scoped run/event endpoints now support SSE `Last-Event-ID` replay cursors with non-negative validation; remaining PRD domains and contract verification remain open | `apps/api/app/routers/agent_runs.py` commits `3b592151`, `01ab679f` (per-delivery cursor advancement); no tests/OpenAPI generation run in this increment |
| 07 | Worker & durable run lifecycle | IN PROGRESS — worker now distinguishes lost/uncertain lease from user cancellation and refuses stale terminal writes; approval pause/resume, checkpoint recovery, outbox and bounded tool deadlines remain implemented but require race/recovery acceptance | `apps/worker/app/runtime.py` commits `4bf4daeb`, `6f042071`; `engine/agents/durable_tool_runtime.py` commit `26b0ae6b`; no tests/runtime verification run |
| 08 | LLM/tool/workflow/orchestration integration | IN PROGRESS — provider routing/fallback, structured tool-call validation, ReAct loop, durable planning, memory replay and policy-enforced registry exist; per-tool and provider HTTP deadlines are configurable and timeout is classified for fallback/recovery; full upstream Flow/server/session parity and safe adapter coverage remain open | `MOREAI_TOOL_TIMEOUT_SECONDS` default 120 and `MOREAI_PROVIDER_TIMEOUT_SECONDS` default 90 in `.env.example`; commits `1468c202`, `2b308445`; no tests/runtime verification run for this increment |
| 09 | Existing Frontend API Integration | IN PROGRESS — Customer profile/wallet/analytics/network sessions and Partner operations are partially bound; Customer workspace APIs expose accessible workspaces, owner-scoped create/rename, files, immutable version history and signed downloads; typed client exposes workspace list/create/rename; Files view lists/downloads workspace files; EduTech lesson completion now persists through FastAPI + Supabase; remaining screens still need complete screen-to-contract binding; Captive Portal, gateway device inventory, EduTech and remaining workflows stay open | [PHASE-09-CUSTOMER-PROFILE-ANALYTICS-INTEGRATION-20261111.md](./PHASE-09-CUSTOMER-PROFILE-ANALYTICS-INTEGRATION-20261111.md); [PHASE-09-CUSTOMER-WIFI-PARTNER-OPERATIONS-INTEGRATION-20261111.md](./PHASE-09-CUSTOMER-WIFI-PARTNER-OPERATIONS-INTEGRATION-20261111.md); source commits 3c60eeb7, c436cf1a, 165cab8c, eb75e336, 5521952c, 120485e6, b5e6d437, 18d07ed3, 9ad496c7; no tests/staging run by owner instruction |
| 10 | End-to-end integration verification | BLOCKED | No real-provider authenticated browser → worker → provider E2E; real keys intentionally deferred |
| 11 | Integration release gate | NOT STARTED | No production worker/sandbox activation or release until full parity and acceptance evidence |

## Direct-main execution policy

Implementation is being performed directly on `main` as explicitly requested by the product owner. No new branch is created and the existing historical Phase 04 branch/PR is not used as the work target. Changes are committed in small, reviewable commits; production deployment and worker activation remain prohibited until Phase 11 passes.

## Current Phase 04 next work

- Customer workspace identity lifecycle increment: added owner-only `PATCH /api/v1/customer/workspaces/{workspace_id}` and typed `customerWorkspaceApi.list/create/rename`. Shared members remain read-only for workspace identity. This is a narrow API/client increment, not complete workspace CRUD or Flow/server/session parity. Commits `9238b530`, `557babf0`, `4316a430`.

1. Approval pause/resume and atomic single-use consumption are wired through the worker RPC gate and now protect workspace restore; continue closing edge cases and recovery behavior, then obtain runtime acceptance when authorized.
2. Integrate the sandbox supervisor with the OpenManus dispatcher. Keep Bash/Python/browser/file tools unavailable until the approval and supervisor gates are actually wired.
3. Complete browser isolation, DNS pinning/rebinding defenses, redirect revalidation, private/reserved IP rejection and controlled downloads. Workspace file version restore is now available through a gated worker tool; finish remaining workspace lifecycle and UX parity.
4. Close the source-to-target behavioral parity gaps in `openmanus-backend-capability-map.json`, including agent/flow lifecycle, tool schemas/handlers and upstream server/session/stream functions.
5. Maintain durable recovery, idempotency and tenant boundaries. The current user instruction for this continuation is to skip tests; therefore no new pass evidence is claimed.

## 2026-11-11 frontend route, auth and workflow integration continuation

- Root cause of the Workflow route issue: the product used a single client-side tab state with no direct Next.js route aliases for Workflow/Login/Register/Partner Login. Direct route entry had no durable mapping to the corresponding screen.
- Added route entry points `/workflow`, `/workflow-progress`, `/login`, `/register`, and `/partner/login`, all forwarding into the existing main UI (no second frontend).
- Main navigation now updates browser history and restores the active screen from direct links/history. Supabase Auth session restoration and auth-state changes protect the workspace; unauthenticated visits to protected screens return to Login.
- Customer Login/Register continue to use Supabase Auth. Password recovery now invokes `resetPasswordForEmail` instead of displaying a fabricated success toast.
- Partner Login no longer accepts hardcoded demo credentials or shows fake success. It signs in through Supabase Auth and calls the server-side Partner tenant discovery endpoint. Access is granted in the UI only when an active Partner membership is returned. Partner applicant metadata does not grant authorization; tenant membership remains server-controlled.
- WorkflowProgressView now reads persisted Customer Agent Runs from `GET /api/v1/customer/agent-runs`. The Tasks view now uses actual agent-run history instead of seeded tasks and no longer locally toggles completion. Artifact-result view reads real artifact metadata from `GET /api/v1/artifacts`; owner-scoped upload and short-lived signed-download endpoints are now implemented, but remain unavailable until a private artifact bucket is provisioned and configured.
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


## 2026-11-11 direct-main integration increment — durable planning tool and workflow step API

- Added the durable `planning` tool handler to `DurableOpenManusRuntime`, backed by the existing Supabase `agent_run_steps` store. Commands: create, get and mark_step. It is registered through the central `PolicyEnforcedToolRegistry`; it does not bypass tool policy.
- Injected the same `SupabasePlanStore` instance into the Manus runtime from the worker registry factory.
- Hardened provider tool-call parsing: malformed call objects, duplicate IDs, invalid tool names, oversized/non-JSON arguments and non-object arguments now fail closed instead of being silently discarded.
- Added `GET /api/v1/customer/agent-runs/{run_id}/steps`; it verifies ownership of the parent run before returning persisted step metadata.
- Added typed `CustomerWorkflowStep` and `customerApi.getRunSteps` to the existing frontend API client. No UI components, routes, styles or navigation were changed in this increment.
- Direct-main commits: `284001641d963a2213c653e4ac6477c58ab2ac9b`, `e373ef1258e9cff80812b9009916eac7d73f1222`, `b207f30eb987e802135fe7b7720a86fe1da48a32`, `19d14df45cced74d8ed36b64fb94be082f71ea86`, `32fd349cc8952a469d09586cec45064cb0080fdf`, `92e4373b0fcd74008fbc0b77178079d764c621d4`.
- No tests, lint, build, browser, provider, database mutation or live runtime checks were run, per explicit instruction. These commits are source changes only and are not phase acceptance.
- Still open: safe file storage/download contract, search-provider adapter, browser supervisor/socket-level egress, isolated SWE/editor workspace, full upstream flow/server/session/WebSocket/log parity, remaining Customer/Partner APIs, Super Admin mutation/audit governance, and all Phase 10/11 gates.


## 2026-11-11 direct-main integration increment — Search, Files, Profile, Partner and RBAC

Detailed report: [DIRECT-MAIN-FULLSCOPE-INTEGRATION-REPORT-20261111.md](./DIRECT-MAIN-FULLSCOPE-INTEGRATION-REPORT-20261111.md).

- Added `TavilySearchAdapter` at `engine/tools/search_provider.py`. It is pinned to the provider endpoint, accepts only a query (not an arbitrary URL), caps result count and output lengths, and returns normalized source URLs/snippets. Worker registration is conditional on `TAVILY_API_KEY`; absent credentials mean the tool is not advertised.
- Added `SupabaseArtifactTool` at `engine/tools/storage.py`. It writes a per-user/per-artifact Storage path, enforces a 2 MB UTF-8 text limit, validates filename/MIME type, hashes content with SHA-256, persists the artifact row and compensates a failed metadata insert by deleting the uploaded object. Worker registration is conditional on `MOREAI_ARTIFACTS_BUCKET`.
- Added private artifact upload and signed-download API routes. Upload requires authenticated Customer context, a safe filename, raw request body up to 2 MB, a configured private bucket, service-role-only Storage access, and owner-scoped metadata persistence. Signed download first verifies the artifact row belongs to the caller and that its path is inside the caller's storage prefix, then creates a 60-second signed URL.
- Added `MOREAI_ARTIFACTS_BUCKET` configuration. The Supabase Storage inventory previously showed no configured buckets; no bucket was created or modified. File API returns 503 until a private bucket is provisioned and this setting is configured.
- Added profile PATCH endpoint using the caller's Supabase access token against the existing `profiles` table, so RLS remains authoritative. Avatar paths must remain inside the user's prefix; arbitrary external URLs are rejected.
- Added Partner location/campaign/member mutations with active server-side Partner membership, owner/admin role checks and tenant/location validation. Added network creation, verification configuration read/write gated by the platform method catalog and adapter readiness, and one-time access-code creation/revocation. Access codes are stored as SHA-256 hashes; plaintext is returned once. Network-bound access codes require a location.
- Added platform permission resolution through active `user_role_assignments` → platform `roles` → `role_permissions` → `permissions`. Super Admin overview, partner listing, agent-run listing and audit reads now enforce their concrete permission keys rather than role-name-only checks.
- Added typed frontend API client methods for profile update, artifact upload/download, Partner locations/campaigns/members/networks/verification and access codes. Existing screen components were not modified because the required before/after UI screenshot gate could not be satisfied in this no-browser/no-live-test continuation.
- Direct-main commits for this increment include: `536aa98105cf4b89329a368c3d105a32bbdc3619`, `662d24195c6c0b3c933feb4292fd1bb72a0cc6d9`, `cda97d516aded560a83fe96f586b2eae1840c3e9`, `9d5d27828429709c4f8082991d4cb72946d80844`, `ce21ce5a19f57fc1defbe8823b5cc2dc2df97e6b`, `475af4c101c646b29e4fba369d06cea957858d01`, `a6c87ea84ef8b7ef54feac01112ad175e5d0bf15`, `5dedef1f65aeda4be90203a0f75854d38be7299c`, `208d20e94e8187e3f21a2c4d3a35f7eb21734dd0`, `eb21c925341b4da7821acfa3b5b53ae98858eb8a`, `e6790a7bcb85a4fd96b9e75e208f6f9de324a5e4`, `578852194bd4a89537dcd0c252ce05d191962237`, `11069b1e455984968ade08f6c224ca48597e5b56`, `3033aa7dfc21380cdd72a4bc6e0fdcd1fe3a4c20`, `ad27e80255673f6417264d9c92f16d2aaef4dd1c`, `35a62f3ef00354cdb659084a5e174fa6832fed0d`, `7d97ed8c9bbfe47f97e2cb779887168e4e24d985`, `556da5e8d82d6d0c2a9e5eec8229da159d2a284f`, `1d57df3089f2b640e7c4f80435b6c44369fb8874`.
- Schema inspection confirmed there are no public notification tables and no dedicated captive-portal/Wi-Fi configuration table in the connected database. Existing network verification catalog/config tables can store adapter-specific public configuration and secret references, but this is not equivalent to a full captive-portal management domain.
- Super Admin mutation endpoints were intentionally not added: the current API lacks a transactional mutation RPC that atomically enforces permission, performs the privileged change and appends an immutable audit record. A non-atomic "mutate then best-effort audit" implementation would violate governance requirements. The existing audit table does not itself prove immutability at the database layer.
- Browser remains default-deny. The existing Docker sandbox is network-disabled for Python/Bash, but a browser supervisor with socket-level egress enforcement, DNS pinning/rebinding protection, redirect/subresource/download controls is not integrated. The SWE workspace editor has no isolated persistent workspace adapter and is not advertised.
- No UI screenshots, tests, lint, typecheck, build, browser checks, provider calls, database writes/migrations or deployment were performed in this increment, per the product owner's current instruction. These are committed source changes, not phase acceptance evidence.

- Follow-up hardening commits: `4015422d5a8acb52a4ba014797cfcf878e1a7736` (API private-bucket check) and `5808c3fc8ad976d9e905c98eef64f91031ea2de0` (worker private-bucket check and artifact run linkage). Capability map updated at `a8cfef8e7745298f429a7daa81990330f1c1b9e3`.


## 2026-11-11 — Phase 05 notifications and Super Admin governance increment

- Increment report: [PHASE-05-06-NOTIFICATIONS-GOVERNANCE-20261111.md](./PHASE-05-06-NOTIFICATIONS-GOVERNANCE-20261111.md).
- Applied migrations `20261111100000_moreai_notifications_private_artifacts_immutable_audit` and `20261111103000_moreai_admin_partner_status_atomic_audit` to Supabase project `uunfgimtokhucegqbpce`.
- Verified `notifications` (12 columns) and `notification_preferences` (5 columns) exist with RLS enabled and server-only grants.
- Verified private `moreai-artifacts` bucket, `public=false`, 2 MiB limit and MIME allowlist.
- Verified immutable audit UPDATE/DELETE and TRUNCATE triggers on `admin_audit_logs`.
- Added owner-scoped notification list/read/preferences endpoints, typed API client methods, and a permission-specific `partner.organization.manage` partner-status mutation. The database RPC locks the partner row and writes the audit record plus idempotency response in one transaction.
- This is not Phase 05/06 completion: notification producers/delivery, remaining Wi-Fi/captive portal/voucher/analytics domains, full Partner operations and broader Super Admin governance remain open. No UI files were modified.
- Supabase Storage RLS table ownership blocked a direct policy DDL attempt; existing `storage.objects` already has RLS enabled and no client policies. The migration intentionally did not bypass ownership.
- No runtime tests, lint, typecheck, build, browser verification or deployment were performed in this increment. Schema catalog and migration application were verified only.


## 2026-11-11 — Phase 04 / 07–08 cancellation and browser egress increment

- Report: [PHASE-04-07-08-CANCELLATION-EGRESS-INCREMENT-20261111.md](./PHASE-04-07-08-CANCELLATION-EGRESS-INCREMENT-20261111.md).
- `engine/agents/durable_tool_runtime.py`: active tool invocation is raced against cancellation; when cancellation wins, the tool coroutine is cancelled and awaited before the run exits.
- `apps/sandbox/app/browser_security.py`: added DNS-pinned TLS socket transport primitive, peer-IP verification, and bounded redirect-chain validation.
- Browser remains disabled: the browser engine is not yet forced through this transport, and socket/network namespace enforcement plus full redirect/subresource/WebSocket/download mediation are not complete.
- SWE persistent workspace/editor and full upstream Flow/server/session parity remain open.
- No tests, lint, typecheck, build, browser checks or deployment were run. No new pass evidence is claimed.


## 2026-11-11 — Phase 04 Browser Supervisor & Persistent SWE Workspace increment

- Report: [PHASE-04-BROWSER-SWE-INTEGRATION-20261111.md](./PHASE-04-BROWSER-SWE-INTEGRATION-20261111.md).
- Added private Supabase Storage-backed SWE workspace editor scoped by `user_id/workspace_id`; workspace ID is passed from durable run context into `str_replace_editor`.
- Added path traversal and implicit overwrite rejection, UTF-8/2 MiB bounds, private bucket verification and SHA-256 result metadata.
- Added authenticated DNS-pinned CONNECT proxy and standalone proxy entrypoint. Each CONNECT is checked against domain allowlist, public DNS set and pinned peer IP.
- Added isolated FastAPI Playwright supervisor service and worker-side HTTP adapter; browser tool is registered only when explicit feature enablement, service URL/token and network-egress enforcement flag are present.
- Browser remains disabled by default. The egress flag is only a deployment assertion; actual network namespace/firewall denial of direct egress has not been provisioned or verified. Downloads remain disabled, and click/type are not in the exposed action contract.
- Workspace file CAS/leases, list/read/delete/version history, complete upstream SWE parity, durable event outbox/sequence/replay, remaining OpenManus Flow/server/session parity and remaining product domains remain open.
- No browser/SWE runtime tests, network tests, build, lint, typecheck, E2E or deployment were performed. No release acceptance is claimed.


## 2026-11-11 continuation — browser egress topology and durable run event outbox

- Added a separate browser container image and Docker Compose topology. Browser supervisor has only the Docker internal network; the authenticated egress proxy is the only component attached to the external bridge. Containers are non-root/read-only with dropped capabilities and resource limits.
- This is deployment configuration, not packet-level verification. Browser remains disabled until the actual host/network policy is deployed and negative direct-egress tests pass.
- Added migration draft `20261111110000_moreai_durable_run_event_outbox.sql`: per-run monotonic sequence allocation, event-key idempotency, transactional append to `agent_run_events` and `agent_run_event_outbox`, bounded payloads and service-role-only RPC.
- Worker now emits run lifecycle/progress events and durable Manus emits tool.started/tool.completed/tool.cancelled events. Sensitive checkpoint/tool arguments and outputs are not included in public event payloads.
- Existing event GET/SSE endpoints can replay the ordered `agent_run_events` sequence. Outbox publisher/consumer delivery acknowledgement and retry/dead-letter worker remain open.
- Migration is not applied. Do not deploy event-publishing worker code until schema review/apply/RPC verification is authorized.
- SWE workspace still lacks list/read/delete, version snapshots, database lease/CAS and crash recovery. Full upstream Flow/server/session and memory/RAG/provider/tool parity remain open. Phase 06 domain coverage and Phase 09 UI integration remain incomplete.
- No UI files changed. No tests, lint, typecheck, build, browser network verification, SQL apply, E2E, provider call or deployment run in this increment.
- Report: [PHASE-07-BROWSER-EGRESS-EVENT-OUTBOX-20261111.md](./PHASE-07-BROWSER-EGRESS-EVENT-OUTBOX-20261111.md).
- Commits: `5ce5416` (event outbox migration draft), `b1c4203` (worker event client), `ee876f8`/`ce33e22` (run lifecycle/progress), `a96df53`/`baaa049` (tool lifecycle), `aefb661` (registry wiring), `e4dafa8` (browser image), `d7cf092` (isolated network topology), `997e4b5` (implementation report).


## 2026-11-11 Phase 07A continuation — canonical outbox publisher (source committed, DB not applied)

- Read-only live schema reconciliation confirmed existing `agent_run_events`, `agent_run_checkpoints`, and canonical `outbox_events`; outbox status check allows pending/processing/published/failed/dead_letter, `aggregate_id` is UUID, and RLS has restrictive deny for anon/authenticated.
- Corrected the earlier event migration to extend `outbox_events` instead of creating a parallel event outbox. The migration adds event idempotency/sequence columns and worker lease fields.
- Worker append now requires an active worker lease. The migration replaces checkpoint and finish RPCs to allocate event sequence through one serialized per-run counter, eliminating the old `max(sequence)+1` race among worker event writers.
- Added leased outbox claim, acknowledgement, exponential retry and dead-letter RPCs. Worker publisher sends private per-run Realtime Broadcast notifications and acknowledges only after successful HTTP response. Delivery is at-least-once; dedupe uses event_id/sequence. Existing authenticated Customer SSE/GET remains the durable replay source.
- Worker runtime starts outbox publishing concurrently with agent dispatch.
- **Not applied to Supabase**; no production RPC invocation, migration, tests, lint, typecheck, build or deployment run. Event publisher cannot be considered operational until the migration is reviewed/applied and verified.
- Workspace CRUD/version/locking, upstream Flow/server/session + full memory/RAG parity, Phase 06 domain/governance, Phase 09 screenshot-gated UI work, Phase 10 and Phase 11 remain open.
- Detailed report: [PHASE-07-BROWSER-EGRESS-EVENT-OUTBOX-20261111.md](./PHASE-07-BROWSER-EGRESS-EVENT-OUTBOX-20261111.md).
- Commits: `7e1ec05` outbox claim/ack/retry RPCs; `c42aa35` canonical outbox reconciliation; `fe44df8` worker lease check; `4771ec6` checkpoint/finish serialization; `43e3f3c` worker client publisher; `6061038` publisher loop; `3d53f8f` worker loop integration; `76410ad`, `08f11b5`, `02542d8`, `ce933f8` follow-up schema/payload correctness fixes; `dfc8819` report.


## 2026-11-11 Phase 07A — database schema acceptance

- Applied canonical outbox migration to Supabase project `uunfgimtokhucegqbpce` (migration version `20261111091531`) and follow-up retry lease-fencing migration.
- Live read-only verification confirms `agent_run_event_counters` and outbox extension columns exist; all six RPC signatures are installed; anon/authenticated EXECUTE is false and service_role EXECUTE is true.
- Outbox publisher runs in worker source alongside durable run execution; append creates replay event and outbox record transactionally; claim uses SKIP LOCKED; retry backoff/dead-letter and lease expiry recovery are implemented; Broadcast is at-least-once and deduplicated by event_id/sequence.
- No production run/outbox rows were created or mutated for smoke tests. No actual worker process, Realtime subscriber, cancellation, retry or crash-recovery E2E has been proven. Thus database schema gate passed; Phase 07 runtime acceptance remains OPEN pending isolated staging execution.
- Security Advisor still flags five RLS-enabled tables with no policies and leaked-password protection disabled. See the Phase 07A report for exact tables and remediation.
- Report: [PHASE-07A-DURABLE-EVENT-OUTBOX-ACCEPTANCE-20261111.md](./PHASE-07A-DURABLE-EVENT-OUTBOX-ACCEPTANCE-20261111.md).


## 2026-11-11 — Explicit server-only RLS remediation (direct main)

- Product-owner execution constraints: work directly on `main`; do not create a branch; skip staging and runtime/real-world tests; prioritize integration within the MoreAI platform ecosystem. No test/build/deployment success is claimed.
- Added and applied forward-only migration `20261111120000_moreai_explicit_server_only_rls_denials.sql` to canonical Supabase project `uunfgimtokhucegqbpce`.
- Five server-owned tables now have explicit `FOR ALL TO anon, authenticated USING (false) WITH CHECK (false)` policies: `agent_tool_approvals`, `network_gateway_nonces`, `network_verification_method_catalog`, `partner_access_code_redemptions`, and `partner_access_codes`.
- Read-only `pg_policies` inspection confirmed all five policies and their deny-all predicates. Latest Security Advisor response no longer reports the five RLS-without-policy findings.
- Leaked Password Protection remains WARN and is not remediated by SQL. It must be enabled through Supabase Auth project configuration; no auth-setting connector action was available in this execution.
- No production rows were written and no runtime/staging tests were run.
- Implementation report: [SECURITY-EXPLICIT-SERVER-ONLY-RLS-20261111.md](./SECURITY-EXPLICIT-SERVER-ONLY-RLS-20261111.md).
- Commit: `2b1a728d424a93dc943d8ab9650957ee6782401a`.


## 2026-11-11 — Phase 04 independent high-risk approval gate
- Fixed `apps/worker/app/registry_factory.py`: the durable owner-approval gate is now always passed to the tool runtime, not conditionally coupled to Docker sandbox enablement. This covers independently enabled browser supervisor as well as sandbox tools.
- Browser/sandbox activation flags and release gates remain unchanged; this wiring does not activate either adapter.
- The worker still waits/heartbeats during approval rather than releasing and reclaiming the run lease. Full run-level pause/resume remains open.
- No staging/runtime/provider tests, production data writes, migrations, build/lint/typecheck or deployment. UI untouched.
- Report: [PHASE-04-HIGH-RISK-APPROVAL-GATE-20261111.md](./PHASE-04-HIGH-RISK-APPROVAL-GATE-20261111.md).


## 2026-11-11 — Phase 04 run-level approval pause/resume
- Added atomic approval + pause checkpoint + lease release, idempotent owner decision/resume, claim exclusion, expiration recovery and attempt-preserving continuation.
- Worker runtime now handles RunPausedForApproval without marking the run failed or cancelled.
- Migration: 20261111140000_moreai_run_level_approval_pause_resume.sql.
- Report: PHASE-04-RUN-LEVEL-APPROVAL-PAUSE-RESUME-20261111.md.
- Migration applied successfully to canonical Supabase project uunfgimtokhucegqbpce. Read-only verification confirmed the column, table, RPC signatures, RLS and deny policy. No staging/runtime/tests/build/lint/typecheck/provider calls/deployment; runtime acceptance remains pending.


## 2026-11-11 — Phase 04 durable workspace CAS and FlowFactory wiring
- Added immutable versioned workspace object paths with expected-version CAS, lease-fenced reservation/commit/abort RPCs, owner/member authorization and private server-only metadata.
- SWE editor now reads file version metadata, rejects stale expected_version, reserves a fenced write, uploads immutable content, and commits metadata only while the worker lease is valid.
- FlowFactory is now wired into worker registry construction; planning flow is adapted to the durable MoreAI plan/checkpoint runtime rather than importing upstream process-global log/plan state.
- Migration: 20261111150000_moreai_workspace_file_cas_versioning.sql.
- Browser supervisor remains isolated behind a pinned-DNS CONNECT proxy and internal-only supervisor network; no browser deployment/runtime proof was performed.
- Flow lifecycle parity, full upstream server/session behavior, browser redirect/subresource live proof, and runtime acceptance remain open. No tests/build/lint/typecheck/staging/deployment.


## 2026-11-11 — Phase 07 cancellation/approval recovery
- Approval-paused and queued runs now cancel terminally; pending approvals are denied, pause checkpoints marked cancelled, leases cleared, and a deduplicated cancellation event is written to the durable outbox.
- Running tasks retain cooperative cancellation through heartbeat and tool boundaries.
- Migration: 20261111160000_moreai_cancel_waiting_approval_and_outbox.sql.


## 2026-11-11 — Phase 06 Customer wallet/ledger/usage and Phase 09 run route alignment
- Added authenticated read endpoints for customer wallet, credit ledger, LLM usage, entitlements and quotas using existing canonical tables and authenticated principal scoping.
- Typed frontend run APIs now target existing `/api/v1/agent-runs` routes; UI components untouched.
- Report: PHASE-06-CUSTOMER-ACCOUNT-READ-APIS-20261111.md.
- Migration `20261111150000_moreai_workspace_file_cas_versioning` applied and schema/RLS/RPCs verified read-only. Runtime/API contract tests not run.


## 2026-11-11 — Phase 06/09 partner access-code redemption integration
- Added tenant-scoped partner access-code inventory/redemption history and authenticated customer redemption using the existing atomic RPC with server-side hashing and Idempotency-Key.
- Added typed client methods; UI untouched.
- Report: PHASE-06-PARTNER-ACCESS-CODE-APIS-20261111.md.


## 2026-11-11 — Phase 04 PlanningFlow restart/resume parity
- PlanningAgentRuntime restores the persisted manifest and steps on worker recovery; it does not regenerate the plan after a pause/restart.
- Succeeded step outputs are rehydrated, dependency gates are enforced, and step outputs/checkpoints are persisted.
- Report: PHASE-04-PLANNINGFLOW-REPLAY-20261111.md.


## 2026-11-11 — Phase 04 planning approval integration
- Planning steps with elevated risk or non-basic tool requirements now use the durable run-level approval gate and resume from the persisted plan after owner approval.
- Tool registry policy remains independently enforced after the planning approval.


## 2026-11-11 — Phase 04 workspace CAS crash recovery
- Added expiring write reservations and safe reclamation after worker crashes; stale reservation tokens cannot commit.
- Migration: 20261111170000_moreai_workspace_cas_expiry_recovery.sql.


## 2026-11-11 — Schema application verification
- Applied migrations to canonical Supabase project `uunfgimtokhucegqbpce`: `20261111150000_moreai_workspace_file_cas_versioning`, `20261111160000_moreai_cancel_waiting_approval_and_outbox`, and `20261111170000_moreai_workspace_cas_expiry_recovery`.
- Read-only verification confirmed workspace version/reservation columns, four workspace CAS RPCs, cancellation RPC, and server-only RLS policy. No runtime tests or deployments were performed.


## 2026-11-11 — Phase 04/09 workflow step API contract
- Implemented the previously missing authenticated `GET /api/v1/agent-runs/{run_id}/steps` route, scoped to run ownership and exposing safe metadata only.
- Existing typed frontend client already calls this path; no UI changes required.
- Report: PHASE-04-09-RUN-STEPS-API-20261111.md.


## 2026-11-11 — API client contract alignment

- Commit: `c2e1c5a437485207a09712d3e118f095b5e579eb`.
- Added typed Customer conversation detail and durable run-event replay methods to `lib/api/client.ts`.
- Aligned workflow-step type with the metadata-only response of `GET /api/v1/agent-runs/{run_id}/steps`; private step input/output/error are not represented in the public client type.
- No UI files changed and no tests/build/lint/typecheck/staging/deployment were run. This is API contract alignment, not Phase 09 acceptance.
- Report: [API-CLIENT-CONTRACT-ALIGNMENT-20261111.md](./API-CLIENT-CONTRACT-ALIGNMENT-20261111.md).

- SSE client follow-up commit: `6b10c622b1716cf4422a99d4e2f653c5ad9642ca`; stream event IDs are preserved and caller-supplied replay cursors are passed to FastAPI. Automatic reconnect and live runtime delivery remain unverified.


## 2026-11-11 direct-main integration continuation

- Customer run-step endpoint now uses the same metadata-only contract as the canonical run endpoint; private step input/output/error are excluded and limit is bounded. Commit `1efe43a0f87b97596ada43126aa9dad6d3781267`.
- Durable run event replay now validates non-negative cursors and bounded limits; SSE wait windows are validated to 1–120 seconds on both general and Customer routes. Commits `b2a49909792f1ea17627d91519835d6572a0eb54` and `de60315866ac60558b67c117d5fb9d3b3ada6f65`.
- Read-only Supabase inventory and migration history reviewed on canonical project `uunfgimtokhucegqbpce`; no SQL was applied.
- No tests/build/lint/typecheck/staging/provider calls/deployment were run in this continuation. These commits do not constitute phase acceptance.
- Full report: [DIRECT-MAIN-INTEGRATION-CONTINUATION-20261111.md](./DIRECT-MAIN-INTEGRATION-CONTINUATION-20261111.md).


## 2026-11-11 — Phase 04/06 approval transport contract alignment
- The Customer tool-approval request schema now accepts the canonical OpenManus browser tool key `browser_use`, matching the worker registry/policy key (previously only the alias `browser` was accepted). Existing compatibility keys are retained.
- Commit: `a8c69eb6d01609990cefcfcd7b85d15ec6db9ae8`.
- This closes a narrow API contract mismatch only; browser supervisor deployment, socket-level egress proof and full approval lifecycle acceptance remain open. No tests/runtime checks were run.
- Report: [DIRECT-MAIN-INTEGRATION-CONTINUATION-20261111.md](./DIRECT-MAIN-INTEGRATION-CONTINUATION-20261111.md).


## 2026-11-11 — Phase 04 canonical OpenManus approval key reconciliation
- API schema, database CHECK constraint and server-only approval request RPC now consistently accept canonical runtime keys `browser_use` and `planning_step`, retaining legacy aliases.
- Migration `20261111180000_moreai_openmanus_approval_tool_keys` applied to canonical Supabase project `uunfgimtokhucegqbpce`.
- Read-only verification confirms the new CHECK constraint and function ACL restricted to postgres/service_role. Security Advisor continues to flag leaked-password protection disabled (WARN).
- Commits: `379944a6d4715ce551155df7fe39d38882a79a56` (migration), `5af4da0670319326d2e562f6e4a3f21961f3f7d7` (API), `8d581cdc3c4cc3fca8f753ee15e6258a03f25d6e` (report).
- No runtime/tests/build/lint/typecheck/staging/provider/deployment. Phase 04 remains IN PROGRESS; browser supervisor socket-level egress, complete upstream Flow/server/session parity and full SWE integration remain open.
- Report: [PHASE-04-OPENMANUS-APPROVAL-KEY-ALIGNMENT-20261111.md](./PHASE-04-OPENMANUS-APPROVAL-KEY-ALIGNMENT-20261111.md).


## 2026-11-11 — Phase 04 browser supervisor hardening continuation
- Browser proxy cancellation is now propagated correctly and tunnel cleanup tolerates socket-close errors. Browser action contract is typed, request count is capped at 200 per action, and WebSockets are denied because they are outside the approved action contract.
- Commits: `ac571bd3589ef09393ee7f94043986f2bdc573c6`, `1735c5700db427b822648fdfad13b9655959a4fd`.
- Report: [PHASE-04-BROWSER-SWE-HARDENING-CONTINUATION-20261111.md](./PHASE-04-BROWSER-SWE-HARDENING-CONTINUATION-20261111.md).
- Phase 04 remains IN PROGRESS. Direct browser egress denial has not been provisioned/verified; SWE list/read/delete/version history/restore and Git workflows remain incomplete; full upstream Flow/session/server/WebSocket and backend capability parity remain open. Browser stays disabled. No tests, lint, typecheck, build, runtime/network verification, staging, provider calls or deployment were run.


## 2026-11-11 — Browser network isolation topology
- Added a two-network Compose topology: browser supervisor only on an internal network; CONNECT egress proxy on internal + external network. Added proxy entrypoint, dedicated browser/proxy Dockerfiles, and pinned Playwright dependency.
- Commits: `16db80a9d9d7a5d1488de9cb2aece9afade0993a`, `57f7428ca87445b0fab985952e21c2db19a2e1b6`, `ea26636acbc0d599db52873890c0e8f1ead77eb3`, `5dc2f8753b32741458f6417472114703cd757045`, `13ca010e0fc08f17aaffd520003e9ef636126081`.
- Acceptance report: [PHASE-04-BROWSER-NETWORK-ISOLATION-ACCEPTANCE-20261111.md](./PHASE-04-BROWSER-NETWORK-ISOLATION-ACCEPTANCE-20261111.md).
- This is deployable source topology, not runtime proof. Do not activate browser until direct IPv4/IPv6 egress and bypass tests fail as expected. SWE CRUD/history/restore/Git and complete Flow/session/server/WebSocket/backend parity remain open. Phase 04 NOT ACCEPTED; Phase 07 not started.


## 2026-11-11 — Browser runtime acceptance verifier
- Added `apps/sandbox/scripts/verify-browser-network-isolation.sh` for private-only browser attachment, proxy bridge topology, Docker internal network, blocked direct IPv4/IPv6 egress, allowlisted proxy egress, rejected loopback/metadata/unlisted targets, and non-privileged/non-host network mode.
- Commits: `8b1093cdc29765385883e79598137340ea66f52a`, `4eebf0984a5362e39f34b98865cd02844edc6f14`.
- Report: [PHASE-04-RUNTIME-ACCEPTANCE-VERIFIER-20261111.md](./PHASE-04-RUNTIME-ACCEPTANCE-VERIFIER-20261111.md).
- Verifier is committed but not executed: no authorized Docker host tool in this session, and prior test/build/deploy restriction remains in force. SWE API/history/restore/Git and full Flow/session/server/WebSocket/backend parity remain incomplete. Phase 04 IN PROGRESS; Phase 07 not started.


## 2026-11-11 Customer Wi-Fi and Partner operations API integration

- Implementation report: [PHASE-09-CUSTOMER-WIFI-PARTNER-OPERATIONS-INTEGRATION-20261111.md](./PHASE-09-CUSTOMER-WIFI-PARTNER-OPERATIONS-INTEGRATION-20261111.md).
- Added owner-scoped Customer `GET /api/v1/customer/network-sessions` using existing `network_sessions`, `partner_networks` and `partner_locations` schema.
- Wi-Fi Management and connected-device surfaces now consume actual session data; gateway device inventory, per-device bandwidth/IP and disconnect actions are explicitly unavailable rather than fabricated.
- Partner access-code screen now lists/creates/revokes server-generated one-time plaintext codes; Partner staff screen reads memberships and creates UUID-based invitations; Partner campaign screen reads/creates/updates tenant campaigns.
- Customer profile credit display now reads wallet balance. Analytics breakdown derives model/request/token counts from persisted `llm_usage` records instead of illustrative feature percentages.
- Existing Supabase schema only was used; no DDL, migration, RLS, grant, RPC or production row mutation occurred.
- User instruction: no real testing or staging. No build, lint, typecheck, unit/integration/E2E, browser, screenshot, CI, migration apply, runtime check or deployment was performed. No phase acceptance is claimed.
- Phase 09 remains IN PROGRESS. Remaining domain blockers include Captive Portal verification lifecycle, actual gateway device inventory/control, customer reward catalog/claims, EduTech, partner invitation by email/revocation, promotion asset delivery, and complete Super Admin workflows.


## 2026-11-11 — Durable worker active-dispatch cancellation

- Commit: `46a988587b0353256fa403b232e9c483f2a135a6`.
- `WorkerRuntime.run_once` now races the active dispatcher task against the heartbeat-driven cancellation event. When cancellation is requested while a provider/tool call is in flight, the dispatcher task is cancelled, awaited/reaped, and the run is finalized as cancelled with a durable event.
- Worker shutdown cleanup now cancels/reaps child dispatch and cancellation-watch tasks while leaving the interrupted run lease recoverable when shutdown is not a user cancellation.
- This closes the worker coordinator gap where cancellation was only cooperative and could wait indefinitely for an active I/O call. It does not prove every provider/tool adapter responds immediately to task cancellation.
- No tests, lint, typecheck, build, runtime/provider calls, staging or deployment were run, following the standing owner instruction. This is source implementation only, not Phase 07 acceptance.
- Phase 07 remains IN PROGRESS. Next: verify adapter-level cancellation and timeout behavior when testing is authorized; continue approval resume, lease fencing/recovery reconciliation, and event replay/outbox acceptance.


## 2026-11-12 — bounded tool execution deadline

- Added a hard per-invocation timeout to `DurableOpenManusRuntime`, raced alongside the existing cancellation signal. On deadline, the active tool task is cancelled and awaited before control returns to the agent loop.
- Timeout is not conflated with user cancellation or generic adapter failure: the durable tool observation records `tool_execution_timed_out`, the configured deadline and tool key; the settled checkpoint records `timed_out`, allowing recovery to reuse the result rather than silently re-execute the same invocation.
- Configured through `MOREAI_TOOL_TIMEOUT_SECONDS`, default 120 seconds, bounded to 1–1800 seconds. Invalid values fail closed during registry construction.
- Commits: `cbcbda694206a0c2904b6a5626dc04feff292d07` (deadline/cancellation race), `ca7dce8dcd92f638997adad2abca68f71b62d3c6` (worker config), `e363526fbb820a2f794fc21c48eda0079cf797fa` (.env example), `92639fbeec936a0e8cc04ce72fe5afb245f55092` (distinct timeout outcome).
- No tests, lint, typecheck, build, provider/runtime, migration, staging, browser QA or deployment were run, per the standing owner instruction. This is source-only implementation evidence, not acceptance.
- Phase 07 and Phase 08 remain IN PROGRESS. Phases 04, 06 and 09 remain IN PROGRESS; Phase 10 remains BLOCKED; Phase 11 remains NOT STARTED.


## 2026-11-12 — provider and tool deadline alignment

- Durable tool execution now uses the lower of the configured worker deadline and the canonical tool-catalog deadline. The persisted timeout observation reports that effective deadline rather than incorrectly reporting the larger worker ceiling. Commit: `26b0ae6b7795f08c7312e5439de4ea211a0169a7`.
- OpenAI-compatible complete and streaming adapters now read `MOREAI_PROVIDER_TIMEOUT_SECONDS` (default 90 seconds; accepted range 1–600 seconds). Invalid values fail closed. Transport timeouts remain classified as retryable provider availability failures so the configured fallback route can be attempted where no stream output has been emitted. Commit: `1468c202be284c8d02e51dd9de1e600bdba515d8`.
- `.env.example` documents the provider timeout. Commit: `2b3084455cd6d59acaacb4edcc5930dfd9cda301`.
- No tests, lint, typecheck, build, runtime/provider execution, migration apply, browser QA, staging or deployment were run. No runtime pass or release acceptance is claimed.
- Phase 07 and Phase 08 remain IN PROGRESS; Phase 04, 05, 06 and 09 remain in their existing states; Phase 10 remains BLOCKED and Phase 11 NOT STARTED.


## 2026-11-12 — worker lease fencing behavior and SSE replay cursor

- Worker heartbeat handling now distinguishes a confirmed/uncertain lease loss from a user cancellation. On lease loss or heartbeat transport failure, the worker stops local dispatch and deliberately avoids event append/finish calls; the current lease owner or database lease-expiry recovery remains authoritative. This prevents stale workers from writing terminal state after ownership is no longer proven. Commits: `4bf4daebbce10c7ad12d82c4074af8670ce222ae`, `6f042071ee9e67bcb5750fbc6671ee49e0555ee3`.
- The owner-scoped FastAPI run event list and SSE stream now accept the standard `Last-Event-ID` header. It is validated as a non-negative integer and combined with the optional `after` query cursor, enabling browser EventSource reconnects to resume after the last delivered sequence. Commit: `3b592151022d4425dbf9081dad34dcd607944814`.
- These are source changes only. No tests, lint, typecheck, build, OpenAPI generation, migration apply, worker runtime, browser QA, staging or deployment were run. Race safety and replay continuity remain unaccepted until tests are authorized and executed.
- Phase 04/07/06 remain IN PROGRESS. Phase 08 and 05/09 remain IN PROGRESS; Phase 10 remains BLOCKED and Phase 11 NOT STARTED.


## 2026-11-12 — Phase 07 frontend durable SSE reconnect contract

- Commit: `500510bbb041dc235d3b7a832d3dc314a6d86fc6`.
- Extended `moreAiApiStream` with bounded reconnect, numeric durable event cursor, `Last-Event-ID` header, refreshed Supabase Auth session per reconnect, AbortSignal cancellation, and exponential backoff for transient transport/5xx failures.
- Terminal auth/authorization/contract errors are not retried. Terminal run events stop reconnect. Server `stream.timeout` is treated as a long-poll boundary and resumes from the last delivered sequence.
- This is transport-layer implementation only. No current UI component invokes this stream helper, and no tests, lint, typecheck, build, browser, API, SSE, worker/runtime or staging checks were run. Phase 07/09 acceptance remains open.
- Capability map updated: `openmanus-backend-capability-map.json`.
- Report: [PHASE-07-FRONTEND-SSE-RECONNECT-20261112.md](./PHASE-07-FRONTEND-SSE-RECONNECT-20261112.md).



## 2026-11-12 — Phase 08 streaming usage latency accounting

- Commit: `157b110a14d456dad6751a22f34983a26c2df19e`.
- `MeteredGateway.stream` now records elapsed provider-stream latency using `time.monotonic()` instead of persisting a hardcoded zero. Provider/model token usage and cost remain recorded through the existing idempotent accounting lifecycle.
- No provider call, database write, credit settlement, retry/fallback runtime, tests, lint, typecheck or build was executed. This closes a source-level accounting omission only; Phase 08 remains IN PROGRESS.
- Capability map: `openmanus-backend-capability-map.json`.
- Report: [PHASE-08-STREAMING-LATENCY-ACCOUNTING-20261112.md](./PHASE-08-STREAMING-LATENCY-ACCOUNTING-20261112.md).

## 2026-11-12 — SWE workspace CAS tool-contract alignment
- Commit: `18fecad2f2785f14b8ae1aa3c676ff3936a095e6`.
- The `str_replace_editor` tool schema now exposes optional non-negative `expected_version`, aligning the LLM-visible contract with the existing lease-fenced workspace CAS handler. Stale explicit versions are rejected by the handler; omission retains compatibility by resolving the current version.
- No tests, lint, typecheck, build, browser/runtime, migration or deployment checks were run. This is a narrow contract fix, not SWE workspace or Phase 04 acceptance.
- Detailed remaining phase gaps and next sequence: `PHASE-04-09-CONTINUATION-20261112.md`.


## 2026-11-12 — durable approval pause propagation and live Supabase inventory
- Commits: `b3c493cd4ba42717ca206ace7b817d8d656c60ce`, `2f79f1086a21596294a499daff80af3d15513f33`, `a88de22363147701f75ed83d1c298fe36f5d94a2`.
- Added shared `engine.agents.errors.RunPausedForApproval`; worker client and durable OpenManus tool loop now share and preserve the pause control-flow signal. Approval pause no longer gets converted to a generic tool failure observation before reaching WorkerRuntime.
- Read-only Supabase snapshot for canonical ref `uunfgimtokhucegqbpce`: 59 public tables, 59 RLS-enabled, 59 policies, 46 public routines, 42 applied migrations. Security advisor reports leaked-password protection disabled.
- Migration ledger has two applied versions named `moreai_workspace_file_cas_versioning` (`20261111140238`, `20261111140255`); history needs reconciliation without destructive reset.
- No tests, lint, typecheck, build, worker/provider runtime, browser QA, migration apply, data writes or deployment validation were performed. Approval lifecycle acceptance and all phase completion gates remain open.
- Detailed report: `PHASE-04-09-CONTINUATION-20261112.md`.


## 2026-11-12 — Customer API duplicate-route reconciliation
- Removed duplicate FastAPI route registrations for Customer wallet, ledger, usage, entitlements and quotas; retained the later implementations with timezone-aware cursor validation and global/user quota visibility.
- Source commit: `21201caaec53be5b80bdc5e3e2ec07c802d54289`.
- Report: [PHASE-04-06-07-08-09-CUSTOMER-ROUTE-RECONCILIATION-20261112.md](./PHASE-04-06-07-08-09-CUSTOMER-ROUTE-RECONCILIATION-20261112.md).
- No tests, lint, typecheck, build, runtime, staging, migration or deployment were run. This is not phase acceptance.
- Read-only Supabase inventory found no dedicated EduTech/course/lesson/progress/certificate tables among the inspected public tables; EduTech requires a product-approved data model before real persistence endpoints can be implemented.
- Phase 04, 06, 07, 08 and 09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.


## 2026-11-12 — Worker lease heartbeat interval correction
- `apps/worker/app/runtime.py` now renews leases at `max(1s, min(30s, lease_seconds / 3))`, avoiding a fixed 30-second heartbeat that could exceed short configured leases.
- Source commit: `5dcfda51dfa69b4c321348959ff00e58cf2585e0`.
- Report: [PHASE-04-07-WORKER-LEASE-HEARTBEAT-CORRECTION-20261112.md](./PHASE-04-07-WORKER-LEASE-HEARTBEAT-CORRECTION-20261112.md).
- No tests, build, runtime, staging, migration or deployment run; no phase acceptance is claimed.
- Phase 04, 06, 07, 08 and 09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.


## 2026-11-12 direct-main Customer workspace integration increment

- Added `apps/api/app/routers/workspaces.py` with authenticated Customer endpoints:
  - `GET /api/v1/customer/workspaces` — active owned and active member workspaces.
  - `POST /api/v1/customer/workspaces` — create a workspace for the authenticated user.
  - `GET /api/v1/customer/workspaces/{workspace_id}/files` — owner/member-scoped file metadata.
  - `GET /api/v1/customer/workspaces/{workspace_id}/files/{file_id}/versions` — owner/member-scoped immutable version metadata.
- Registered the router in the existing FastAPI application; no second API service or frontend shell was introduced.
- Added forward-only migration `20261112100000_moreai_workspace_file_version_history.sql`. A database trigger archives the previous committed file metadata whenever the CAS-controlled file version increments. Object bytes remain in private Storage; no content or signed URL is exposed by the history endpoint.
- Workspace access is checked against active workspace ownership or active membership. Non-members receive a not-found response to avoid workspace enumeration.
- The migration is source-only and has NOT been applied to Supabase. No tests, lint, typecheck, build, runtime call, staging, browser QA, or deployment was run, as instructed. No phase acceptance is claimed.
- Remaining: SWE file read/write/delete/restore orchestration; Storage bucket lifecycle; API contracts for all remaining customer domains; UI binding for Workspace/Files; complete OpenManus Flow/server/session parity; durable approval/retry/recovery acceptance.



## 2026-11-12 workspace restore and Customer Files integration continuation

- Added the canonical `workspace_restore_version` OpenManus tool contract. It is registered only when the persistent workspace adapter is configured.
- Restore reads an immutable prior version from private Storage, validates byte length and SHA-256, reserves a new write through the worker lease-fenced CAS RPC, uploads to the newly reserved object path, and commits the restored bytes as a NEW version. Historical objects are never overwritten.
- Added `workspace_restore_version` to the default-deny high-risk approval policy. Customer approval API accepts this exact tool key. Added a forward-only Supabase migration to extend the approval RPC/check allowlist. This migration is NOT applied.
- Added Customer workspace file signed-download API. It verifies active workspace owner/member access, resolves current or historical metadata, checks the configured private Storage bucket, and issues a 60-second signed URL. The workspace file and history queries are workspace-scoped so active members can access shared files.
- Added typed Customer workspace API methods in `lib/api/client.ts`; connected the existing Files view to list workspace files and obtain signed downloads. Existing artifact listing remains intact.
- No tests, lint, typecheck, build, browser verification, Supabase migration application, staging, or deployment were run per explicit instruction. These source changes are not acceptance evidence.
- Remaining Phase 04: complete workspace CRUD semantics, upstream Flow/server/session behavioral parity, browser egress/supervisor, sandbox gating and capability-map closure. Phase 07 remains open for runtime recovery/approval continuation acceptance. Phase 08 remains open for full provider/tool/agent/memory parity. Phase 09 remains open for remaining Customer screens and domain APIs.


## 2026-11-12 Supabase migration and Customer EduTech progress integration

- Applied to canonical Supabase project `uunfgimtokhucegqbpce`:
  - `moreai_workspace_file_version_history` — immutable version metadata, server-only RLS, archive trigger.
  - `moreai_workspace_restore_approval_key` — extends approval constraint and request RPC allowlist for `workspace_restore_version`.
  - `moreai_customer_learning_progress` — per-user/module/lesson completion state and atomic service-role RPC.
- Supabase migration history now records all three versions. Database verification confirms workspace history table/trigger/function, approval RPC key, learning progress table/RPC, RLS, service-role grants and private `moreai-artifacts` bucket.
- Added `apps/api/app/routers/learning.py` with authenticated Customer GET/PUT progress endpoints, registered in FastAPI.
- Added typed `learningApi` methods and connected the existing EduTech module lesson completion controls to persisted progress. Existing layout and visual styling are retained; only persistence/loading behavior changed.
- New files/changes: `supabase/migrations/20261112130000_moreai_customer_learning_progress.sql`, `apps/api/app/routers/learning.py`, `apps/api/app/main.py`, `lib/api/client.ts`, `components/views/edutech-view.tsx`.
- No app test suite, lint, typecheck, build, browser E2E, staging or deployment was run. Database schema/migration verification was run directly against Supabase. UI visual regression screenshots are therefore not claimed.
- Remaining Phase 04/07/08/06/09 work is still open; no phase is declared complete.


## Focused OpenManus ↔ Customer integration audit (2026-11-12)

Scope is restricted to the Customer application and OpenManus backend integration. Network gateway, Wi-Fi, Captive Portal, and partner network features are explicitly deferred until the OpenManus integration gate is closed.

### Confirmed integration surfaces from source inspection

- The pinned upstream snapshot is present at `vendor/openmanusweb`; the source manifest is retained at `docs/implementation/openmanusweb-source-manifest.json`. This confirms source provenance/copy only, not production parity.
- Existing Customer chat enqueue uses `moreai_enqueue_chat_run` to persist user message + durable run atomically; the worker dispatcher resolves an allowlisted runtime.
- Manus tool loop, planning adapter, model router/provider adapter, credit/quota accounting, conversation memory adapter, workspace/file tools, run checkpoints/events, approval flow, and outbox publisher exist as production integration seams.
- Customer APIs expose conversations, run status/steps/events/stream/cancel, workspace files/version/download/restore approval, artifacts, catalog, notifications, learning progress and other account domains.
- Existing Customer UI components and typed API client are retained; no upstream frontend was mounted.

### Blocking gaps — integration is NOT full

1. Upstream `app/web` server behavior has not yet been reconciled endpoint-by-endpoint into FastAPI. Existing SSE/run APIs cover part of the surface, but server/session lifecycle, job/task management, log/thinking tracker, file/session parity and websocket behavior require a documented compatibility map and implementation/acceptance.
2. Workspace lifecycle remains partial: workspace list/create/rename and file list/download/history/restore exist, but full lifecycle (archive/delete semantics, membership management, file CRUD/rename/delete, conflict/version behavior and recovery) is not closed.
3. Runtime parity is partial. Production registry currently enables a subset of upstream tool adapters based on environment/configuration. Browser and sandbox adapters are intentionally disabled unless their isolated service/release gates are configured. A source catalog entry alone is not an executable adapter.
4. Agent/Flow parity is partial: Manus and durable planning are registered. Every upstream agent/flow behavior, planner/tool interaction, prompt/schema contract and server-exposed workflow must be mapped and reconciled; process-global upstream plan/log/session behavior must remain replaced by durable state.
5. RAG/vector retrieval and knowledge ingestion/retrieval lifecycle have not been proven end-to-end. Conversation history memory exists; that is not equivalent to full RAG/memory parity.
6. Model routing and accounting adapters exist, but provider/model configuration, fallback behavior, stream accounting, interruption reconciliation, entitlement/quota and idempotency need runtime proof against actual enabled configuration.
7. Customer UI domain coverage is not proof of complete integration: some catalogs/content remain static and gateway-dependent screens are explicitly outside the current scope.

### Verification boundary

This is a source-level audit only. No tests, typecheck, build, browser E2E, staging, provider calls, or deployment were run. Do not mark Phase 04/07/08/06/09 complete on the basis of source presence or GitHub commits.

### Required next order

Phase 04: produce endpoint/capability parity matrix from the pinned upstream tree; finish durable server/session/Flow and workspace lifecycle; complete browser/sandbox isolation and egress gate. Then Phase 07 → Phase 08 → Phase 06 → Phase 09. No gateway-network integration before these gates.


## Active implementation increment — Customer OpenManus workspace lifecycle (2026-11-12)

- Added owner-only soft archive endpoint `POST /api/v1/customer/workspaces/{workspace_id}/archive`.
- Archive is blocked with HTTP 409 while workspace has queued, running, or waiting-approval agent runs. No hard delete is performed; workspace file version history and audit records remain intact.
- Added typed `customerWorkspaceApi.archive()` method to the existing Customer API client.
- Commits: `70101b310847040f6af9be75f2846bd2a55b4cec` (FastAPI) and `e2af2140438ab7c20aa2848e3c0107f33b8feee8` (typed client).
- This closes only the soft-archive slice of workspace lifecycle. It does not close Phase 04 or imply UI exposure; no existing UI file was changed.


## Active implementation increment — Customer workspace membership lifecycle (2026-11-12)

- Added owner-authorized `GET /api/v1/customer/workspaces/{workspace_id}/members` for invited, active, and suspended memberships.
- Added owner-authorized `DELETE /api/v1/customer/workspaces/{workspace_id}/members/{member_id}` as a soft revocation (`status=removed`); it refuses self-removal of the workspace owner and preserves workspace files/version history.
- Added typed Customer API client methods `workspaceApi.members()` and `workspaceApi.removeMember()`.
- Commits: `8705c19ea6b0e0993d1cc46a049c5171952e2089` (FastAPI), `ca68fc75e6b1f275e4c99fa9dedbda967b7dbb03` (typed client).
- This advances workspace membership lifecycle but does not yet implement invitation creation/acceptance, role assignment, file CRUD, or UI management. Phase 04 remains active.


## Active implementation increment — Workspace durable run/session listing (2026-11-12)

- Added `GET /api/v1/customer/workspaces/{workspace_id}/runs?limit=50`, validating limit 1–100 and workspace membership before reading.
- Run visibility is additionally constrained to the authenticated caller's `user_id`; shared workspace members cannot enumerate another member's private run records.
- Returns persisted run lifecycle metadata only (status, attempt bounds, timestamps, heartbeat, cancellation request, checkpoint key); prompt/input/output/tool payloads are not exposed by this endpoint.
- Added typed `workspaceApi.runs(workspaceId, limit)`.
- Commits: `0cb9a0bc3c288315184dc8866fdcf91f619caa89` (FastAPI), `5d123d879f387f4177f26b1957b5fe35d9053e33` (typed client).
- This is a read-side workspace/session integration seam; it does not claim parity with upstream server-side session creation, websocket, logs, thinking tracker, or Flow lifecycle. Phase 04 remains active.


## Active implementation increment — Conversation session parity (2026-11-12)

- Added `GET /api/v1/conversations/{conversation_id}/sessions?limit=50` to expose durable OpenManus run sessions attached to an owned Customer conversation.
- Endpoint validates conversation ownership before querying; filters run rows by both conversation_id and authenticated user_id; returns lifecycle/checkpoint metadata only and excludes private input/output/tool state.
- Added typed `conversationSessions(conversationId, limit)` to the existing Customer API client.
- Commits: `0d92d72980c979589bcce4cf2e895b69b8fa902d` (FastAPI), `3628d366256f47e3c28a4e258d42de7c1731c5f1` (typed client).
- This adds a conversation-scoped session read contract; it does not implement upstream in-memory server session creation, WebSocket semantics, Flow state transitions, or session mutation parity. Phase 04 remains active.
