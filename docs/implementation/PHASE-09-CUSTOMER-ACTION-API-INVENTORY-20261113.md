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
| Home identity | `profileApi.get()` | `GET /api/v1/me`, `PATCH /api/v1/me/profile` | Connected; FastAPI response schemas now declare the authenticated user/profile envelope; profile reads/updates use the configured Customer API origin; Auth-only identity fallback remains limited to transient identity outage |
| Home Agent Run summary | `customerApi.agentRunsPage()` | `GET /api/v1/customer/agent-runs` with keyset cursor | Connected |
| Home wallet and entitlement | `customerApi.wallets()`, `entitlements()` | `GET /api/v1/customer/wallet`, `GET /api/v1/customer/entitlements` | Connected |
| Customer context | `customerApi.context()` | `GET /api/v1/customer/context` | Connected |
| Chat conversation restore | `customerApi.conversationsPage()`, `getConversation()` | `GET /api/v1/customer/conversations`, `GET /api/v1/customer/conversations/{id}` | Connected; stable `updated_at + id` keyset pagination with `X-Next-Cursor`; Chat restore uses the typed page client |
| Chat message / Agent Run enqueue | `customerApi.sendMessage()` | `POST /api/v1/customer/conversations/{id}/messages` | Connected; atomic message/run/attachment RPC and idempotency key |
| Chat attachments | `artifactApi.uploadAttachment()` | `POST /api/v1/artifacts` with chat purpose/conversation headers | Connected; private Storage, owner validation and worker extraction |
| Chat stream and cancellation | `moreAiApiStream()`, `cancelRun()` | `GET /api/v1/customer/agent-runs/{id}/stream`, `POST .../{id}/cancel` | Connected; terminal states include timed_out/expired; Customer, conversation-session and general Agent Run cancellation routes now short-circuit already-terminal owner-scoped runs, and Chat reflects immediate cancel vs worker-accepted cancellation; SSE reconnect honors Last-Event-ID |
| Run detail, steps and events | `getRun()`, `getRunSteps()`, `getRunEvents()` | `GET /api/v1/customer/agent-runs/{id}`, `GET .../{id}/steps`, `GET /api/v1/agent-runs/{id}/events` | Connected; Pydantic response schemas cover run detail/list/steps/logs/thinking/progress/events and customer steps |
| Workflow approvals | `customerToolApprovalApi`, `customerApi.agentRunsPage()` | `/api/v1/customer/tool-approvals`, Agent Run history | Connected to durable owner/run-scoped approval lifecycle; approval creation pre-verifies run ownership and reloads the persisted row after idempotent RPC; cursor pagination and incremental history are wired in Workflow; decision response includes durable pause/resume outcome; worker recovery/race acceptance remains |
| Create Studio text/document/translation/presentation | `CreateView → handleStartPrompt → Chat` | Existing Chat message enqueue and Agent Run lifecycle | Connected as an explicit Chat handoff; the run is created when the Chat prompt is submitted |
| Create Studio image/video generation | No provider client exposed | No verified generation provider contract | Unavailable; must not create mock media or charge credits |
| Agent Studio catalog | `customerApi.agents()` | `GET /api/v1/agents` | Connected; FastAPI response schema declares enabled agent catalogue; explicit typed client uses configured Customer API origin |
| Research history and artifacts | `customerApi.agentRunsPage()`, `artifactApi.listPage()/signedDownload()` | Agent Run and private Artifact routes | Connected; Research uses keyset run and artifact pages with incremental loading; artifact references are owner-scoped and signed downloads remain server-issued |
| Analyse document upload | `knowledgeApi.upload()/listPage()/get()` | `POST /api/v1/customer/knowledge/documents/upload`, `GET /documents`, `GET /documents/{id}` | Connected to private ingestion and owner-scoped Knowledge Library; Analyse document selection and Knowledge Library now load document pages incrementally; upload/list/detail/retry/archive response schemas declared; document chunks now use owner-scoped after_chunk_index pagination and exact total count; retry and archive remain owner-scoped |
| Analyse selected document with Agent | Knowledge document selection → Chat handoff | Durable Agent Run + `knowledge_search(document_ids)` | Source-integrated; retrieval is restricted to the selected ready document ID |
| Code Assistant analysis | `CodeView → handleStartPrompt` | Existing Chat Agent Run contract | Connected; no Python execution claim |
| Code snapshot save/list/download | `artifactApi.upload/listPage/signedDownload` | `POST/GET /api/v1/artifacts`, `POST /{id}/signed-download` | Connected; Code Assistant snapshot history and Agent Run selector load incrementally; optional owner-verified Agent Run link |
| Tasks / Agent Run history | `customerApi.agentRunsPage()` | `GET /api/v1/customer/agent-runs` | Connected; succeeded/failed/cancelled/timed_out/expired are all treated as terminal for active-vs-finished filtering |
| Tasks / Run artifacts | `artifactApi.listPage()/signedDownload()` | `GET /api/v1/artifacts`, `POST /{id}/signed-download` | Connected in Tasks view with keyset pagination; run relationship displayed |
| Workspace files | `workspaceApi`, `customerWorkspaceApi` | `/api/v1/customer/workspaces` and nested file/version/member/run routes | Connected to database-side owner/member union keyset pagination (no 1,000-row fan-in); Files loads workspace/file/version pages, resolves exact server-side path/version before CAS upload, exposes soft-delete/restore, archives deleted versions, copies restore bytes into the next immutable Storage path, and supports explicit archived-version download; owner-only workspace rename/archive/member removal retained |
| Private artifacts | `artifactApi.listPage()/upload()/signedDownload()` | `GET/POST /api/v1/artifacts`, `POST /{id}/signed-download` | Connected; owner-scoped list has stable keyset pagination and Files, Tasks, Research, Workflow, Results and Code screens load pages incrementally; 2 MB object limit, private Storage and owner checks retained |
| Profile update | `profileApi.update()` | `PATCH /api/v1/me/profile` | Connected |
| Security MFA/password | Supabase Auth MFA and password methods | Supabase Auth | TOTP factor management and password update; extended session/device inventory is unavailable |
| Notifications | `notificationApi.listPage()` and preference/read methods | `GET /api/v1/notifications`, preferences GET/PUT, read POST, read-all POST | Connected; notification history uses stable `created_at + id` cursor pages and the screen loads older notifications incrementally; preferences and read actions remain owner-scoped |
| EduTech learning progress | `learningApi.progress()/progressPage()` | `GET /api/v1/customer/learning/progress` with `(completed_at,id)` keyset cursor and exact count RPC | Saved progress is owner-scoped, keyset-paged without the previous 1,000-row cap, and returns exact total_count; EduTech overview reads the total. Local sample courses/lessons and fake progress writes remain removed. Progress mutation is withheld until official catalog identifiers exist; catalog, enrollment, certificates and protected video delivery remain unavailable |
| Analytics usage | `customerApi.usageAnalytics(days)` | `GET /api/v1/customer/usage/analytics` → server-only SQL aggregate | Newly connected; 7/30/365-day historical aggregation from all matching usage records |
| Wallet / ledger / quotas | `customerApi.wallets()/ledgerPage()/usagePage()/quotas()` | Customer wallet, ledger and quota read routes | Read-only connected; ledger and usage use stable `created_at + id` keyset pagination; ledger can be scoped to an owner-verified wallet; Token Ledger and Benefit Credit use the active wallet; Wi-Fi Session and Captive Success no longer add unlike currencies; quota reads include platform/global/user policy scope and exact active window |
| Payment top-up / checkout / subscription | No active payment mutation client | No checkout, payment-intent or verified webhook settlement contract/table/provider | Unavailable; no balance or entitlement mutation is claimed |
| Wi-Fi session history | `customerApi.networkSessionsPage()` | `GET /api/v1/customer/network-sessions` | Read-only connected with stable `started_at + id` keyset pagination; Devices, Benefit Credit, Wi-Fi Session and Captive Success use paged responses |
| Network speed test | `customerApi.networkSpeedtestPing/Download/Upload()` | `GET /api/v1/customer/network/speedtest/ping`, download, upload | Typed FastAPI client now matches the actual upload response (`status`, `received_bytes`, `server_receive_ms`); measures client ↔ MoreAI API path only, not an ISP throughput guarantee ([report](./PHASE-09-CUSTOMER-SPEEDTEST-TYPED-API-20261113.md)) |
| Captive terms / consent / OTP / access activation | UI remains fail-closed | No complete customer consent, OTP send/verify or gateway session create/refresh/revoke API | Unavailable pending real gateway adapter and provider credentials |
| Access code redemption | `customerApi.redeemAccessCode()` | `POST /api/v1/customer/access-codes/redeem` | Connected but requires a valid network verification session first |
| Device pause/filter/session control | No active customer mutation client | No verified partner gateway device-control contract | Disabled; no simulated device status |
| Support request/ticket | No active ticket client | No support ticket table, workflow or official support provider | Unavailable; FAQ does not claim ticket submission |

- Chat workspace context: Chat loads the owner/member workspace page list, allows selection for new conversations, restores the stored `workspace_id`, and sends it through `POST /api/v1/customer/conversations`. FastAPI validates `agent.run.create` at conversation binding and message enqueue; the existing atomic enqueue RPC persists that conversation workspace ID onto the Agent Run. The existing Workflow screen remains the PRD task/run monitor.
- Workspace authorization: read endpoints require `workspace.read`; direct file upload/delete/restore require `workspace.manage`; workspace-scoped run listing requires `agent.run.read`; workspace identity rename/archive and member removal remain owner-only. Active member access is resolved through `roles`, `role_permissions`, and `permissions`, not membership status alone.
- Workspace member navigation decision: Master PRD section 6.1 does not specify a Customer workspace-member administration screen, and the current API has no invitation contract. No incomplete member-management screen was added. The existing member list/removal API remains owner/member scoped.
- Workflow approvals now render persisted approved/denied/expired/consumed history and update the local decision timestamp from the API response. Files artifact pagination now deduplicates IDs and preserves retry state.

## Contract correction in this increment

- Extended the typed Customer client to cover the already-existing conversation/session lifecycle routes: list sessions with `X-Next-Cursor`, read a session, cancel a session, read sequenced session events, update conversation metadata and archive a conversation. All methods use the authenticated FastAPI client and the backend's existing ownership checks. [Implementation report](./PHASE-09-CUSTOMER-CONVERSATION-SESSION-API-COVERAGE-20261113.md)

- Corrected the unused typed `conversationSessions` client method, which previously called `/api/v1/conversations/{id}/sessions` even though the FastAPI contract requires `/api/v1/conversations/{conversation_id}/sessions/{run_id}`. The typed method is now `conversationSession(conversationId, runId)` and targets the implemented route.
- Added `GET /api/v1/customer/usage/analytics?days=7|30|365` and its typed response contract.
- Added optional document ID filtering to the OpenManus `knowledge_search` tool schema/runtime. Analyse sends the selected ready document ID into the new Chat Agent Run, and the worker passes that exact ID to the existing owner/workspace-scoped pgvector RPC.
- Tasks now lists persisted private artifacts and downloads them using short-lived signed URLs.


- Customer run streaming now treats both `run.timed_out` and `run.expired` as terminal. Chat maps those events and persisted polling statuses to explicit terminal messages instead of leaving the run in a generic in-progress state (commits `1710a01a`, `750aa794`).
- Profile, notification, tools catalog and model-capability requests now use the configured Customer API origin, preserving role-specific API routing when `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` is configured (commit `00974162`).
- Agent Studio's `GET /api/v1/agents` request is exposed as the typed `customerApi.agents()` contract rather than an inline generic request (commit `4e709c28`).


## Workspace union pagination and immutable file lifecycle — 2026-11-13

- Workspace list no longer fetches separate owner/member collections and merges them in memory. FastAPI calls `moreai_customer_workspaces_page`, which unions active owner/member workspace IDs and applies a stable database keyset cursor. Supporting partial indexes are applied.
- Customer delete is a soft-delete with version-history archival. Customer restore validates the stored object hash/size, copies it into the next version-addressed Storage path, and commits metadata with CAS semantics.
- OpenManus Worker restore uses a lease-fenced RPC and the same immutable object-copy rule. The old worker restore RPC overload is no longer executable by `service_role`.
- Files screen exposes deleted state, restore/delete actions, exact path lookup before upload, and explicit download of archived versions. Upload into a deleted path requires restore first.
- Conversation session detail now includes all persisted timing/cancellation lifecycle fields; conversation attachment response items are typed.
- Workspace member/run API contracts remain owner/member-scoped and paginated. The current UI does not contain a dedicated member/run management screen.
- Knowledge Library list and document chunk detail are paged and owner-scoped, with exact chunk totals. Learning progress is also keyset-paged with exact total count and no 1,000-row cap; progress writes remain fail-closed until official catalog IDs exist.
- See [Workspace union pagination & immutable file lifecycle report](./PHASE-09-CUSTOMER-WORKSPACE-UNION-LIFECYCLE-20261113.md).

## Additional reconciliation — 2026-11-13

- FastAPI response models now explicitly cover wallet, ledger, usage, entitlement, quota, artifact, workspace CAS upload, learning progress, tool approval list and notification contracts (see [workspace/quota/run reconciliation](./PHASE-09-CUSTOMER-WORKSPACE-QUOTA-RUN-RECONCILIATION-20261113.md)).

- Centralized Agent Run status semantics in `lib/api/agent-run-status.ts`; Home, Research, Tasks and Workflow now share terminal/active classifications and localized labels for queued, pending, running, approval-waiting, succeeded, failed, cancelled, timed-out and expired states.
- Backend Agent Run activity history now includes `run.expired` in logs/thinking and marks it as an error-level terminal event.
- Workspace archive now refuses to archive while any known active state exists: queued, pending, running, awaiting_approval or waiting_approval.
- Wallet display now uses one active primary wallet rather than summing balances with potentially different currencies.
- Workspace CAS upload result is represented by `CustomerWorkspaceUploadResult` rather than `Record<string, unknown>`.
- Customer quota reads now include both platform/global and user policies, retrieve the exact active window for each policy, and expose a declared FastAPI response schema. Usage lookup is keyed to the policy and its computed active window, not a user-only scope filter.


## 2026-11-13 continuation — conversation, pagination and data integrity

- FastAPI response schemas now cover Customer conversation/message, session/list/events, Agent Run list/detail/steps/logs/thinking/progress/events, and workspace lifecycle resources.
- Customer conversation history uses stable `updated_at + id` keyset pagination; ledger and usage use stable `created_at + id` keyset pagination. Legacy `before` timestamp parameters remain for compatibility.
- Token Ledger loads additional entries only for the active wallet; Benefit Credit history is similarly wallet-scoped. Wi-Fi Session and Captive Success display a single active wallet instead of summing currencies.
- Tool approval creation checks that the requested run belongs to the authenticated Customer before calling the approval RPC.
- EduTech Customer screens no longer present local sample courses/lessons as live catalogue data or write progress for a hardcoded sample module. Saved progress remains readable while official catalog/video integration is blocked.
- See [Conversation, pagination & screen data integrity report](./PHASE-09-CUSTOMER-CONVERSATION-PAGINATION-DATA-INTEGRITY-20261113.md).


- Additional FastAPI response models now cover Customer context, network session records, speedtest ping/upload, Knowledge Library document operations, agent/model/tool catalogs, message/session cancellation, workspace member removal and approval decisions. Network session listing is bounded to 100 rows. See [Conversation, pagination & screen data integrity report](./PHASE-09-CUSTOMER-CONVERSATION-PAGINATION-DATA-INTEGRITY-20261113.md).

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


## 2026-11-13 late continuation — pagination, cancellation and schema reconciliation

- Added incremental artifact loading to Tasks, Research, Workflow, Hasil Pekerjaan and Code Assistant; Code Assistant also pages the Agent Run selector used for owner-verified artifact linkage.
- Added incremental Knowledge Library selection in Analyse and paged network-session history to the Wi-Fi status screens.
- Token Ledger now deduplicates page appends and retains a retryable pagination error state.
- Workspace CAS failure reconciliation now refreshes via `filesPage` and restores the next cursor rather than falling back to a truncated legacy list.
- Customer cancellation endpoints now return terminal statuses without invoking the deployed cancellation RPC for succeeded/failed/cancelled/timed_out/expired runs. The RPC itself still needs a forward-only migration for direct-call terminal parity; no migration was applied.
- Read-only Supabase schema inspection aligned the Customer network nested response, workspace file nullable fields and artifact JSONB metadata. Profile identity now has a dedicated FastAPI response model.
- See [Customer pagination, lifecycle & contract hardening](./PHASE-09-CUSTOMER-PAGINATION-LIFECYCLE-CONTRACT-HARDENING-20261113.md).


## 2026-11-13 authorization and collection pagination continuation

- Customer router endpoints for context, conversation/message lifecycle, Agent Runs, network-session history, wallet, ledger, usage, analytics, entitlements, quota and access-code redemption now use `customer_principal` instead of generic bearer authentication. The principal resolver excludes active Partner memberships and platform-privileged assignments from the Customer API.
- Notification list/read/read-all and preference read/update endpoints now use the same Customer principal. Notification rows remain user-scoped and keyset-paginated by `created_at,id`.
- Agent, tool and model capability catalogues used by Customer screens now require the Customer principal. Partner and platform APIs remain separate.
- Incremental page loading now exists for artifact collections in Artifact Results, Workflow and Code Assistant; the Analyse document selector uses paged Knowledge Library data; Code Assistant Agent Run selection loads additional run pages. Existing notification, approval, workspace/file/version, conversation/message, Agent Run, ledger and usage page cursors remain wired.
- Approval decision state is rendered from the durable response. Agent Run refresh is independent and may show a refresh warning without rolling back or misreporting a committed approval decision.
- Owner-scoped cancellation routes short-circuit already-terminal runs. The response status union includes `cancel_requested`, `cancelled`, `succeeded`, `failed`, `timed_out` and `expired`.
- Report: [Customer authorization, pagination & lifecycle continuation](./PHASE-09-CUSTOMER-AUTH-PAGINATION-LIFECYCLE-20261113.md).

This remains a source-level inventory. It is not proof of runtime authorization, Supabase RLS behavior, complete pagination under concurrent writes, or Customer-to-Worker E2E. No tests, builds, lint, typecheck, browser/API probes, staging, migrations, live Supabase writes, provider calls or deployment were performed in this continuation.


## 2026-11-14 source audit addendum

### Customer authorization/response contract coverage
A source-level scan of the 10 Customer/shared router modules counted 77 route handlers. All 77 route signatures require `customer_principal`; the Customer WebSocket handlers resolve the bearer token and then call `require_customer_context`. That principal rejects active Partner memberships and privileged Platform assignments. Owner checks and membership/permission checks remain enforced by the individual route services.

JSON routes declare Pydantic response models. The intentional transport exceptions are Customer Agent Run SSE, shared run-event SSE, binary speed-test download and WebSocket message envelopes. This scan is not a live authorization/RLS test and does not prove cross-tenant denial at runtime.

### Chat RAG citations
Assistant message responses now include a typed `citations` array. FastAPI resolves each assistant message's `run_id` to an owner-scoped `agent_runs.output.citations` record, validates UUID chunk/document IDs, exact `[source:<chunk_id>]` marker, title, similarity and source offsets, and returns only the safe citation projection. The same enrichment is used for conversation detail and older-message keyset pages. Chat initial restore, older history and resumed-run completion restore the structured citations.

### Activity transport privacy
Conversation session event replay and Customer Agent Run SSE now share the safe activity metadata contract. Raw tool arguments, tool observations, provider payloads and checkpoint state bodies are not sent to the Customer browser. Terminal SSE sends only final answer text and validated citations plus a bounded error code.

### Approval decision event contract
The forward-only migration is applied to canonical Supabase project `uunfgimtokhucegqbpce` as version `20261113182657`. Read-only schema inspection confirms the helper is installed and the decision RPC contains the `run.resume_queued` event path. No runtime approval flow was executed.


### Event-history privacy closure
The direct Agent Run event-history endpoint now uses the same safe allowlist as logs/thinking/WebSocket/SSE. Customer SSE terminal payloads are projected to final answer text, validated citations and a bounded error code. Raw event payloads and provider/tool internals are not part of the Customer event response contract.

### Final RAG marker contract
Knowledge Search returns an explicit validated `citation_marker` for each chunk. The final model instruction requires exact markers; the durable runtime resolves them against retrieved chunk IDs, stores chunk/document provenance in Agent Run output, and strips markers from visible prose. Conversation detail and keyset message history restore citations through the assistant message's owner-scoped `run_id`.
