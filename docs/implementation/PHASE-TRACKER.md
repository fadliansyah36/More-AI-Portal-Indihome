# MoreAI Implementation Phase Tracker

Updated: 2026-11-13

Implementation is proceeding directly on `main`. In this Phase 09 continuation, additive Supabase migrations were applied to the canonical project; no tests, build, lint, typecheck, browser/API verification, staging or application deployment were run.

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| 00 | Repository baseline & UI freeze | REVALIDATED — current UI build/lint/server/browser smoke PASS | [Phase 00 run 42965739011](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/42965739011): lint 0 errors, build/server/browser PASS at 360/390/768/1024/1440 px; 3 existing image optimization warnings |
| 01 | Upstream source pin & provenance | COMPLETE | `dev_web_app` @ `3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f` |
| 02 | Monorepo backend workspace foundation | COMPLETE — foundation | `apps/api`, `apps/worker`, `engine`, `packages` |
| 03 | Complete upstream source copy | COMPLETE — hash verified | 111/111 matching Git blob SHA in `vendor/openmanusweb/` |
| 04 | Full backend integration & security hardening | IN PROGRESS — Phase 04A now includes dependency-output handoff, manifest/partial-step crash recovery, allowlisted per-step agent selection, durable logs/thinking/progress projections and authenticated replayable WebSocket envelopes. Phase 04B now includes lease-fenced create/edit/delete/rename/restore-deleted operations, version history and include_deleted listing; migrations 20261112073357 and 20261112073831 are applied. Phase 04C now includes private worker-to-supervisor transport, startup readiness gate, digest-pinned browser image and Docker acceptance for IPv4/IPv6, proxy, redirect, DNS rebinding and download denial; Docker workflow still requires a final green run and production deployment acceptance remains outstanding | Sandbox policy tests [run 43170133933](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43170133933) PASS incl. proxy-readiness fail-closed tests; no deployed supervisor proof |
| 05 | Supabase schema reconciliation | COMPLETE — additive forward-only migrations; five server-only RLS policies added explicitly; no reset/destructive DDL | Phase 07A migrations plus `moreai_explicit_server_only_rls_denials`; policy catalog verified for all five tables; leaked-password protection remains open |
| 06 | FastAPI core & OpenAPI contract | IN PROGRESS — OpenAPI bearer JWT security and X-Correlation-ID are declared; Customer conversation/session, Agent Run, network, workspace, artifact, profile, wallet/ledger/usage/quota, learning, approval, notification and catalog JSON endpoints have explicit response models (streaming/binary routes remain transport-specific). Stable keyset cursors cover conversations/messages, Agent Runs, workspaces/files/versions/members/runs, network sessions, Knowledge Library, notifications, approvals, artifacts, ledger and usage. Source-level owner checks are present; live RLS/cross-tenant proof, universal idempotency and API/runtime acceptance remain open | [Continuation 2026-11-12 #2](./PHASE-08-06-09-CONTINUATION-20261112-2.md); Phase 09 source reports; no live verification or DB mutation |
| 07 | Worker & durable run lifecycle | IN PROGRESS — added bounded per-run wall-clock deadline (30–7200 seconds, default 1800), dispatch cancellation on timeout, idempotent `run.timed_out` event and retryable failed transition through durable finish RPC. Lease loss/cancel/restart handling retained | Worker contract suite [run 43170133933](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43170133933) PASS incl. timeout regression; crash/lease chaos and approval race acceptance remain open |
| 08 | LLM/tool/workflow/orchestration integration | IN PROGRESS — scanned PDF OCR via PDFium+Tesseract (English/Indonesian), image pixel limits, 45-second lease heartbeat with CAS fencing, owner-scoped retry/recovery, SHA-256 upload dedupe, enabled provider capability matrix, sandbox-gated SWE registry, nested policy-enforced `run` dispatch and durable `terminate` semantics implemented in source. Remaining upstream logger/exception/web-session/tracker parity, process-local provider/model circuit breaker now skips open routes and admits one half-open probe; MeteredGateway breaker wiring corrected; durable cross-worker breaker telemetry/state and gated browser/sandbox acceptance remain open | [Continuation 2026-11-12 #2](./PHASE-08-06-09-CONTINUATION-20261112-2.md); source commits `87cc926e`, `43f4dfd0`, `61299d59`, `82bb0ed8`, `ff82a201`, `6fa06a44`, `d9a86dee`, `fce7d22e`, `2cb36c23`, `c34c4964`, `bc525412`, `d55aed3a`, `78be756a`; migration unapplied; no runtime verification |
| 09 | Existing Frontend API Integration | IN PROGRESS — Customer authorization boundary tightened: Customer routes, notifications/preferences and agent/model/tool catalogues now require `customer_principal`; owner-scoped resource checks remain. Incremental keyset loading now covers artifacts across Results/Workflow/Code/Tasks/Research, Analyse Knowledge Library, Code Agent Run selector and existing notification/approval/workspace/conversation/run/ledger/usage collections. Approval decisions remain visible independently from Agent Run refresh failures; terminal cancellation responses are typed and UI copy reflects persisted outcomes. Network-session, workspace-file and artifact JSONB response contracts reconciled to Supabase nullability/types. Customer source scan remains ongoing; editor starter snippets are examples only. Workspace union listing uses a database-side owner/member union and stable `(updated_at, id)` keyset cursor. Customer file soft-delete/restore is exposed in Files UI and FastAPI with immutable version history. This increment adds workspace selection to new Chat conversations, persists `workspace_id` through conversation responses, rechecks `agent.run.create` before enqueue, and enforces role-aware `workspace.read`, `workspace.manage`, and `agent.run.read` checks in workspace routes. Workflow now exposes durable approval decision history; Files artifact pagination deduplicates pages and retains retry behavior. PRD review confirms no Customer workspace-member administration screen is required by section 6.1 and no invite API exists; the existing global Workflow screen fulfills the Customer task/run monitor requirement. Source-level auth/response-contract audit continues; no runtime or end-to-end proof. Gateway/OTP, EduTech catalog/video, media generation, payment settlement and support remain fail-closed pending official contracts/credentials. No tests, staging or runtime checks were run | [Auth/pagination/lifecycle continuation](./PHASE-09-CUSTOMER-AUTH-PAGINATION-LIFECYCLE-20261113.md) · [Conversation, pagination & data integrity](./PHASE-09-CUSTOMER-CONVERSATION-PAGINATION-DATA-INTEGRITY-20261113.md) · [Workspace/quota/run reconciliation](./PHASE-09-CUSTOMER-WORKSPACE-QUOTA-RUN-RECONCILIATION-20261113.md) · [Customer API inventory](./PHASE-09-CUSTOMER-ACTION-API-INVENTORY-20261113.md) · [Pagination/lifecycle hardening](./PHASE-09-CUSTOMER-PAGINATION-LIFECYCLE-CONTRACT-HARDENING-20261113.md) · [Workspace union & immutable file lifecycle](./PHASE-09-CUSTOMER-WORKSPACE-UNION-LIFECYCLE-20261113.md) · [Workspace context, RBAC & approval lifecycle](./PHASE-09-CUSTOMER-WORKSPACE-CONTEXT-RBAC-APPROVAL-20261113.md) |
| 10 | End-to-end integration verification | PARTIAL / NOT ACCEPTED — engine, worker (including timeout), sandbox-policy (including readiness), and FastAPI auth/tenant contract CI suites PASS; frontend baseline browser smoke previously PASS at five viewports. No authenticated Customer → real worker → real provider → Supabase E2E | [Phase 04 CI run 43170133933](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43170133933) all four jobs PASS; frontend baseline [43168282282](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43168282282) PASS; provider/runtime E2E outstanding |
| 11 | Integration release gate | BLOCKED — frontend lint/build/browser smoke now PASS, but not releasable: full upstream parity, deployed worker/sandbox, real-provider E2E, live RLS/cross-tenant proof, API OpenAPI compatibility and release security evidence remain outstanding | No production deployment or worker activation |

## Direct-main execution policy

Implementation is being performed directly on `main` as explicitly requested by the product owner. No new branch is created and the existing historical Phase 04 branch/PR is not used as the work target. Changes are committed in small, reviewable commits; production deployment and worker activation remain prohibited until Phase 11 passes.

## Current Phase 04 next work

- Customer workspace identity lifecycle increment: added owner-only `PATCH /api/v1/customer/workspaces/{workspace_id}` and typed `customerWorkspaceApi.list/create/rename`. Shared members remain read-only for workspace identity. The Customer Files surface now also exposes version-fenced soft delete and restore, exact path lookup before CAS upload, archived-version download and immutable restore copy. Workspace member/run API contracts are paged, but no dedicated Customer management screen currently exists. See [workspace union & immutable file lifecycle](./PHASE-09-CUSTOMER-WORKSPACE-UNION-LIFECYCLE-20261113.md).

1. Approval pause/resume and atomic single-use consumption are wired through the worker RPC gate and now protect workspace restore; continue closing edge cases and recovery behavior, then obtain runtime acceptance when authorized.
2. Integrate the sandbox supervisor with the OpenManus dispatcher. Keep Bash/Python/browser/file tools unavailable until the approval and supervisor gates are actually wired.
3. Complete browser isolation, DNS pinning/rebinding defenses, redirect revalidation, private/reserved IP rejection and controlled downloads. Workspace file version restore is now available through a gated worker tool; finish remaining workspace lifecycle and UX parity.
4. Close the source-to-target behavioral parity gaps in `openmanus-backend-capability-map.json`, including agent/flow lifecycle, tool schemas/handlers and upstream server/session/stream functions.
5. Maintain durable recovery, idempotency and tenant boundaries. Targeted CI tests are now authorized by the current request; use the latest run evidence and do not substitute unit tests for real provider/runtime acceptance.

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


## 2026-11-12 — Customer artifact API origin alignment
- Commit: `a28719068ccdefb05d0fed88b0975799a89358eb`.
- Customer Files artifact list/upload/signed-download methods now use the Customer API transport and honor `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL`, retaining the generic API origin fallback and shared Supabase Auth token handling.
- No UI redesign or direct browser Supabase data/Storage access was introduced.
- No tests, lint, typecheck, build, browser/API runtime, staging, migration or deployment were run. This is a source-level integration correction, not Phase 09 acceptance.
- Phase 04/07/08/06/09 remain IN PROGRESS; continue Phase 04 before the dependent phases.


## 2026-11-12 — Phase 04 workspace signed URL origin hardening
- Commit: `7405e5d6fb580b74c0c0d3bd07efe89024907255`.
- Workspace signed-download endpoint rejects absolute Storage URLs outside the configured HTTPS Supabase origin, URLs with userinfo, and malformed/protocol-relative relative paths. Existing authorization/private bucket checks remain.
- Report: `docs/implementation/PHASE-04-WORKSPACE-SIGNED-URL-ORIGIN-HARDENING-20261112.md`.
- Source-only change; no tests/lint/typecheck/build/runtime/browser QA/staging/migration/deployment. Phase 04 remains IN PROGRESS.


## 2026-11-12 — Workspace Storage path validation follow-up
- Commit: `53a2850bde142f4a4f01ea75e7470e13a7e9665f`.
- Fixed single-backslash rejection in relative signed paths and URL-encoded Storage bucket path segments for bucket lookup and signed URL creation.
- Report: `docs/implementation/PHASE-04-WORKSPACE-STORAGE-PATH-VALIDATION-20261112.md`.
- Source-only; no tests/lint/typecheck/build/runtime/browser QA/staging/migration/deployment. Phase 04 remains IN PROGRESS.


## 2026-11-12 — Browser Compose and isolation verifier alignment
- Updated legacy `apps/sandbox/docker-compose.browser.yml` to match the canonical isolated runtime contract in `apps/sandbox/compose.browser.yml` (service names, Dockerfile, proxy URL, network names and no published browser port).
- Updated `apps/sandbox/scripts/verify-browser-network-isolation.sh` to use the canonical Compose file and assert `browser_isolated` + `browser_egress`, including direct IPv4/IPv6 egress denial and proxy allowlist checks.
- Commits: `d3b02c3d16d10cbcbfe3bc5cc9b8252f80ad7b9f` (Compose compatibility), `85073f812422aaa29f0fc144ed2f8adbeebd5283` (verifier).
- Report: [PHASE-04-BROWSER-COMPOSE-VERIFIER-ALIGNMENT-20261112.md](./PHASE-04-BROWSER-COMPOSE-VERIFIER-ALIGNMENT-20261112.md).
- Source-only alignment. No Docker, shell verifier, tests, lint, typecheck, build, staging, migration or deployment was run; browser runtime remains inactive and no network acceptance is claimed.
- Phase 04/06/07/08/09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.


## 2026-11-12 — Phase 06 FastAPI error contract normalization
- Added a shared error response envelope for FastAPI `HTTPException`, request validation failures, and unexpected server exceptions.
- Stable error codes now cover common HTTP statuses; correlation IDs are included; authentication challenge headers are preserved; validation details omit submitted values.
- Source commit: `0d0ef242dd17713b8fa649ba74e3c988b6379353`.
- Report: [PHASE-06-FASTAPI-ERROR-CONTRACT-20261112.md](./PHASE-06-FASTAPI-ERROR-CONTRACT-20261112.md).
- No tests, lint, typecheck, OpenAPI generation, build, API runtime, staging, migration or deployment run. Endpoint-local JSONResponse paths and full route authorization reconciliation remain open.
- Phase 06 remains IN PROGRESS; Phase 08 and 09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.


## 2026-11-12 — Phase 08 tenant-scoped RAG implementation increment
- Added additive pgvector schema for owner/workspace scoped knowledge documents and chunks, with server-only RLS and a tenant-filtered semantic match RPC.
- Added worker embedding adapter, bounded text chunking/ingestion, semantic search, canonical tool definitions, durable runtime registration, and explicit retrieval/ingestion instructions.
- RAG tools are registered only when embedding endpoint/model configuration exists; 1536-dimensional vectors are required.
- Commits: `6e418112`, `2d08de80`, `31449379`, `0ed2225e`, `3730f40f`, `27e8d6cc`, `e625087f`.
- Report: [PHASE-08-TENANT-KNOWLEDGE-RAG-20261112.md](./PHASE-08-TENANT-KNOWLEDGE-RAG-20261112.md).
- This is source implementation only. Migration was not applied; provider calls, worker runtime, tests, lint, typecheck, build, staging and deployment were not run.
- Phase 08 remains IN PROGRESS; Phase 06 and Phase 09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.

- RAG follow-up hardening: owner/scope/content digest uniqueness, fail-closed duplicate ingestion, and personal + exact-workspace retrieval. Commits: `20f43316`, `b8b961f6`.


## 2026-11-12 Customer Knowledge Library integration increment

- Report: [PHASE-08-09-CUSTOMER-KNOWLEDGE-LIBRARY-20261112.md](./PHASE-08-09-CUSTOMER-KNOWLEDGE-LIBRARY-20261112.md).
- Added owner-scoped Customer knowledge document list/detail/soft-archive endpoints in `apps/api/app/routers/knowledge.py`; mounted through FastAPI.
- Added typed browser API client `lib/api/knowledge.ts`.
- Added authenticated Customer route `/customer/knowledge` and a Knowledge Library view with real API listing, status filters, title search, refresh and soft archive.
- Added navigation from the existing Files screen. Existing UI design and the single Customer application are retained.
- Source commits: `2f3e1cf6`, `135ceae4`, `5a10013d`, `7f4a54cd`, `5939b92d`, `8034aea4`, RAG operator fix `3b388d4c`, report `6c3978b2` and update `b63834d1`. Supabase migration version `20261112060109` applied.
- Applied the additive RAG migration to canonical Supabase after fixing the pgvector operator schema qualification; migration history version `20261112060109` is present. Schema inventory confirms both knowledge tables exist with RLS enabled. No document data, embedding provider, or worker was invoked.
- Per owner instruction, no tests, lint, typecheck, build, real API/browser request, staging, migration apply, provider call, worker activation or deployment was performed. This increment is source-committed but not runtime-verified and does not close Phase 08/09.


## 2026-11-12 continuation — workspace security, Customer Knowledge Library and CI repair

Baseline commit before this increment: `b06ffd183d6ce7ba28dd3491c65c36272d09af56`.
Current implementation commit at this report: `d5983ea19ac9ae6432ceaee51b40c3839a0e6c52`.

- Added `workspace_read_file` to the durable OpenManus tool catalog/runtime. It requires an existing workspace ID, validates membership through the server-side workspace RPC, enforces a private Storage bucket, rejects missing/invalid metadata, caps reads at 2 MB, accepts UTF-8 text only, and verifies byte count + SHA-256 against the persisted file version before returning content.
- Added policy/catalog/runtime wiring and tests for workspace reader default-deny behavior, integrity mismatch and path traversal. The tool is not enabled by default.
- Added `str_replace_editor` to the high-risk approval policy. Worker approval maps this upstream adapter key to the persisted canonical `file_edit` approval key, preserving the hash of the exact tool arguments; the edit handler cannot execute when approval is denied/expired/unavailable.
- Updated tests to match the complete MoreAI-extended tool inventory and the durable planning store contract. Updated the API contract test to assert the normalized error envelope and correlation ID.
- Fixed missing `BaseModel`/`Field` import in Customer routes and missing `Any` import in FastAPI main module, discovered by API CI.
- Refactored data-loading state transitions in existing views and moved analytics time capture to API response completion to remove render/effect lint violations. No component hierarchy, spacing, colors, typography, or navigation design was intentionally changed.
- CI evidence: [Engine Contract Tests 43167699004](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43167699004) PASS; [Phase 04 Sandbox Security Tests 43167699075](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43167699075) all four jobs PASS (API contract, worker contract, engine policy, sandbox policy). [Phase 00 baseline 43167699018](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43167699018) is pending final lint/build/browser screenshot results at report time.
- Supabase RAG migration version `20261112060109` remains applied to canonical project; tables `knowledge_documents` and `knowledge_chunks` were previously confirmed with RLS enabled. No document data was inserted.
- No production deploy, worker activation, real provider request, or authenticated browser-to-provider end-to-end session was performed. Phase 10 remains partial and Phase 11 remains blocked.


## 2026-11-12 Phase 00 frontend evidence and visual preservation note

- Latest frontend baseline: [run 43168282282](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43168282282) PASS — lint, build, server start and browser smoke; responsive screenshots were captured at 360, 390, 768, 1024 and 1440 px.
- The current unauthenticated root screenshot shows the MoreAI splash/entry screen. A historical run from 2026-11-11 shows the old dashboard with a seeded-looking “Andi Pratama” identity and “Partner ISP 100M” badge. The difference is between historical commits and is not caused by this increment's data-loading refactors; no root route, splash, navigation or layout file was edited in this increment. Keep the current authenticated/splash behavior; do not restore demo-looking dashboard data as a baseline.
- The views changed in this increment only adjust when data loads and when loading/error state is set; no intentional visual design change. Current screenshots are stored as the Phase 00 workflow artifact for run 43168282282.


## 2026-11-12 continuation — bounded run timeout and browser readiness

- Added `MOREAI_RUN_TIMEOUT_SECONDS` to WorkerSettings and `.env.example`, bounded to 30–7200 seconds (default 1800).
- Worker dispatch now races execution against configured run timeout, durable cancellation and lease-loss signals. On timeout it cancels the dispatch task, appends idempotent `run.timed_out`, and calls the existing durable finish RPC with `agent_run_timeout` and retry delay; database attempt/max-attempt policy remains authoritative.
- Added worker tests for dispatch cancellation, timeout event and retryable terminal transition.
- Extracted browser readiness into a stdlib-only helper and changed supervisor readiness to require a reachable configured proxy in addition to the private egress-enforced configuration. This prevents a false-positive readiness response when the egress proxy is down.
- Added browser readiness tests for both reachable and unavailable proxy cases.
- CI [Phase 04 run 43170133933](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43170133933): worker-contract, API-contract, engine-policy and sandbox-policy jobs all PASS.
- This is not production deployment proof: no browser supervisor/proxy containers were started in a controlled host/network environment, no network-isolation acceptance script was run, and no worker runtime was activated.


## 2026-11-12 — Phase 04 PlanningFlow dependency handoff and browser acceptance probe

- `engine/agents/planning_runtime.py` now forwards the persisted outputs of every declared dependency into the dependent step's execution prompt, together with explicit dependency indexes. It only constructs this context after verifying dependencies are already completed; prior-step ordering and persisted recovery remain authoritative. The serialized dependency context is bounded to 20 KB.
- Extended `engine/tests/test_planning_runtime.py` to assert dependency indexes and predecessor output are present in the next step's prompt.
- `apps/sandbox/Dockerfile.browser` now installs `curl`, which the existing `verify-browser-network-isolation.sh` acceptance script requires inside the browser container to prove successful allowlisted HTTPS proxy egress. Without this package, the verifier could never pass its positive proxy-path check even when the proxy worked.
- Commits: `1cd00cc5f854c463f76d0aee11dd58be18ac7010` (Flow runtime), `07f225fc2fe5717f55be8596f38f73438483f702` (Flow regression test), `ddedb1ff55ae7cbadbf8006f4eeaef5b75d95cc2` (browser image probe dependency).
- CI: Engine Contract Tests [43171904754](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43171904754) PASS; Phase 04 Sandbox Security Tests [43171904694](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43171904694) PASS for the Flow runtime + prior sandbox image. The Dockerfile follow-up run [43171983972](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43171983972) PASS: sandbox-policy, engine-policy, api-contract and worker-contract all green.
- No live browser containers, direct-egress probe, allowlist egress acceptance, supervisor-to-worker deployment, authenticated OpenManus E2E, provider call, or staging deployment has been performed. This is an incremental fix, not Phase 04 acceptance.
- Remaining Phase 04 blockers: full upstream server/session/log/thinking/WebSocket parity; workspace file create/upload/rename/delete lifecycle and invitation/acceptance semantics; durable Flow resume and richer multi-agent/flow-factory parity; worker-to-supervisor private service connectivity; real Docker IPv4/IPv6 isolation and proxy egress acceptance. Continue Phase 04 before Phase 07 and Phase 08.


- PlanningFlow follow-up correctness fix: dependency outputs are now tracked from the active execution loop (including recovered completed steps), not from the initial persisted snapshot. This ensures the dependent step receives the actual predecessor result. CI [Engine Contract Tests 43172280306](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43172280306) and [Phase 04 Sandbox Security Tests 43172280282](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43172280282) PASS. Commits `be8586c4b19fdbded8991c07e9b5b5994a9595cb`, `29ddce091d2b504bd6f3b0f3d8f18049cfe0a171`.


## 2026-11-12 — Phase 04A/04B implementation and Phase 04C Docker acceptance

- PlanningFlow now carries predecessor outputs into dependent steps, persists complete bounded manifests, repairs partial step-row creation after a crash, reconstructs a missing manifest from persisted step inputs, and dispatches each step through an explicit allowlisted `agent_key`.
- FastAPI run activity now includes owner-scoped `/logs`, `/thinking`, and `/progress` projections over durable event/step records. An authenticated WebSocket route replays persisted activity using status/log/thinking/result envelopes; sensitive prompts, tool arguments and observations are not included in activity projections.
- SWE workspace tool now supports create/edit/delete/rename/restore-deleted. Delete is a soft tombstone with a retained version record. Rename increments version and is fenced by the active worker lease. Restore clears the tombstone and increments version. File list supports `include_deleted=true`.
- Supabase migrations applied to canonical project `uunfgimtokhucegqbpce`: `20261112073357_moreai_workspace_delete_rename_lease_fencing` and `20261112073831_moreai_workspace_restore_deleted_file`. Verification confirms `deleted_at`, invoker-secured RPCs, service_role execute access and no authenticated execute grant. Security advisor returned no new finding attributable to these functions; pre-existing advisor findings remain separately tracked.
- Browser supervisor uses a private-only HTTP exception for exact `browser-supervisor:8080` transport, requires authenticated `/ready` and a live enforced proxy. Worker startup fails closed if browser is enabled but supervisor/proxy readiness fails. Browser Docker image is digest-pinned and Playwright binaries are accessible to the non-root runtime user.
- Docker acceptance workflow now builds browser/proxy and worker images, attaches a worker client container to the internal browser network, and checks IPv4/IPv6 direct-egress denial, authenticated proxy readiness, positive allowlisted HTTPS, Playwright navigation, unauthorized redirect denial, download denial while scanning is disabled, DNS public-to-loopback rebinding rejection, private/metadata/unauthorized target denial, and non-privileged/non-host network mode.
- Latest full Phase 04 workflow: [run 43178037719](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43178037719) — running at report time. Prior worker-contract and engine-policy suites have passed, but no Docker acceptance result is claimed until this run completes.
- No production/staging worker deployment or browser activation. Download scanning is not implemented; downloads remain denied by default. The Docker test proves the container topology/client contract on GitHub-hosted Docker, not the target production platform's network connectivity.
- Phase 04 remains IN PROGRESS. Phase 07 and Phase 08 remain downstream and must not start until Phase 04 acceptance is signed off. Phase 06/09, Phase 10 authenticated Customer-to-provider E2E and Phase 11 release gate remain open.


## 2026-11-12 — Customer registration/login hardening (incremental)

- Registration form removes WhatsApp phone number and submits only normalized email, full name and password. Password policy is 12–128 characters with upper/lowercase, digit and symbol checks; duplicate submissions are disabled while in flight.
- Login form is email-only. Supabase Auth errors are mapped to safe user-facing messages, and session absence is no longer represented as successful registration/login.
- Applied and recorded Supabase migration `20261112084047_moreai_auth_profile_provisioning_and_owner_update`: creates an auth.users insert trigger in non-exposed `auth_private` to provision profiles, adds owner-scoped profile UPDATE RLS, and backfills existing Auth users without overwriting existing profile rows.
- Added API mutation Origin and Fetch Metadata checks, plus baseline browser/API security response headers. Tests were added for cross-site mutation rejection.
- Security Advisor currently reports `auth_leaked_password_protection` WARN. Enable leaked-password protection and tune Auth rate limits/CAPTCHA in Supabase Dashboard.
- **External configuration gate:** connected Supabase DB tools cannot update hosted Auth provider settings. Project owner must switch Authentication → Sign In / Providers → Email → Confirm email OFF. Until this is saved, signup may return a user with a null session and immediate login remains blocked by the provider setting. No claim of successful real signup/login E2E is made.
- API unit tests passed: 27 passed (run [43185507782](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43185507782)); worker tests also passed. Phase 04 API/worker/engine/sandbox policy jobs passed in [run 43185332570](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43185332570). The responsive browser baseline and new register/login smoke assertions are still running in [run 43185507782](https://github.com/fadliansyah36/More-AI-Portal-Indihome/actions/runs/43185507782).
- Detailed implementation and configuration steps: [AUTH-REGISTER-LOGIN-SECURITY-20261112.md](AUTH-REGISTER-LOGIN-SECURITY-20261112.md).


## 2026-11-12 Customer API runtime recovery (priority scope)

- Confirmed production root cause behind Customer Tasks `Failed to fetch`: configured FastAPI origin `https://more-ai-api-more-ai.vercel.app` returns HTTP 500 `FUNCTION_INVOCATION_FAILED` for both `/health` and `/ready`. This is not a missing frontend API URL; Vercel project env includes `NEXT_PUBLIC_MOREAI_API_URL`, and backend CORS env includes `https://moreai.web.id`.
- API Vercel build evidence shows Python metadata under `apps/api/pyproject.toml` but deployment entrypoint `.` at monorepo root, while the function entrypoint is nested under `apps/api/api/index.py` and imports `app.main` plus root `engine`. Updated the API function entrypoint to explicitly resolve both API workspace and monorepo root before importing FastAPI; aligned Vercel API project root directory to `apps/api` and enabled source files outside root for engine imports.
- API and worker unit tests passed on commit `b9426254f8fb8b143696edec36a46d0666e6b920`; frontend lint/build passed. Follow-up entrypoint hardening commit `17453150da788481500b36c0683e4e7db750aab6` is committed, but not yet deployed or runtime-verified.
- Vercel production redeployment was rejected with HTTP 402 `api-deployments-free-per-day`; do not claim runtime recovery. See [PHASE-09-CUSTOMER-API-PRODUCTION-RECOVERY-20261112.md](./PHASE-09-CUSTOMER-API-PRODUCTION-RECOVERY-20261112.md).
- Corrected Customer API contract drift: list/get/steps/stream now use `/api/v1/customer/agent-runs/*`; added authenticated Customer cancel endpoint and a route-registration regression test. The existing Tasks “Tambah Tugas” action now routes into the real authenticated Chat → FastAPI → durable Agent Run flow without creating local/mock task rows. Latest code commit `7784431a11fda14ce82fb8bc3bf8607a43d4199e`; API/worker/browser baseline CI run `43189842274` is in progress.

- `MOREAI_AGENT_EXECUTION_ENABLED=false` remains intentional until durable worker/provider/credit gates are live. Do not enable merely to hide a queue that has no active worker.

## Next focused work

1. Restore FastAPI runtime deployment and prove `/health` and `/ready` from production.
2. Verify every existing Customer screen against the real FastAPI route/schema and Supabase-backed records; fix mismatches without changing visual design.
3. Complete Customer chat/run lifecycle only after worker/provider readiness; prove enqueue → worker → engine → persistence → events → UI.
4. Keep Phase 09 IN PROGRESS and Phase 10/11 NOT ACCEPTED until authenticated production E2E is evidenced.


## 2026-11-12 direct-main Customer Workspace continuation

- Report: [CUSTOMER-WORKSPACE-DIRECT-MAIN-CONTINUATION-20261112.md](./CUSTOMER-WORKSPACE-DIRECT-MAIN-CONTINUATION-20261112.md).
- Repository HEAD at reconciliation: `e309fd093cde6e34b98a69d235098f6cebada833`.
- Direct production FastAPI deployment from that exact `main` SHA is READY: deployment `dpl_5fpYzDFuqcB9Xzt4nNnj2UhHHykk`, alias `more-ai-api.vercel.app`, root `apps/api`, source files outside root enabled. This is deployment/build status only; no runtime endpoint was invoked.
- Existing frontend API origin is configured as `https://more-ai-api-more-ai.vercel.app`; API CORS origins include the production frontend domains.
- A direct production frontend deployment from the same SHA was rejected by Vercel with HTTP 402 `api-deployments-free-per-day` and retry-after 86400 seconds. Current frontend production therefore still serves an earlier commit.
- API runtime keeps `MOREAI_AGENT_EXECUTION_ENABLED=false`. Worker source and Docker profile exist, but no deployed always-on worker service was found in the connected Vercel project inventory. Provider routing, worker secrets/configuration, credit conversion, wallet currency, entitlement/quota keys and runtime health are not established by this deployment.
- No real endpoint/browser/provider/worker/SQL/E2E test, staging deployment, migration or worker activation was performed.
- Phases 04, 06, 07, 08 and 09 remain IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED. See continuation report for dependency-ordered next actions.


## 2026-11-12 — Phase 07 worker poll recovery increment

- Report: [PHASE-07-WORKER-POLL-RECOVERY-20261112.md](./PHASE-07-WORKER-POLL-RECOVERY-20261112.md).
- Updated `apps/worker/app/main.py`: transient errors during steady-state run claiming/polling no longer terminate the long-lived worker process; they are logged and retried with bounded exponential backoff (maximum 30 seconds).
- Startup configuration remains fail-fast. This does not activate or deploy the worker and does not enable agent execution.
- Commit: `58c921054274722797967276363d442b6939189f`; report commit: `5bce1b1e32fa79df336ca3b2b64108081eef2326`.
- No tests, lint, typecheck, build, runtime probe or deployment were run, following the current instruction.
- Phase 07 remains IN PROGRESS; Phase 04 backend parity remains the upstream dependency. Continue Phase 04 before declaring Phase 07/08/06/09 complete.


## 2026-11-12 — Customer Profile identity and greeting integration

- Report: [CUSTOMER-PROFILE-IDENTITY-INTEGRATION-20261112.md](./CUSTOMER-PROFILE-IDENTITY-INTEGRATION-20261112.md).
- Profile no longer couples identity loading to notification preference loading; an unrelated notification API failure cannot reject the Profile identity request.
- FastAPI authenticated principal now exposes only a normalized \`display_name\` derived from Supabase Auth \`user_metadata.full_name\` / \`name\`, in addition to id/email. Raw Auth metadata is not returned.
- Customer Home now uses the shared typed profile API and resolves registered name in this order: profile display_name → Auth metadata display_name → email local-part → existing supplied identity. Transient API errors no longer overwrite a known identity with a generic placeholder.
- Source commits: \`3ea69daed8caf10322482042d9cd928de9a1a31f\`, \`b9ebfd71456359e5d25532c6d58ff4f07039ccaa\`, \`27966787443cd4ec2e1de4ab6e95ed40a627bc7c\`, \`f18280ac70b57e9a730ea51f0446bef9bf5dd33f\`; report commit: \`54f8d314df93d757d501011d911e4d5a07e7ed1c\`.
- No tests, lint, typecheck, build, runtime API/browser call, migration, staging or deployment were performed per instruction. Runtime Profile availability remains unverified.
- Phase 06/09 remain IN PROGRESS. Phase 08 remains IN PROGRESS; this is an identity integration increment, not full phase acceptance.


## 2026-11-12 continuation — capability routing, RAG citations, profile contract and wallet data

- Current report: [PHASE-08-06-09-CONTINUATION-20261112.md](./PHASE-08-06-09-CONTINUATION-20261112.md).
- Model route matching now accepts required capability sets and normalizes provider/model capability aliases; tool-enabled Manus turns require `tool_calling`.
- RAG chunk IDs/document IDs survive the tool boundary and are attached to durable final output from checkpointed retrieval observations; Customer Chat displays source titles and stable source markers.
- Profile API error paths now use the common structured error envelope; browser API client parses detail, code and correlation ID.
- Customer Wallet screen now consumes actual authenticated wallet/ledger endpoints and no longer shows seeded sample transactions, a fabricated balance, or a fabricated token conversion.
- No tests, lint, typecheck, build, API calls, provider calls, database changes, staging or deployment were run, per owner instruction. These are code increments, not phase acceptance.
- Latest commits: `681617addb946c585bc22a5fb2c72f45e306069c`, `5967ab698eae58de768f38b03dcc285bcfbaab48`, `34bf606ba6bbf3661529e5a33ce6658ed1ae6d36`, `78699331b0b440f436a64242ca11f87859bd1818`, `e59680dfc2ead0d860d7b41df3794395eec15362`, `c7df5ee843709e4091c38a5c063b10969f67917e`, `bb25ef3e4110c5c860bee72d63fb0a98361a19b2`, `98c100f55ee54f90c40c4a60906c1af96b658c1a`, `a5066ee6d7da66bf238620ce451d2e32c59fb9e2`, report `4b052696d21fb76a1f5e1ae920ba6805c6095183`.


## 2026-11-12 — Durable Customer Knowledge file upload and ingestion

- Native device file picker added to the existing Knowledge Library. PDF/JPEG/PNG/WEBP bytes go to FastAPI as multipart/form-data; no URL upload workflow is used.
- FastAPI validates customer principal, active workspace membership, MIME/signature, filename and 25 MiB limit, then stores bytes in a private Supabase Storage bucket.
- Worker claims knowledge jobs with database leases, extracts PDF pages, OCRs images with Tesseract, embeds page-aware chunks, and retries recoverable failures with bounded exponential backoff (maximum three attempts).
- RAG citation records preserve source page and normalized page-local character offsets; Chat shows page number with source marker.
- Migration `20261112170000_moreai_durable_knowledge_file_ingestion.sql` is committed only; it has not been applied. Worker dependencies/container and API changes have not been deployed.
- Report: [PHASE-08-KNOWLEDGE-FILE-INGESTION-20261112.md](./PHASE-08-KNOWLEDGE-FILE-INGESTION-20261112.md).
- No tests, lint, typecheck, build, API calls, uploads, OCR run, DB mutation, staging or deployment were performed. Phase 08 and Phase 09 remain IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.


## 2026-11-13 direct-main Customer integration increment

- Phase 09: Supabase Auth TOTP factor inventory/enrollment/challenge/verification/unenrollment is now connected in the existing Security Settings view. Local-only 2FA success toggles were removed.
- Removed fabricated device inventory and local pause/filter actions from Customer Device Access Control; it now clearly reports that a real partner/gateway device API is not yet connected.
- Removed fabricated captive Wi-Fi countdown, venue identity, throughput metrics, AI quota numbers and local extend/disconnect success actions. Unsupported operations remain disabled until a real gateway contract is available.
- Existing screen structure and styling were retained; no broad UI redesign.
- Report: [Phase 09 Customer Security, Device & Wi-Fi Correctness](./PHASE-09-CUSTOMER-SECURITY-DEVICE-WIFI-CORRECTNESS-20261113.md).
- Commits: `083bef75`, `0a0675c2`, `b0b54e37`, `477f590e`, `55138bc0`, `d7f7cd6f`.
- No tests, lint, typecheck, build, screenshots, browser/API probes, staging, deployment, provider calls or database mutations were run per instruction. Phase 09 remains IN PROGRESS; TOTP login-time challenge/AAL enforcement and real gateway APIs are outstanding.


## 2026-11-13 API error contract increment

- Phase 04/06 partial: FastAPI now distinguishes upstream HTTP timeouts (504 `upstream_timeout`) from upstream transport failures (503 `upstream_unavailable`). Unhandled exceptions emit correlation ID, route, method and exception class without logging raw exception text/tracebacks.
- OpenManus capability map now reflects this limited transport-level parity. Full upstream exception taxonomy and durable engine/worker log projections remain open.
- Source commit: `e76f7ccebeca21ee6b4ac0a57488eef547c8ceea`; capability map: `7ac60192b8e32d11f2a060edc1d62382a61801fd`.
- No tests or runtime checks were run per instruction.


## 2026-11-13 Create Studio integration increment

- Removed simulated Create Studio generation output, fake 50-point pricing and local-only clipboard result.
- Text-based Create Studio prompts now hand off to the existing authenticated Customer Chat/Agent Run flow. Image/video generation is explicitly unavailable until real runtime adapters are connected.
- Report: [Phase 09 Create Studio Agent Handoff](./PHASE-09-CREATE-STUDIO-AGENT-HANDOFF-20261113.md).
- Commit: `cf1f9f5c5a51e0f65a0bf85c1195cb869e36ae1a`.
- No tests/runtime/staging/deployment executed per instruction; Phase 09 remains IN PROGRESS.


## 2026-11-13 — concrete OpenManus ToolCall agent registration

- Inspected upstream concrete agent classes; ReActAgent is abstract, while ToolCallAgent is concrete. Registered ToolCallAgent as a distinct durable MoreAI runtime using the adapted upstream prompt and the existing policy-enforced, approval-gated tool adapters.
- Added `toolcall` to the Customer conversation request contract and runtime-backed agent catalog allowlist.
- Added migration `20261113100000_moreai_enable_toolcall_agent.sql` to allow `toolcall` in the service-role-only enqueue RPC while preserving ownership and idempotency behavior. Source committed only; NOT applied to Supabase.
- Capability map and report updated: [ToolCall agent registration](./PHASE-04-06-08-TOOLCALL-AGENT-REGISTRATION-20261113.md).
- Commits: worker `caf98089`, API `da1381b9`, catalog `53a658ec`, migration `ac369092`, capability map `1d72c3c2`, report `5002c851`.
- No tests, build, typecheck, runtime calls, migration apply, staging or deployment performed. Phase 04/06/07/08/09 remain IN PROGRESS.


## 2026-11-13 — Customer conversation and run keyset pagination

- Added a shared opaque cursor helper over stable `(created_at,id)` ordering with timezone-aware cursor validation.
- Customer conversation and agent-run list endpoints now support bounded `limit` and optional `cursor` while preserving the existing JSON array response. Next cursor is returned in `X-Next-Cursor`; CORS exposes it.
- Added typed `moreAiCustomerApiPage<T>` helper. Existing screens are not yet migrated to incremental loading; that remains Phase 09 work.
- Report: [Customer Keyset Pagination](./PHASE-06-CUSTOMER-KEYSET-PAGINATION-20261113.md).
- Commits: `8836057b`, `21d2b70d`, `9fd7414b`, `959e0729`, `262f6957`.
- No tests, lint, typecheck, build, runtime API calls, staging, migration apply or deployment were run. Phase 06 remains IN PROGRESS.


## 2026-11-13 — WebSocket replay cursor correction

- Corrected the Agent Run WebSocket initial replay batch to query only events with sequence strictly greater than the caller's cursor, in ascending order. This prevents replaying acknowledged events and skipping gaps on reconnect.
- Conversation session WebSocket delegates to the same run stream after validating conversation ownership and run association.
- Commit: `66a374c6`. Capability map and [WebSocket replay report](./PHASE-04-WEBSOCKET-REPLAY-CURSOR-20261113.md) updated.
- No tests, lint, typecheck, build, runtime API/browser calls, staging, migration apply or deployment performed. Phase 04 remains IN PROGRESS.


## 2026-11-13 — Conversation session keyset pagination

- Added bounded keyset pagination to `GET /api/v1/conversations/{conversation_id}/sessions`, retaining the existing `{items,count}` response and enforcing conversation/user ownership before listing.
- Uses the shared opaque cursor and emits `X-Next-Cursor` only when a further page exists. Commit `e93eea09`.
- Report: [Conversation Session Pagination](./PHASE-06-CONVERSATION-SESSION-PAGINATION-20261113.md). Customer screens still need Phase 09 incremental-loading integration.
- No tests, lint, typecheck, build, runtime API/browser calls, staging, migration apply or deployment. Phase 06 remains IN PROGRESS.


## 2026-11-13 — Phase 04 remote sandbox supervisor increment
- Branch: `main`; baseline `9ea16f90bccd406d4ea799ba091817c46168c8e2`; increment commits: `308c95b7e605ee5f8c92c5f3489704729ea47f62`, `338f1251dd841032d2ec20ab12475bd781524ac7`, `5521721fef7af1983dcf0365255f5eb680ca63fe`, `c63261a4c4071788b1d4044c0cbe3f1450ac6c3f`, `5a7df92bb239bebd9ae5f30bf3ac64525f365a11`, `897fe2f5aab51d05eec529676e51a7ab732177d8`, `fa822a601b25346a434e7460cb80efad791817a8`, `7af75ae9d47ea57c3edfe793c04ad26d1b9e5b02`, `60e701f514e46941c7e3e3e82110c8bea1bd1f27`.
- Added a separate authenticated FastAPI execution supervisor and image; worker now calls it over HTTPS or the exact private Compose endpoint rather than invoking Docker locally.
- Wired readiness preflight into worker startup and dispatcher; SWE requires the supervisor; sandbox tool invocations recheck readiness.
- Added run-scoped remote cancellation and documented private network / restricted Docker socket proxy prerequisites.
- Sandbox remains disabled unless both runtime and release-gate flags are explicitly enabled. No tests, lint, typecheck, build, Docker build, staging, deployment, migration or live probes were run.
- Report: `docs/implementation/PHASE-04-REMOTE-SANDBOX-SUPERVISOR-20261113.md`.
- Phase 04 remains IN PROGRESS; server/session parity, workspace lifecycle binding, browser download scanning and exception taxonomy remain open. Next: complete those Phase 04 areas, then Phase 06.

- Follow-up hardening: execution supervisor readiness now calls the configured Docker daemon/socket proxy and requires a successful server-version response; configuration-only readiness is not accepted. Commits: `2b3598a4c0f1e9c811044d670b14bb80d1aba285`, `068553a012b95412fd39a3e83d38b96684a74262`.


## 2026-11-13 — Phase 04 browser and execution topology hardening
- Fixed the undefined browser navigation variable and enforce the configured domain allowlist for initial navigation, every intercepted HTTPS subresource, and the final navigation URL. The CONNECT proxy remains the DNS/IP pinning boundary.
- Added a private execution Compose topology with an isolated supervisor and Docker socket proxy; the worker must join the internal network but never receives the Docker socket.
- Added a minimal non-root Python/Bash runner image definition. Both runner and socket-proxy images must be published/resolved to immutable SHA-256 digests before activation.
- Commits: `2c62bc79f808420926a7dc79206c72c52781e7b1`, `91fa8128462a72f5826061df5316cdf61fdf4285`, `7a681f504935a7c7278300849f627c6dcdbc2d4d`, `c3de455c0da2c06955dde3b3aea4e938fc8c1220`, `c507d6930f41f25ef463b8e4691ab6d2b60e11c7`.
- Report: [Phase 04 remote sandbox supervisor](./PHASE-04-REMOTE-SANDBOX-SUPERVISOR-20261113.md).
- No tests, lint, typecheck, build, Docker build, browser/API probes, staging, deployment, migration or Supabase mutation were run. Phase 04 remains IN PROGRESS; upstream server/session lifecycle, complete workspace-to-runner binding and exception taxonomy remain open.

- Follow-up cancellation hardening: Docker runner now records each container ID and requests daemon-side forced removal from the cleanup finalizer after timeout, cancellation, output-limit termination or normal completion. Commits: `b32cb13e97c855872f44b001b607b2b0d60452e7`, `2b45715f89f647d4194e1e76ecc5506b59a9db3b`. No Docker runtime was invoked.

- Phase 04 exception taxonomy increment: `AgentExecutionError` and conservative exception classifier added; dispatcher maps permission/capability/validation/timeout/internal faults to stable safe codes; worker persists only sanitized code and retryability metadata. Commits: `df7adb4e4635517e1d3d9e30be2e6643bc6c41bd`, `f389b12ad4a490b15588be0c5f044c6fd9c63569`, `a61c0eb130d69b3facdea0fc0bad2a0e258843ac`. Workspace file tools remain context-scoped, but no persistent filesystem mount is provided to Python/Bash runner; server/session parity and browser download scanning remain open. No runtime checks performed.

- Phase 04 lifecycle correction: dispatcher now preserves `RunPausedForApproval` so durable approval pauses reach the worker's pause handler; upstream timeout/transport/429/5xx failures receive explicit retryable taxonomy without leaking response bodies. Commits: `96388b5cbd9d898c35012240f307ba9fb976429d`, `bdaf4b2c3809acb2c22bc3d26e6ed63780e57b65`. No tests or runtime probes.

- Phase 04 browser download hardening: isolated browser context rejects downloads (`accept_downloads=False`), explicitly cancels download events and reports blocked download count. No download artifact persistence is enabled pending scanning/quarantine policy. Commit: `845b9e7d5ae5cff9676b06218324126fbaa6eca4`. Persistent workspace-to-Python/Bash filesystem bridge remains unimplemented; no runtime checks.


## 2026-11-13 — Phase 04 persistent workspace snapshot bridge
- Added a bounded copy-in/copy-out bridge between immutable Supabase workspace objects and the isolated Python/Bash runner. Snapshot is limited to 200 files / 2 MiB, membership and metadata are rechecked through the workspace RPC, and every object is size/SHA-256 verified.
- The runner materializes files only in disposable /tmp/workspace, has no host mounts/network, rejects symlinks and returns a bounded snapshot. Successful non-timeout runs commit changed/new files through worker-lease and version-fenced CAS RPCs; removals use the existing soft-delete RPC. Failed/timed-out runs discard changes.
- Workspace identity is now passed to bash/python_execute handlers from AgentRunContext; model tool arguments cannot choose the workspace. New-file writes are fenced against concurrent inserts and deleted paths require explicit restore.
- Write-back is per-file, not atomic across multiple files; partial commit can occur if a later file conflicts. This limitation and recovery expectations are documented.
- Report: [Phase 04 Persistent Workspace Snapshot Bridge](./PHASE-04-PERSISTENT-WORKSPACE-SNAPSHOT-BRIDGE-20261113.md).
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment, migration or Supabase live mutation were run. Sandbox remains disabled behind both explicit activation gates. Phase 04 remains IN PROGRESS.

- Runner output buffering was further bounded through temporary files on the runner's 16 MiB tmpfs, with only the first 64 KiB per stdout/stderr stream returned. Source fix: `b7db9fcec321457edcd50232d4645c493cbd5f63`; report includes the complete source commit list.


## 2026-11-13 — Phase 04 session lifecycle and atomic workspace commit
- Added conversation-scoped session cancellation with conversation + run ownership checks, delegated to durable cancellation RPC. WebSocket/SSE replay cursors and event query parameters are bounded to PostgreSQL bigint and malformed/negative values are rejected.
- Replaced per-file workspace metadata write-back with one atomic, lease-fenced PostgreSQL RPC transaction. Changed/new immutable Storage objects are uploaded first; a deterministic SHA-256 operation key makes commit retries idempotent. The RPC validates active workspace membership, private bucket, object existence, path safety, version preconditions, size limits and duplicates; updates and soft deletes commit together and existing version-history metadata is retained.
- Added migration `20261113120000_moreai_workspace_atomic_execution_commit.sql` (source committed only; not applied). Failed metadata transactions can leave unreferenced uploaded Storage objects; object garbage collection remains open.
- Report: [Phase 04 Persistent Workspace Snapshot Bridge](./PHASE-04-PERSISTENT-WORKSPACE-SNAPSHOT-BRIDGE-20261113.md).
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment or Supabase live migration/write. Phase 04 remains IN PROGRESS.


## 2026-11-13 — Session lifecycle, atomic workspace and Customer dashboard integration
- Phase 04: conversation-scoped durable session cancellation checks conversation/run ownership; WebSocket/SSE event cursors are strictly validated and bounded to bigint. Workspace multi-file write-back now uploads immutable objects and commits all metadata/deletes in one idempotent, lease-fenced PostgreSQL transaction. Migration `20261113120000_moreai_workspace_atomic_execution_commit.sql` is committed but not applied; orphan Storage object cleanup remains open.
- Phase 06: `/api/v1/customer/agent-runs` now supports stable `(created_at,id)` keyset pagination while preserving the array response and legacy `before` cursor. `X-Next-Cursor` and `X-Pagination-Mode` are exposed.
- Phase 09: Customer Tasks view now renders persisted prompt text and loads additional Agent Run pages; Home view reads recent runs, wallet balance and Partner entitlement from authenticated APIs. Removed fabricated quota/task metrics and unsupported fixed capability claims. Existing UI layout/navigation retained; no screenshot regression evidence because browser/runtime testing was explicitly prohibited.
- Report: [Session, Workspace Atomicity & Customer Dashboard Integration](./PHASE-04-06-09-SESSION-WORKSPACE-CUSTOMER-DASHBOARD-20261113.md).
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment, provider calls or Supabase live migration/write. Phases 04/06/09 remain IN PROGRESS.

- Home view now differentiates an unavailable Agent Run API from a valid empty history state; no backend failure is presented as “no tasks”. Commit `9b5f59c10dafdeffdb16d95d11892ef9459bfe4b`.


## 2026-11-13 — Customer profile and Wi-Fi session integration continuation

- Phase 09: existing Customer Profile Settings now persists display-name edits and language locale through the authenticated FastAPI profile API; email remains read-only from Auth identity. Existing Wi-Fi Session screen now reads network sessions, wallet balances and quota usage through Customer APIs, derives active-session expiry from persisted timestamps, and exposes API errors without fabricating gateway telemetry.
- Source commits: `a7282fa7fd774d8dc4a78d66ed07fa8aa363122f`, `4bd3ca15a7951b1b3bc7027450e7f934285efdd7`, `2d74e9d0e8f1f28e99f45d79093d8ff369142daa`.
- Report: [Phase 09 Customer Profile & Wi-Fi Session Integration](./PHASE-09-CUSTOMER-PROFILE-WIFI-SESSION-INTEGRATION-20261113.md).
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment, Supabase migration or live write were run. This is source-only progress; Phase 09 remains IN PROGRESS and no runtime success is claimed.


- Customer integration continuation: Profile Settings persists display name and locale through FastAPI; Wi-Fi Session reads active network session, wallet and quota APIs; Code Assistant routes review requests to Customer Agent Chat instead of simulating Python execution; captive OTP success is disabled until a real gateway verification contract exists; captive success/preview surfaces no longer claim fabricated Wi-Fi speed, session duration or bonus credits and read actual network session/wallet/entitlement state. See [Phase 09 Customer Profile & Wi-Fi Session Integration](./PHASE-09-CUSTOMER-PROFILE-WIFI-SESSION-INTEGRATION-20261113.md). Source commits include `a7282fa7`, `4bd3ca15`, `2d74e9d0`, `cb205850`, `7d1d599b`, `e5b558bf`, `a0c9770b`, `61493b3c`, `26465c54`, `11cdde9f`. No tests/build/lint/typecheck/browser/API probes/staging/deployment/Supabase writes were run; Phase 09 remains IN PROGRESS.


## 2026-11-13 direct-main continuation — Benefit and Wi-Fi history

- Added persisted Customer network-session history to the existing Benefit & AI Credit screen.
- Wired the Wi-Fi filter to real network-session rows; sorted combined usage, ledger and session records by source timestamps.
- Separated quota limit, used amount and remaining amount in the benefit summary; wallet balance remains distinct.
- Report: [PHASE-09-CUSTOMER-BENEFIT-WIFI-HISTORY-20261113.md](./PHASE-09-CUSTOMER-BENEFIT-WIFI-HISTORY-20261113.md).
- Commits: `3f329d71`, `2fa22e5b`. Source-only increment; no tests, staging, deployment or Supabase writes. Phase 09 remains IN PROGRESS.


## 2026-11-13 direct-main continuation — Benefit and EduTech customer surfaces

- Benefit & AI Credit now combines persisted wallet, immutable ledger, LLM usage, entitlements, quota usage and Customer network-session history. Wi-Fi filter is populated from real network sessions; quota remaining is distinguished from quota limit.
- EduTech no longer shows unverified star ratings, review counts or partner affiliation. The video action is replaced with a truthful unavailable state while persisted learning progress remains active.
- Reports: [Benefit and Wi-Fi history](./PHASE-09-CUSTOMER-BENEFIT-WIFI-HISTORY-20261113.md); [EduTech truthfulness](./PHASE-09-CUSTOMER-EDUTECH-TRUTHFULNESS-20261113.md).
- Source commits: `3f329d71`, `2fa22e5b`, `b3e629ba`, `aa3b8ac0`. Documentation is source evidence only; Phase 09 remains IN PROGRESS.

- EduTech follow-up source correction: removed the remaining selected-module star/review claim. Commit `7c89b04f`; report updated.

## 2026-11-13 direct-main continuation — Customer files, code and captive flow

- Report: [PHASE-09-CUSTOMER-DASHBOARD-FILES-CODE-CAPTIVE-CONTINUATION-20261113.md](./PHASE-09-CUSTOMER-DASHBOARD-FILES-CODE-CAPTIVE-CONTINUATION-20261113.md).
- Added private artifact upload in Files, signed download in Artifact Results, persisted Code Assistant snapshots, and resilient per-workspace file listing.
- Removed false captive connection/consent/credit/speed claims, disabled unsupported registration/device controls, and corrected onboarding/help/welcome/partner benefit copy.
- Customer screen/action source inventory documented. Workspace direct upload, Chat attachment/resume, gateway verification, payment, EduTech catalog/video and support integrations remain open. Phase 09 remains IN PROGRESS.
- Source commits include `ebc2fd6b`, `6a5d5afc`, `da375eda`, `fb358e25`, `89c80599`, `a908baf5`, `29127edc`, `7d2fb99c`. No tests, staging, deployment, or Supabase live writes.


## 2026-11-13 Phase 09 continuation — workspace CAS upload and Chat resume

- Report: [PHASE-09-CUSTOMER-WORKSPACE-CAS-CHAT-RESUME-20261113.md](./PHASE-09-CUSTOMER-WORKSPACE-CAS-CHAT-RESUME-20261113.md).
- Customer workspace upload endpoint uses private version-addressed Storage objects, SHA-256 validation, active owner/member checks, idempotency and expected-version CAS through a server-only RPC. Existing immutable version-history trigger archives prior metadata.
- Files screen now uploads into a selected accessible workspace and refreshes versioned metadata. Artifact uploads remain a distinct private-artifact path.
- Chat now restores the most recent persisted conversation and messages when entered without an initial prompt. Attachment upload/reference/worker consumption is still outstanding.
- Migration `20261113001500_moreai_customer_workspace_upload_cas.sql` is committed but not applied to Supabase.
- No tests, lint, typecheck, build, browser checks, screenshots, staging, runtime probes or live Supabase changes were performed.
- Production deployment remains blocked by the controlling `AGENTS.md` Phase 11 release gate. No production deployment was attempted.
- Phase 09 remains IN PROGRESS.


- Final source increment head: `b2241ecf42a2cf53b1af894ccb5e1b6ac9738097`; implementation report updated at `0546163732e2c448630c4d859078a9d2e3748b10`.
- Vercel More AI team project listing returned HTTP 403 (not authorized), so the deployment target could not be independently inspected. Production deploy was not attempted because Phase 11 remains BLOCKED and the requested no-test constraint prevents satisfying the repository release gate.


## 2026-11-13 direct-main continuation — Chat attachments and run artifact linkage

- Report: [PHASE-09-CUSTOMER-WORKSPACE-CAS-CHAT-RESUME-20261113.md](./PHASE-09-CUSTOMER-WORKSPACE-CAS-CHAT-RESUME-20261113.md).
- Customer Chat now accepts up to 10 private artifacts (2 MB each, 10 MB total), validates MIME and binary signatures, and atomically links owned attachment metadata to the exact persisted message and durable run.
- Worker resolves attachments by run/user, verifies owner scope, purpose, conversation, byte length and SHA-256, then extracts UTF-8 text, PDF text or OCR text. Attachment content is passed as untrusted context.
- Customer conversation history restores attachment metadata; Workflow view shows persisted artifacts under their originating Agent Run with signed download.
- Nine pending migrations were applied to Supabase project `uunfgimtokhucegqbpce`; history versions `20261113002544`–`20261113002624` and `20261113003132`.
- Vercel frontend Production deployment request returned HTTP 402 daily deployment quota (retryAfter 86400). CLI fallback was attempted but the isolated CLI session was logged out; no authenticated Vercel CLI credentials were available. Backend project deployment was not submitted; newest commits are not deployed.
- No tests, lint, typecheck, build, browser/API/worker runtime checks, staging or E2E verification were run. Phase 09 remains IN PROGRESS, Phase 10 NOT ACCEPTED, Phase 11 BLOCKED.

- Latest source commit before tracker update: `575e193fd7f1a38310b4b6ca63da44446b9e0fde`; report updated at `6c8b9e0c898333d901ba500e3406383510393122`.

- Vercel CLI fallback outcome is documented in the Phase 09 report; the disposable sandbox was removed after the unauthenticated CLI attempt.


## 2026-11-13 direct-main continuation — Agent Run / Artifact cross-screen linkage

- Added owner-verified Agent Run association for artifact uploads via `X-Agent-Run-Id`; FastAPI checks the run belongs to the authenticated Customer before persisting `artifacts.run_id`.
- Code Assistant can select an owned persisted Agent Run before saving a private code snapshot; Research AI displays run-linked artifacts and signed downloads in its run detail.
- Commits: `6f06afa4`, `9126d358`, `4af10492`, `fe3b2efa`, `26c73d7e`, `828eb868`, `ed0eb39e`.
- Vercel More AI binding confirmed. Frontend and FastAPI Production deployments for `5501e3c80200f8c3e0d8314a6828a915f5c73305` reached READY. Frontend aliases include `moreai.web.id` and `www.moreai.web.id`; API alias is `more-ai-api.vercel.app`.
- A subsequent attempt to deploy current source HEAD `ed0eb39ef96267f24c7bfe6024763e1684b3f82d` hit Vercel HTTP 402 daily deployment quota. The latest cross-screen source increment is not yet live.
- Supabase migration history re-read: the nine previously applied migrations remain recorded; no migration was added in this increment.
- No real tests, staging, browser/API/worker runtime checks or E2E verification. Phase 09 IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.
- Detailed report: [PHASE-09-CUSTOMER-WORKSPACE-CAS-CHAT-RESUME-20261113.md](./PHASE-09-CUSTOMER-WORKSPACE-CAS-CHAT-RESUME-20261113.md).


## 2026-11-13 follow-up — chat attachment run relationship resolution

- Corrected the artifact listing contract to resolve Chat attachment `run_id` through the authoritative `conversation_message_attachments` junction. Chat attachments are uploaded before their Agent Run exists, so the artifact row's nullable `run_id` is not sufficient; this owner-scoped join now exposes the exact run association to Research, Workflow and artifact clients without a schema migration.
- Source commit: `9e1c64e5de6e2ee33d3ba2e127ebb05413d7c73d`.
- This latest API source change is not included in the current Vercel Production deployments (both remain at commit `5501e3c`). The attempt to deploy newer source HEAD `ed0eb39` was rejected by Vercel's daily API deployment quota; no new deployment was created for `9e1c64e`.


## Vercel alias assignment readback — 2026-11-13

- Production aliases were explicitly reassigned from the older deployments to the two newly READY deployments for commit `5501e3c80200f8c3e0d8314a6828a915f5c73305`.
- Readback confirms `moreai.web.id` and `www.moreai.web.id` resolve to frontend deployment `dpl_524drp293BpdsxwtRWmEcUScz8p8`; `moreai.web.id` retains its 308 redirect to `www.moreai.web.id`.
- Readback confirms `more-ai-api.vercel.app` resolves to FastAPI deployment `dpl_2VajdXAEAgmSzfyx5J5WtQKkex88`.
- These alias updates make the READY deployment the current domain target. They do not deploy later source commits; current source HEAD remains ahead of the deployed SHA.

## 2026-11-13 direct-main continuation — Customer identity fallback and API transport recovery

- Home greeting and Profile now fall back to the signed-in Supabase Auth user when the FastAPI identity request cannot be reached. Registered name lookup supports `full_name`, `name`, and `display_name`; email local-part is the final display fallback. Browser Supabase access remains Auth-only.
- The typed API client now retries only GET/HEAD requests against the verified canonical API alias when the configured primary API host fails at the transport layer. Mutating requests are never automatically replayed. Transport errors are surfaced with actionable API/CORS guidance.
- Production configuration readback confirms the frontend API origin and allowed CORS origins include `moreai.web.id` and `www.moreai.web.id`. Current READY production deployments still point to commit `5501e3c80200f8c3e0d8314a6828a915f5c73305`; the new source changes are not deployed.
- Vercel runtime error aggregation (24h) returned no error clusters for frontend or API; API individual logs beyond the Hobby plan's one-hour retention were unavailable. No live API/browser request was made.
- Commits: `a127c4eb`, `eedd1e90`, `0fd4f4e8`.
- No tests, lint, typecheck, build, browser/API/worker runtime checks, screenshots, staging, or E2E verification. No Supabase schema/data changes.
- Phase 09 remains IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.


## 2026-11-13 — Provider onboarding and customer-domain contract gate

- Re-read the controlling `AGENTS.md` and Master PRD at `public/assets/aistudio/MoreAI_Master_PRD_v1.0_ID_2f5fa0c2.md`. Confirmed the required trust boundary: FastAPI owns all business data/actions; browser Supabase access remains Auth-only; provider credentials stay server-side; unavailable sponsored access fails closed.
- Read-only production schema inspection confirms the verification/session persistence primitives already exist: `network_verification_attempts`, `network_verification_evidence`, `network_verification_sessions`, `network_gateway_nonces`, `network_sessions`, and `network_session_events`. All listed network lifecycle tables are RLS-enabled. This does not establish that the API lifecycle or provider integration is complete.
- Consent persistence and OTP challenge/delivery primitives were not identified in the inspected schema. Existing Customer routes expose network session history and access-code redemption, while Partner routes expose tenant-scoped network registration/configuration, readiness gating, and access-code lifecycle. No verified provider callback contract or secret resolver is configured.
- Reconciled the real-provider prerequisites for Captive Gateway, OTP, EduTech, payment and support in [Provider onboarding and domain contract gate](./PHASE-09-PROVIDER-ONBOARDING-AND-DOMAIN-CONTRACTS-20261113.md). This is an onboarding/architecture artifact, not a claim that an adapter or lifecycle was implemented.
- No migration, provider activation, test, staging, runtime request, build, lint, typecheck, browser check, worker execution or deployment was performed. Phase 09 remains IN PROGRESS; Phase 10 remains NOT ACCEPTED; Phase 11 remains BLOCKED.

## 2026-11-13 — Customer Create Studio text workflow continuation

- Corrected the existing Create Studio Generate Video action: the screen's described script/storyboard deliverable now hands off to the existing Chat/OpenManus Agent path, with an explicit text-only instruction and no claim that a video file was rendered.
- Image generation remains unavailable until a real media provider is configured; no synthetic media, credit charge or success state was introduced.
- Existing Customer UI layout and visual styling were not changed.
- Source commit: `02a619298894ba4cfedff72bafd7b2eea116604a`.
- Continuation report: [Phase 09 Customer Dashboard Integration — Continuation](./PHASE-09-CUSTOMER-DASHBOARD-CONTINUATION-20261113-2.md).
- No tests, lint, typecheck, build, browser/API/worker runtime checks, provider calls, migration, staging or deployment were run.
- Phase 09 remains IN PROGRESS; Phase 10 remains NOT ACCEPTED; Phase 11 remains BLOCKED.


## 2026-11-13 direct-main continuation — Customer authorization and pagination

- Report: [Customer authorization, pagination & lifecycle continuation](./PHASE-09-CUSTOMER-AUTH-PAGINATION-LIFECYCLE-20261113.md).
- Customer and notification resources now consistently require the server-resolved Customer principal; catalogue endpoints used by Customer Agent Studio are similarly scoped. Partner/platform principals remain separated.
- Artifact, Knowledge Library and Code Assistant history selectors use incremental keyset pages. Approval decisions no longer appear failed merely because the independent Agent Run refresh failed.
- Source commits: `3e5aae18`, `af4b68c2`, `8346c6cc`, `82f812a8`, `7c8646a4`, `15257ace`, `753fa76a`.
- No tests, lint, typecheck, build, browser/API/worker checks, staging, migrations, provider calls or deployment. Phase 09 remains IN PROGRESS; Phase 10 NOT ACCEPTED; Phase 11 BLOCKED.


## 2026-11-14 — Phase 09 Customer Dashboard integration continuation

Latest source-only continuation commits on `main`:
- `c562378b0d5d9e53e4e1f54c086e37f4ef33b1c2`: ChatView lifecycle event taxonomy and safe metadata.
- `e52a36cd1ec402373d58767c99e87c5332d05366`: expanded REST thinking/WebSocket replay projection for planning, agent, tool and approval lifecycle events.
- `329a6eeaf490f1de73a9ef56447054f3317ff7a0` and `1a55db2bfca2ea745768638df6b68dcd00c57239`: RAG citations limited to final-response source markers and sanitized to chunk/document provenance.
- `62512ce02de7a856949b50cf9277708bc3e6ad96`: detailed Phase 09 continuation report and source-level acceptance matrix.

Phase 09 remains **IN PROGRESS**. Customer event consumers now recognize the expanded event family; Workflow and Tasks continue to consume safe run activity logs. Citation provenance is improved at final-output assembly but still requires response/history contract reconciliation and runtime acceptance. The approval decision RPC remains atomic for approval/pause/run/checkpoint state, but decision/resume event rows are not yet appended in that same database transaction. A forward-only migration is still required; no live Supabase schema/data change was made in this increment.

No tests, lint, typecheck, build, browser verification, live API/worker execution, Supabase mutation, staging or deployment were performed. Source implementation and documentation only; runtime behavior remains unverified.

**Next Phase 09 work:** (1) transactionally append approval decision/resume events in the database RPC via a new forward-only migration; (2) finish Customer endpoint authorization/response contract audit; (3) reconcile RAG citation provenance across retrieval, final output, persisted conversation history and Chat restore; (4) finalize the Customer UI/API acceptance matrix. Phase 10 End-to-End Integration Verification is dependency-next only after Phase 09 and must remain unperformed unless runtime verification is authorized. Phase 11 Integration Release Gate follows Phase 10.


## 2026-11-14 — Phase 09 Customer Dashboard continuation (latest source-only increment)

- Atomic approval decision and resume event migration source committed: `supabase/migrations/20261114090000_moreai_atomic_approval_decision_events.sql` (commit `dd67833335b925ea3fbc4754fff4f5cf44b37f12`). It appends decision and `run.resume_queued` events to the durable event table and canonical outbox in the same transaction as approval/pause/run/checkpoint updates. Applied to canonical Supabase project `uunfgimtokhucegqbpce` as migration version `20261113182657`; read-only schema inspection confirms the helper and `run.resume_queued` are present. No runtime approval flow was executed.
- FastAPI and Chat consumers now surface `run.resume_queued`; worker no longer duplicates atomic grant/deny/expire events. Consumption event remains worker-observed.
- Customer API source audit: 77 route handlers across ten Customer/shared router modules; all 77 route signatures require `customer_principal`, while Customer WebSockets explicitly resolve `require_customer_context`. JSON endpoints use explicit response models except SSE/binary/WebSocket transport-specific routes. Live RLS/cross-tenant proof remains outstanding.
- Customer session replay and SSE now use allowlisted activity metadata; terminal SSE returns final answer text and validated citations, not raw run output/error objects.
- RAG citations now flow from an explicit retrieval `citation_marker`, through final answer marker matching and structured Agent Run output, to owner-scoped Customer conversation detail/history responses and Chat restore/pagination/resumed completion. Markers are removed from visible prose while citation metadata remains attached.
- UI changes remain limited to existing Chat lifecycle labels, typed citation metadata and history restoration. No redesign or token migration.
- Reports updated: [Phase 09 Chat/session/citation continuation](./PHASE-09-CUSTOMER-CHAT-DURABLE-SESSION-RECOVERY-20261113.md) and [Customer action/API inventory](./PHASE-09-CUSTOMER-ACTION-API-INVENTORY-20261113.md).
- No tests, lint, typecheck, build, browser/API/worker execution, migration apply, Supabase mutation, staging or deployment were performed.

**Phase 09 remains IN PROGRESS.** Next: complete source-level screen/action contract reconciliation against latest PRD; close approval consumption/expiry lifecycle transaction gap where necessary; review citation recovery for every agent/checkpoint branch; then finalize acceptance matrix. Phase 10 remains blocked by Phase 09 completion and runtime-verification authorization; Phase 11 follows Phase 10.


### 2026-11-14 final reconciliation update
- Direct Agent Run event history `GET /api/v1/agent-runs/{id}/events` now uses the same safe event projection as logs/thinking/WebSocket/SSE; Customer terminal SSE is restricted to final text, structured citations and bounded error code.
- RAG tool results now include validated per-chunk citation markers; final prompt requires exact markers; the runtime persists chunk/document provenance and removes machine markers from visible prose. Customer conversation detail and keyset history hydrate citations from the owner-scoped run output.
- Worker approval decision labels are no longer duplicated after the atomic decision event; successful single-use consumption remains separately recorded.
- Latest report: [Phase 09 Customer Chat/session/citation continuation](./PHASE-09-CUSTOMER-CHAT-DURABLE-SESSION-RECOVERY-20261113.md), commit `ebb40fe6eca095a33c283edc81c273f38c6a1e8c`.
- Approval decision/resume migration is now applied to canonical Supabase as `20261113182657`. No tests, build, browser/API/worker verification, Supabase mutation, staging or deployment were performed. Phase 09 remains open.


### Supabase migration application (2026-11-14)
- Applied `moreai_atomic_approval_decision_events` to canonical project `uunfgimtokhucegqbpce`; Supabase migration history records version `20261113182657`.
- Renamed the repository migration file to `supabase/migrations/20261113182657_moreai_atomic_approval_decision_events.sql` to match the recorded database version.
- Read-only post-apply schema inspection confirms `moreai_append_approval_lifecycle_event` exists and the deployed `moreai_decide_tool_approval` definition calls it and contains `run.resume_queued`.
- No approval workflow/runtime execution, tests, staging, deployment or browser verification was performed.


### PRD-aligned Customer Dashboard acceptance matrix
- Added [Phase 09 Customer Dashboard Acceptance Matrix](./PHASE-09-CUSTOMER-DASHBOARD-ACCEPTANCE-MATRIX-20261114.md), reconciling Customer navigation and workflows against Master PRD sections 6.1, 16, 17.1, 18.1, 21.5 and 34.
- The matrix separates CONNECTED, PARTIAL/GATED and UNAVAILABLE/FAIL-CLOSED capabilities; it explicitly avoids presenting unavailable connector OAuth, Memory privacy controls, manual retry, payment/subscription settlement or partner OTP/gateway activation as working.
- 77 Customer/shared API route handlers were source-scanned for Customer principal protection. Direct Agent Run event history and Customer SSE are now sanitized; conversation history restores structured RAG citations.
- Approval decision/resume migration is applied to canonical Supabase as version `20261113182657`.
- Phase 09 remains IN PROGRESS because the PRD still includes unavailable provider/domain contracts and runtime acceptance is intentionally not performed. No tests, build, browser/API/worker verification, staging or deployment.


## 2026-11-14 — Customer Auth and Vercel build recovery
- Report: [Phase 09 Auth Recovery & Vercel Build Recovery](./PHASE-09-AUTH-AND-VERCEL-RECOVERY-20261114.md).
- Fixed Customer workspace version-history client mismatch (`versionsPage` → actual `versions` contract) and removed the stale pagination action that Vercel's next type-check reported.
- Customer login now distinguishes Supabase `invalid_credentials`, unconfirmed email, banned account, rate limits and transport failures rather than labeling every failure as a wrong password.
- Read-only Supabase Auth logs show successful password signup/login/refresh events, one `invalid_credentials` password-grant failure and one recovery email rate-limit response (HTTP 429). Vercel project environment metadata confirms required Supabase URL/publishable-key/API URL variable names exist; no secret values were decrypted. No account or Auth settings were modified.
- Vercel API deployment for `fb4929b` reached READY. Frontend deployment for `557c7eb` failed on a stale pagination callback; after correction, the latest `c5eb19a` frontend deployment was QUEUED at report time. The API deployment for `c5eb19a` was also QUEUED; the API deployment at `fb4929b` is READY.
- No tests, lint, typecheck, local build, browser/API/worker runtime checks, staging or E2E were run. Vercel's own Git deployment build is not Phase 10/11 acceptance evidence.
- Phase 09 remains IN PROGRESS; Phase 10 NOT STARTED/BLOCKED; Phase 11 BLOCKED by the controlling AGENTS.md release gate. No production release at the latest source HEAD is yet verified.
