# Phase 09 — Customer Action ↔ FastAPI Contract Inventory

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: source-level reconciliation of Customer dashboard actions against the FastAPI router and canonical Supabase schema. This is not runtime acceptance.

## Architecture boundary

- Existing Next.js Customer screens call the typed API clients in `lib/api/client.ts` and `lib/api/knowledge.ts`.
- FastAPI is the only browser-facing business-data and business-action API.
- Supabase browser SDK access is restricted to Auth flows. Business tables, Storage, RPC, Realtime, provider secrets and service-role access remain server-only.
- Worker-created artifacts are persisted with `run_id`; the private artifact API resolves Chat attachment links through `conversation_message_attachments`.
- Customer and Partner route namespaces remain separate.

## Customer action inventory

| Customer screen / action | Frontend contract | FastAPI contract | Source status |
|---|---|---|---|
| Login, registration, password recovery, Auth session | Supabase Auth browser client | Supabase Auth | Connected; OAuth availability remains provider configuration-dependent |
| Home identity | `profileApi.get()` | `GET /api/v1/me` | Connected; Auth-only identity fallback exists for transient API outage |
| Home Agent Run summary | `customerApi.agentRunsPage()` | `GET /api/v1/customer/agent-runs` with keyset cursor | Connected |
| Home wallet and entitlement | `customerApi.wallets()`, `entitlements()` | `GET /api/v1/customer/wallet`, `GET /api/v1/customer/entitlements` | Connected |
| Customer context | `customerApi.context()` | `GET /api/v1/customer/context` | Connected |
| Chat conversation restore | `customerApi.conversations()`, `getConversation()` | `GET /api/v1/customer/conversations`, `GET /api/v1/customer/conversations/{id}` | Connected |
| Chat message / Agent Run enqueue | `customerApi.sendMessage()` | `POST /api/v1/customer/conversations/{id}/messages` | Connected; atomic message/run/attachment RPC and idempotency key |
| Chat attachments | `artifactApi.uploadAttachment()` | `POST /api/v1/artifacts` with chat purpose/conversation headers | Connected; private Storage, owner validation and worker extraction |
| Chat stream and cancellation | `moreAiApiStream()`, `cancelRun()` | `GET /api/v1/customer/agent-runs/{id}/stream`, `POST .../{id}/cancel` | Connected |
| Run detail, steps and events | `getRun()`, `getRunSteps()`, `getRunEvents()` | `GET /api/v1/customer/agent-runs/{id}`, `GET .../{id}/steps`, `GET /api/v1/agent-runs/{id}/events` | Connected |
| Workflow approvals | `customerToolApprovalApi` | `/api/v1/customer/tool-approvals` | Connected to durable owner/run-scoped approval lifecycle |
| Create Studio text/document/translation/presentation | `CreateView → handleStartPrompt → Chat` | Existing Chat message enqueue and Agent Run lifecycle | Connected as an explicit Chat handoff; the run is created when the Chat prompt is submitted |
| Create Studio image/video generation | No provider client exposed | No verified generation provider contract | Unavailable; must not create mock media or charge credits |
| Research history and artifacts | `customerApi.agentRuns()`, `artifactApi.list()/signedDownload()` | Agent Run and private Artifact routes | Connected |
| Analyse document upload | `knowledgeApi.upload()/list()/get()` | `POST /api/v1/customer/knowledge/documents/upload`, `GET /documents`, `GET /documents/{id}` | Connected to private ingestion and owner-scoped Knowledge Library |
| Analyse selected document with Agent | Knowledge document selection → Chat handoff | Durable Agent Run + `knowledge_search(document_ids)` | Source-integrated; retrieval is restricted to the selected ready document ID |
| Code Assistant analysis | `CodeView → handleStartPrompt` | Existing Chat Agent Run contract | Connected; no Python execution claim |
| Code snapshot save/list/download | `artifactApi.upload/list/signedDownload` | `POST/GET /api/v1/artifacts`, `POST /{id}/signed-download` | Connected; optional owner-verified Agent Run link |
| Tasks / Agent Run history | `customerApi.agentRunsPage()` | `GET /api/v1/customer/agent-runs` | Connected |
| Tasks / Run artifacts | `artifactApi.list()/signedDownload()` | `GET /api/v1/artifacts`, `POST /{id}/signed-download` | Newly connected in Tasks view; run relationship displayed |
| Workspace files | `workspaceApi` | `/api/v1/customer/workspaces` and nested file/version/run routes | Connected to versioned private Storage and CAS |
| Private artifacts | `artifactApi` | `GET/POST /api/v1/artifacts`, `POST /{id}/signed-download` | Connected; 2 MB object limit and owner checks |
| Profile update | `profileApi.update()` | `PATCH /api/v1/me/profile` | Connected |
| Security MFA/password | Supabase Auth MFA and password methods | Supabase Auth | TOTP factor management and password update; extended session/device inventory is unavailable |
| Notifications | `notificationApi` | `GET /api/v1/notifications`, preferences GET/PUT, read POST, read-all POST | Connected |
| EduTech learning progress | `learningApi.progress()/setProgress()` | `GET/PUT /api/v1/customer/learning/progress` | Connected; catalog, enrollment, certificates and protected video delivery are not present |
| Analytics usage | `customerApi.usageAnalytics(days)` | `GET /api/v1/customer/usage/analytics` → server-only SQL aggregate | Newly connected; 7/30/365-day historical aggregation from all matching usage records |
| Wallet / ledger / quotas | `customerApi.wallets()/ledger()/quotas()` | Customer wallet, ledger and quota read routes | Read-only connected |
| Payment top-up / checkout / subscription | No active payment mutation client | No checkout, payment-intent or verified webhook settlement contract/table/provider | Unavailable; no balance or entitlement mutation is claimed |
| Wi-Fi session history | `customerApi.networkSessions()` | `GET /api/v1/customer/network-sessions` | Read-only connected |
| Network speed test | Customer speedtest API client | `GET /api/v1/customer/network/speedtest/ping`, download, upload | Measures client ↔ MoreAI API path only; not an ISP throughput guarantee |
| Captive terms / consent / OTP / access activation | UI remains fail-closed | No complete customer consent, OTP send/verify or gateway session create/refresh/revoke API | Unavailable pending real gateway adapter and provider credentials |
| Access code redemption | `customerApi.redeemAccessCode()` | `POST /api/v1/customer/access-codes/redeem` | Connected but requires a valid network verification session first |
| Device pause/filter/session control | No active customer mutation client | No verified partner gateway device-control contract | Disabled; no simulated device status |
| Support request/ticket | No active ticket client | No support ticket table, workflow or official support provider | Unavailable; FAQ does not claim ticket submission |

## Contract correction in this increment

- Extended the typed Customer client to cover the already-existing conversation/session lifecycle routes: list sessions with `X-Next-Cursor`, read a session, cancel a session, read sequenced session events, update conversation metadata and archive a conversation. All methods use the authenticated FastAPI client and the backend's existing ownership checks. [Implementation report](./PHASE-09-CUSTOMER-CONVERSATION-SESSION-API-COVERAGE-20261113.md)

- Corrected the unused typed `conversationSessions` client method, which previously called `/api/v1/conversations/{id}/sessions` even though the FastAPI contract requires `/api/v1/conversations/{conversation_id}/sessions/{run_id}`. The typed method is now `conversationSession(conversationId, runId)` and targets the implemented route.
- Added `GET /api/v1/customer/usage/analytics?days=7|30|365` and its typed response contract.
- Added optional document ID filtering to the OpenManus `knowledge_search` tool schema/runtime. Analyse sends the selected ready document ID into the new Chat Agent Run, and the worker passes that exact ID to the existing owner/workspace-scoped pgvector RPC.
- Tasks now lists persisted private artifacts and downloads them using short-lived signed URLs.

## Real-provider blockers — do not bypass

### Captive Gateway
Production Supabase currently lists five verification methods: `gateway`, `gps`, `isp_api`, `mikrotik_hotspot`, and `radius`. All five have `adapter_ready=false`. The partner configuration API rejects enabling a method whose catalog adapter is not ready. No provider credentials or secret-vault resolver/contract was supplied in the connected configuration. Do not set adapter readiness or activate customer access until a real provider adapter, signature/nonce verification, consent record, OTP integration and session lifecycle are implemented and configured.

### EduTech
The production schema has `customer_learning_progress`, but no authoritative course/module catalog, enrollment, lesson delivery or protected video entitlement contract. Existing curated syllabus text is not to be represented as a remotely managed provider catalog.

### Payment
Wallet, immutable credit ledger, quota and entitlement records exist. There is no payment checkout/intent, webhook settlement, refund or top-up provider contract in the current schema. No credit balance may be changed by a frontend-only action.

### Support
No support ticket schema, response lifecycle or official support provider is configured. Do not present an informational FAQ toast as ticket submission.

## Verification boundary

- This is a source/schema inventory, not a live Customer runtime acceptance.
- No tests, lint, typecheck, build, browser checks, screenshots, API probes, worker execution, staging or E2E checks were run.
- Supabase schema and migration metadata were inspected read-only, except the explicitly recorded additive analytics migration.
- Production frontend/API deployment still needs a new deployment after the Vercel deployment quota recovers.

## Captive Gateway production inventory addendum

Read-only production counts at the time of this inventory: `network_providers=0`, `partner_networks=0`, `network_verification_configs=0`, `network_sessions=0`. All five network verification catalog methods are `adapter_ready=false`. There is no real gateway/network configuration or provider secret reference in the canonical project to connect an adapter against. The customer portal therefore remains fail-closed until a partner network and supported gateway/provider contract are onboarded.
