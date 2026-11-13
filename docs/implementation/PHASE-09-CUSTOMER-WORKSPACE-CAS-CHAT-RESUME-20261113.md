# Phase 09 — Customer Workspace, Chat Attachments & Run Artifact Integration

**Date:** 2026-11-13  
**Execution branch:** `main`  
**Baseline commit:** `dc514ded8711a59c248b1d657d871be832114225`  
**Latest source commit at report time:** `575e193fd7f1a38310b4b6ca63da44446b9e0fde`  
**Status:** IN PROGRESS — Phase 09 is not complete.

## Scope delivered in this continuation

### 1. Customer workspace immutable upload

- Added `20261113001500_moreai_customer_workspace_upload_cas.sql`.
- Added a server-only idempotency ledger and service-role-only CAS RPC.
- The RPC validates active workspace owner/member access, version-addressed immutable Storage path, SHA-256, file size, idempotency payload consistency, and expected-version compare-and-swap.
- Existing version-history trigger records the previous committed file version.
- Added authenticated FastAPI `POST /api/v1/customer/workspaces/{workspace_id}/files` using `X-Workspace-Path`, `If-Match`, and `Idempotency-Key`.
- Customer Files UI now selects a workspace and uploads to its versioned path through the typed API client. Artifact Storage and workspace versioned Storage remain separate.

### 2. Customer Chat attachment lifecycle

- Added `20261113130000_moreai_chat_attachment_lifecycle.sql`.
- Added private owner-scoped attachment linkage from conversation message → durable Agent Run → artifact metadata, with server-only RLS and a service-role-only atomic enqueue RPC.
- Artifact upload accepts the explicit `chat_attachment` purpose only when the authenticated user owns the target conversation.
- Server enforces a 2-MB per-file limit, MIME allowlist, UTF-8 validation for text, and PDF/JPEG/PNG/WebP signature checks.
- Customer Chat now supports up to 10 attachments and 10 MB total selected bytes. Upload uses the existing private artifact Storage path; no browser service-role access was added.
- Customer message enqueue validates attachment ownership, conversation scope and metadata before persisting message, run and attachment links atomically.
- Replaying the same idempotency key with a different prompt, agent key or attachment set is rejected.
- Conversation history now returns attachment metadata alongside persisted messages.

### 3. Worker-side attachment consumption

- Added `apps/worker/app/attachment_loader.py`.
- Worker resolves attachment links by durable run and user scope, rechecks artifact ownership/purpose/conversation, downloads only from the private artifact bucket, validates byte count and SHA-256, and extracts UTF-8 text, PDF text, or image OCR.
- Per-file extraction is capped at 25,000 characters and total extracted context at 80,000 characters. File content is passed to the agent as explicitly untrusted source material, not trusted instructions.
- Manus, ToolCall and gated SWE runtime registrations receive the attachment loader. Planning uses the same Manus execution runtime.
- Unsupported or unresolved attachments fail closed; worker does not silently omit a requested attachment.

### 4. Agent Run ↔ Artifact lifecycle

- Artifact metadata list now includes its owner-scoped `run_id`.
- Customer Workflow view reads persisted artifacts and renders signed-download actions under the Agent Run that created them.
- This connects worker-generated artifacts with durable run history. It does not yet provide complete cross-screen navigation and linking for every Create/Analyse/Code/Research/Tasks workflow.

### 5. Existing Chat resume and Workspace UI

- Chat restores the most recent active persisted conversation when opened without an initial prompt.
- Customer Files UI provides workspace selection and version-aware upload.
- Existing signed downloads and artifact metadata flows are retained.

## Source files changed

- `supabase/migrations/20261113001500_moreai_customer_workspace_upload_cas.sql`
- `supabase/migrations/20261113130000_moreai_chat_attachment_lifecycle.sql`
- `apps/api/app/routers/workspaces.py`
- `apps/api/app/routers/artifacts.py`
- `apps/api/app/routers/conversations.py`
- `apps/api/app/routers/customer.py`
- `apps/api/app/main.py` — CORS allowlist for workspace CAS and chat attachment headers
- `apps/worker/app/attachment_loader.py`
- `apps/worker/app/registry_factory.py`
- `engine/agents/durable_tool_runtime.py`
- `lib/api/client.ts`
- `components/views/files-view.tsx`
- `components/views/chat-view.tsx`
- `components/views/workflow-progress-view.tsx`

## Supabase production migration status

Canonical project: `MoreAIdb` / `uunfgimtokhucegqbpce` (PostgreSQL 17, ap-southeast-2).

The following nine previously pending source migrations were successfully applied to the production database in dependency order:

1. `moreai_workspace_file_version_history`
2. `moreai_workspace_restore_approval_key`
3. `moreai_customer_learning_progress`
4. `moreai_knowledge_rag_vector`
5. `moreai_durable_knowledge_file_ingestion`
6. `moreai_customer_workspace_upload_cas`
7. `moreai_enable_toolcall_agent`
8. `moreai_workspace_atomic_execution_commit`
9. `moreai_chat_attachment_lifecycle`

Supabase migration history readback records the eight first migrations at versions `20261113002544` through `20261113002624`, and Chat attachment lifecycle at `20261113003132`. This is migration-history confirmation, not application runtime or feature acceptance. No destructive reset/drop/truncate operation was performed.

## Vercel deployment status

Target team: `More AI` / `team_wHMjZ5NapyaF8aYYVs4UUY36`.  
Frontend project: `more-ai-portal-indihome` / `prj_2ge37Xd5uBSUGhn3wPsaHfFcW1UV`.  
Backend project: `more-ai-api` / `prj_L6i6j0ERPcdpZNM1c53hcdPaP9Nn`.

A Production deployment request for the frontend at the then-current `main` commit was rejected by Vercel with HTTP `402 payment_required`, resource `api-deployments-free-per-day`, and `retryAfter=86400`. The API project deployment was not submitted after that quota response. I also attempted the mapped Vercel CLI fallback in a disposable Vercel sandbox: the CLI was not preinstalled, `npx vercel` installed it, but the CLI session was logged out and had no authenticated Vercel credentials. No temporary/preview deployment was substituted for Production. The sandbox was removed. No billing, plan, quota or team settings were changed. The latest attachment/run-artifact commits are therefore not deployed.

## Verification policy and release state

Per the explicit no-real-testing/no-staging instruction, no tests, lint, typecheck, build, browser checks, screenshots, runtime API probes, worker execution, or end-to-end feature checks were run. GitHub source readback and Supabase migration-history readback are not substitutes for runtime verification.

- Phase 09 remains **IN PROGRESS**.
- Phase 10 remains **NOT ACCEPTED** because frontend → FastAPI → worker → provider/tools → Supabase → frontend runtime proof has not been run.
- Phase 11 remains **BLOCKED** because security/RLS/cross-tenant proof, migration validation, API contract acceptance, UI regression evidence, worker/sandbox/provider deployment proof and release evidence are incomplete.
- Production deployment remains blocked by the Vercel daily deployment quota; do not claim that the latest commit is live.

## Remaining Phase 09 scope

1. Full cross-screen Agent Run/Artifact lifecycle: persist and navigate related runs/results across Chat, Research, Create, Analyse, Code, Tasks and Workflow, including artifact-to-run links for all creation flows.
2. Captive Gateway: actual ISP/gateway adapter, signed network context, tenant/network verification, consent persistence, OTP provider and session create/refresh/revoke. Keep unavailable actions fail-closed until the partner gateway integration is configured.
3. Complete Customer screen/action inventory against FastAPI/OpenAPI; remove or explicitly disable any unsupported action without fake success.
4. EduTech catalog, enrollment/lesson contract and protected video delivery.
5. Provider-backed image/video generation with durable run/credit/artifact lifecycle.
6. Payment checkout, verified webhook settlement, top-up and subscription entitlement activation. Pricing/payment product decisions and provider credentials are still prerequisites.
7. Official support channel and ticket lifecycle.
8. Validated historical Analytics aggregation and remaining profile/security/device/Wi-Fi lifecycle parity.

## Next dependency-ordered work

Continue Phase 09. Finish Agent Run/Artifact relationships and the Customer action-to-OpenAPI inventory, then implement the real provider-backed Captive Gateway and other integrations as their contracts/configuration are made available. Phase 10 and Phase 11 cannot be honestly accepted while the requested no-test constraint remains in force.


## 2026-11-13 continuation — Run/artifact linkage and Vercel production recovery

- Added optional `X-Agent-Run-Id` to private artifact uploads. FastAPI re-resolves the supplied Agent Run under the authenticated owner before persisting the artifact's `run_id`; browser clients cannot attach an artifact to another user's run.
- Added the CORS allowlist entry for `X-Agent-Run-Id` and typed `artifactApi.upload(..., runId?)`.
- Code Assistant now loads the authenticated user's persisted Agent Runs, allows selecting a run before saving a code snapshot, and displays the associated run ID on saved snapshots. Snapshots without an explicitly selected run remain unlinked.
- Research AI now loads artifacts alongside Agent Runs and displays signed-download actions for artifacts whose `run_id` matches the selected research run. Existing layout was preserved; additions are limited to the requested run/artifact relationship.
- Source commits: `6f06afa4`, `9126d358`, `4af10492`, `fe3b2efa`, `26c73d7e`, `828eb868`, `ed0eb39e`.
- Supabase migration history was read again. All nine migrations previously reported as applied remain present, including workspace atomic execution and Chat attachment lifecycle. No new migration was introduced in this source increment.
- Vercel More AI binding was re-read and confirmed against the intended team and both linked Git projects. Production deployments for commit `5501e3c80200f8c3e0d8314a6828a915f5c73305` reached `READY`:
  - Frontend: `dpl_524drp293BpdsxwtRWmEcUScz8p8`, aliases include `moreai.web.id`, `www.moreai.web.id`, and `more-ai-portal-indihome.vercel.app`.
  - FastAPI: `dpl_2VajdXAEAgmSzfyx5J5WtQKkex88`, alias `more-ai-api.vercel.app`.
- A further deployment for the newer source HEAD `ed0eb39ef96267f24c7bfe6024763e1684b3f82d` was rejected by Vercel with HTTP 402 `api-deployments-free-per-day`. The two READY deployments therefore do not yet contain this latest cross-screen source increment. No alternate account, team, or billing/quota workaround was used.
- No tests, lint, typecheck, browser/API/worker runtime probes, staging or E2E checks were run. Vercel's production build pipeline did compile/type-check the deployed `5501e3c` frontend as part of its own deployment process; this is not end-to-end acceptance evidence.
- Phase 09 remains IN PROGRESS; Phase 10 remains NOT ACCEPTED; Phase 11 remains BLOCKED.


## 2026-11-13 follow-up — chat attachment run relationship resolution

- Corrected the artifact listing contract to resolve Chat attachment `run_id` through the authoritative `conversation_message_attachments` junction. Chat attachments are uploaded before their Agent Run exists, so the artifact row's nullable `run_id` is not sufficient; this owner-scoped join now exposes the exact run association to Research, Workflow and artifact clients without a schema migration.
- Source commit: `9e1c64e5de6e2ee33d3ba2e127ebb05413d7c73d`.
- This latest API source change is not included in the current Vercel Production deployments (both remain at commit `5501e3c`). The attempt to deploy newer source HEAD `ed0eb39` was rejected by Vercel's daily API deployment quota; no new deployment was created for `9e1c64e`.


## Vercel alias assignment readback — 2026-11-13

- Production aliases were explicitly reassigned from the older deployments to the two newly READY deployments for commit `5501e3c80200f8c3e0d8314a6828a915f5c73305`.
- Readback confirms `moreai.web.id` and `www.moreai.web.id` resolve to frontend deployment `dpl_524drp293BpdsxwtRWmEcUScz8p8`; `moreai.web.id` retains its 308 redirect to `www.moreai.web.id`.
- Readback confirms `more-ai-api.vercel.app` resolves to FastAPI deployment `dpl_2VajdXAEAgmSzfyx5J5WtQKkex88`.
- These alias updates make the READY deployment the current domain target. They do not deploy later source commits; current source HEAD remains ahead of the deployed SHA.

## 2026-11-13 follow-up — production Customer identity and API transport recovery

### Source changes on main
- `components/views/home-view.tsx`: when `GET /api/v1/me` is unavailable, the greeting now reads only the authenticated Supabase Auth user and resolves the registration name from `user_metadata.full_name`, `name`, or `display_name`, then the email local-part. It does not query profile tables directly from the browser.
- `components/views/profile-settings-view.tsx`: profile identity and email now have the same Auth-only fallback if the FastAPI profile request fails. Notification preferences remain an independent resource; no false profile-update success is shown.
- `lib/api/client.ts`: read-only GET/HEAD requests can retry against the verified canonical API alias `https://more-ai-api.vercel.app` only when the configured primary host `https://more-ai-api-more-ai.vercel.app` fails at the transport layer. POST/PATCH/PUT/DELETE are never replayed. Transport failures now produce an actionable API connectivity/CORS message rather than a generic browser `Failed to fetch`.
- Commits: `a127c4eb05239434d1fd9a34e2ef4f233e56300a`, `eedd1e90f3705320bd121a4e62c3d362ac92f7db`, `0fd4f4e8cbc53e070455589ddffade02bfc634d9`.

### Production configuration readback
- Frontend `NEXT_PUBLIC_MOREAI_API_URL` is configured to `https://more-ai-api-more-ai.vercel.app`; the API project's `MOREAI_CORS_ALLOWED_ORIGINS` includes both `https://moreai.web.id` and `https://www.moreai.web.id`.
- The API project's Supabase URL and publishable key variables are configured; API source supports `SUPABASE_PUBLISHABLE_KEY` as the Auth key fallback. Service-role values were not read or exposed.
- Current Production frontend and API deployments are both READY at commit `5501e3c80200f8c3e0d8314a6828a915f5c73305`. That deployed commit is an ancestor of the identity fallback work but does not include the new transport fallback and current source updates.
- Runtime error aggregation for the last 24 hours returned no runtime error clusters for either project. Individual API logs could not be queried for 24 hours because the current Vercel plan retains only one hour; a recent 30-minute error-level log query returned no entries. This is not proof that browser-side CORS/transport requests succeed.
- No live API/browser request was made, in keeping with the no-real-testing instruction. The current production deployment therefore remains unchanged; the latest source commits are not live.

### Verification and scope boundary
- No tests, lint, typecheck, build, browser checks, screenshots, API probes, worker execution, staging, or E2E checks were run.
- No Supabase schema or production data changes were needed.
- Phase 09 remains IN PROGRESS. Identity fallback and safe API transport recovery are source-implemented, not runtime-accepted.
- Remaining Phase 09 scope remains: complete Agent Run/Artifact links across all Customer workflows; actual Captive Gateway provider adapters and signed network verification; full Customer action/OpenAPI inventory; provider-backed EduTech, payment, support and validated Analytics.

## 2026-11-13 continuation — Customer workflow linkage, action contract inventory and analytics

### Agent Run ↔ Artifact / Knowledge linkage
- Tasks view now reads both the paginated Agent Run history and private artifact metadata. Its existing Artifacts tab now lists real artifacts, shows the persisted `run_id` association when present, and downloads through the owner-checked short-lived signed URL API.
- Analyse view now loads the authenticated user's Knowledge Library, displays persisted ingestion states, and only offers Agent analysis for a document in `ready` state. The selected document ID is passed into the Chat handoff.
- OpenManus `knowledge_search` now accepts an optional validated list of 1–20 document UUIDs. The worker validates the UUID list and forwards it to the existing `moreai_match_knowledge_chunks` RPC. This allows Analyse to restrict retrieval to the selected ready document instead of searching the entire knowledge collection.
- Create text/document/translation/presentation remains a Chat handoff; the actual Agent Run is created when Chat submits the prompt. Worker `file_saver` already persists generated artifacts with the current `run_id`. Research, Code and Workflow retain their existing run/artifact links.
- Existing UI layout is retained; changes are limited to linking and showing persisted backend records.

### Customer action ↔ FastAPI inventory
- Added `docs/implementation/PHASE-09-CUSTOMER-ACTION-API-INVENTORY-20261113.md` with screen/action → typed client → FastAPI route → source status, and explicit unavailable boundaries for Captive Gateway, EduTech catalog/video, payment and support.
- Corrected the typed conversation session client method: it now requires both `conversationId` and `runId` and calls the implemented `/api/v1/conversations/{conversation_id}/sessions/{run_id}` route. The previous unused method called a non-existent collection path.
- Source-level inventory confirms the current Customer read/write routes and identifies remaining unsupported actions; it is not runtime contract acceptance.

### Historical Analytics
- Added migration `20261113140000_moreai_customer_usage_analytics.sql`, applied successfully to canonical Supabase project `uunfgimtokhucegqbpce`.
- Migration history records version `20261113051221` / `moreai_customer_usage_analytics`.
- Added service-role-only, SECURITY INVOKER SQL aggregation over `llm_usage`, returning period summary, model/provider breakdown, daily trend, token totals, success/failure counts, recorded cost and average latency.
- Added authenticated FastAPI `GET /api/v1/customer/usage/analytics?days=7|30|365`, typed API client contract and Analytics screen binding. The server aggregates all rows in the selected interval; it no longer derives year analytics from only the latest 100 records.
- Database readback confirms the function exists with signature `(p_user_id uuid, p_since timestamptz, p_until timestamptz)`, is not SECURITY DEFINER, and is recorded in migration history.

### Production API origin configuration
- Re-read the More AI Vercel project binding and corrected frontend Production/Preview/Development `NEXT_PUBLIC_MOREAI_API_URL` from the unverified project subdomain `https://more-ai-api-more-ai.vercel.app` to the verified canonical API alias `https://more-ai-api.vercel.app`.
- Vercel environment variable ID `xVvfczzzPtHWdQH0` was updated. This change applies to a future deployment; it does not rewrite the environment baked into the currently READY production deployment.
- Existing CORS allowlist includes `https://moreai.web.id` and `https://www.moreai.web.id`.
- Current Production deployment is still the previously READY commit `5501e3c80200f8c3e0d8314a6828a915f5c73305`. Latest `main` source and the corrected environment are not yet live. Previous Vercel deployment attempt returned HTTP 402 `api-deployments-free-per-day`; no retry, alternate team, billing or quota workaround was used in this increment.

### Provider / product-domain reconciliation
- Supabase production catalog still shows all five network verification methods (`gateway`, `gps`, `isp_api`, `mikrotik_hotspot`, `radius`) with `adapter_ready=false`. Partner config API rejects activation when the adapter is not ready. No gateway/provider secret, supported callback/API contract or secret-vault resolver is configured; Captive Portal remains fail-closed.
- `customer_learning_progress` is available, but no authoritative course catalog, enrollment or protected video delivery schema/provider is present.
- Wallet, credit ledger, quotas and entitlements are present, but no checkout/payment settlement/webhook provider contract is present.
- No support ticket schema, response lifecycle or official support provider is present.
- These areas remain unavailable rather than simulated; no schema/table was fabricated for a provider that is not configured.

### Source commits in this increment
- `832cdc8b`, `a2fe1bea`, `4b656c76` — analytics migration authored and corrected.
- `2a38afac` — Customer historical analytics FastAPI route.
- `460955c5`, `f8aa2ec3` — typed analytics and corrected conversation session client contracts.
- `0dc59bd0` — Analytics screen uses server-side historical aggregates.
- `5f1aa596` — Tasks view lists/downloads run-linked artifacts.
- `f0e7b6e1`, `4f5b64cc` — document-scoped OpenManus knowledge search schema/runtime.
- `0e7b8c6d`, `6c67ff93` — Analyse document list and selected-document Agent handoff.
- `fddbd11e` — Customer action/API contract inventory.
- Vercel environment correction: `NEXT_PUBLIC_MOREAI_API_URL` now points to `https://more-ai-api.vercel.app`.

### Verification boundary
- Source readback and read-only Supabase migration/function metadata readback only.
- No tests, lint, typecheck, build, browser checks, screenshots, API probes, worker execution, provider calls, staging or E2E checks were run.
- The Supabase analytics migration is applied, but the new analytics API/UI is not runtime-accepted.
- Phase 09 remains IN PROGRESS; Phase 10 remains NOT ACCEPTED; Phase 11 remains BLOCKED.

### Captive Gateway production inventory — additional readback
- Read-only production row counts: `network_providers=0`, `partner_networks=0`, `network_verification_configs=0`, and `network_sessions=0`.
- The five verification catalog methods remain `adapter_ready=false`.
- This confirms there is currently no real partner network/provider configuration to bind an adapter to. No partner gateway credentials, callback/API contract, or secret reference can be inferred from an empty inventory. The gateway remains blocked by actual provider onboarding/configuration, not merely by missing UI wiring.
