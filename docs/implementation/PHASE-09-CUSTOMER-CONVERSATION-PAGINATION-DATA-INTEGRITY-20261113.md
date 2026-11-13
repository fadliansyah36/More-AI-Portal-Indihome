# Phase 09 — Customer Conversation, Pagination & Screen Data Integrity

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: source-level integration and contract corrections only. Existing Customer UI visual system and navigation remain protected; no real tests or staging.

Baseline commit at start of this increment: `749ec489a808ffe5d02c1b753e4109a95dcfdb98`  
Latest source commit in this increment: `1bdce9de5a401214151beee752b1b918906f2185`  
Latest tracker commit: `f0c946386eb3c69185a179f36565700a4562e8dd`

## Implemented in this increment

### 1. Conversation and Agent Run response contracts
- Added FastAPI response models for Customer conversation create/list/detail, messages, Agent Run detail/list/steps, session detail/list/events, and Agent Run list/detail/steps/logs/thinking/progress/events.
- Customer conversation history now uses deterministic keyset pagination ordered by `updated_at DESC, id DESC`, with a backwards-compatible legacy `before` timestamp parameter and `X-Next-Cursor` response header.
- Added a typed `customerApi.conversationsPage()` client; Chat restoration now uses this cursor-aware method.
- Conversation and session ownership remains verified against the authenticated Customer principal. Session operations verify both conversation and run ownership.

### 2. Wallet ledger and usage pagination
- Wallet ledger and LLM usage now use stable `created_at DESC, id DESC` keyset pagination, return `X-Next-Cursor`, and retain the old timestamp `before` parameter for compatibility.
- Ledger supports an optional wallet ID, but validates that the selected wallet belongs to the authenticated user before querying entries.
- Added typed `ledgerPage()` and `usagePage()` methods.
- Token Ledger now pages through the selected active wallet rather than mixing ledger rows from different currency wallets.
- Benefit & AI Credit history now loads ledger rows only for the active wallet.
- Wi-Fi Session and Captive Success no longer sum balances from different currencies; both display one active wallet.

### 3. Workspace and approval contracts
- Added response models for workspace list/create/rename/archive, files, versions, signed downloads, members, workspace runs and CAS uploads.
- Added a Customer Agent Run step response model.
- Tool approval creation now verifies that the requested Agent Run belongs to the current Customer before invoking the approval RPC, and has a typed mutation response.
- Existing owner/member checks, owner-only workspace mutation, private Storage signed links and durable approval RPC remain in place.

### 4. WebSocket terminal parity
- Incremental Agent Run WebSocket frames now include `run.expired` in thinking and error logs.
- Idle WebSocket polling closes on the shared terminal set, including `timed_out`; it no longer leaves timed-out runs connected.

### 5. EduTech demo data removed from active Customer screens
- The Customer EduTech catalogue no longer presents local hardcoded modules as an active provider catalogue.
- The lesson detail screen no longer exposes local sample lessons or writes progress against a hardcoded `edu-1` module.
- The screen now clearly reports that official catalogue, enrollment, certificate and protected video delivery are unavailable until the EduTech provider contract is integrated.
- Existing saved learning progress remains readable; no fake course completion is written.
- This is a minimal content-integrity UI change required to prevent local examples from being mistaken for real provider-backed learning data.

## Important source commits
- `a7e216d25b974928db3ad8b1890ebdc855ef8610` — WebSocket incremental terminal parity.
- `09afd4566304df80d57837c9da2d86ce85a6bdf6` — updated_at keyset helpers.
- `e7de692244b77c899ffd7e87e4492b0def8df7d1` — Customer conversation schema and keyset pagination.
- `3353be22c0aac5a826ceb35499166eeb0302017b` — wallet ledger and usage pagination.
- `6e8f317242a48544afce6dbd785098f45f796db2` — typed page clients.
- `6b5aac829f1f055daad4aff3c3debd771d52450d` — active-wallet ledger pagination UI.
- `45378b8bbbbb3d1f612113ae134d310a0829b1b5` — Benefit Credit wallet-scoped history.
- `444f027a79dabf2aff33b5a4b856a4916881d7b4` — Chat restore via keyset conversation page.
- `399e103816073b3868d82e9aa03413f99f4661fa` — conversation/session response schemas.
- `a35ae2644f803459fef637bc8a1dcd338d790766` — Agent Run response schemas.
- `236bc7f4624ca32ebe5fff2fb6b5b5cb84d280bd` — workspace lifecycle response schemas.
- `0fb87358ae835786c23f2366f8da4009fa3e2c0c` — approval creation run ownership check.
- `d0a5b716c64f3c04bb34d1ac779e7fb7a22c0705` — Customer Agent Run step schema.
- `276f1a5e2dac435fb47dd09369e64fb3db75800f`, `675ffd7c95859ebf0853969701da2d45d2033c29` — currency-safe wallet display in Wi-Fi and captive success.
- `e4fe2b4b43e8a15c69737ec9cd026c389c86094a`, `b1830b17ff49fd9a8ba040087e1f8eb632aa2275`, `a1b8b6b52f2480dee0fb9e1d26d0ed13a63e1e62`, `70953f9fab7a0327f9ae392fa72ededa5d7946ed` — EduTech fail-closed catalogue and lesson views.
- `560b0d97b2511a45a254367c12645e62b2284ccd` — typed quota policy scope.


## Files and UI preservation
- Backend: `apps/api/app/main.py`, `apps/api/app/pagination.py`, and Customer routers for conversations, Customer context/wallet/network, Agent Runs, workspaces, artifacts, approvals, knowledge, learning, catalog and notifications.
- Frontend: `lib/api/client.ts`, `lib/api/knowledge.ts`, and Customer views for Files, Research, Workflow, Code Assistant, Chat, Token Ledger, Benefit Credit, Wi-Fi Session, Captive Success and EduTech.
- Documentation: Phase 09 action/API inventory, Phase 09 reconciliation report and Phase tracker.
- No source was copied from or replaced by a generic OpenManus UI. Existing Customer design system, navigation and component structure were retained. The only material content change removes local EduTech demo courses/lessons from active screens and replaces them with an explicit provider-unavailable state.
- UI screenshots were not captured because the requested boundary excludes browser/runtime verification; this is recorded as an unverified visual regression item, not as proof of visual acceptance.
- No Supabase schema or migration was changed in this increment.

## Provider and source-of-truth boundaries
- Gateway/OTP/consent/session activation remains disabled until official gateway APIs, credentials and verification contracts exist.
- EduTech catalog/enrollment/certificate/video remains unavailable until official provider APIs and protected video delivery are supplied.
- Payment checkout/settlement and support ticket submission remain unavailable without official contracts, credentials and server-side workflows.
- Image/video generation remains unavailable without a real configured media provider. No fake output, credit debit or success state is introduced.
- Code Assistant example snippets are local editor starter templates only; they are not executed and are not represented as customer or partner business data.

## Verification boundary
- All source changes were committed directly to `main`.
- No tests, lint, typecheck, build, browser check, screenshots, API probes, worker execution, staging, database migration or deployment were run, as instructed.
- This report records source-level changes only; it does not claim runtime or production acceptance.

## Remaining Phase 09 work
- Continue the complete route-by-route Customer authorization and response-schema audit, including notifications/profile, knowledge, artifact, catalog, network and all remaining Customer endpoints.
- Add pagination to remaining bounded collection routes where the Customer UI requires it, especially artifacts and workspace resources.
- Reconcile artifact and workspace navigation end-to-end across Research, Tasks, Files and Workflow without adding duplicate screens.
- Reconcile approval decision/recovery lifecycle and ensure UI reflects the durable RPC result without optimistic success.
- Continue removing any remaining local business-data fallbacks; retain only clearly identified static UI copy or editor starter templates.
- Phase 09 remains IN PROGRESS. Phase 10/11 remain gated and are not started by this source-only increment.

### Additional response-contract coverage
- Added typed FastAPI responses for Customer context, network session records, speedtest ping/upload, knowledge document upload/list/detail/retry/archive, agent catalog, model capability registry and tool catalog.
- Added explicit object response contracts for Customer message enqueue/cancellation, session cancellation, workspace member removal, access-code redemption and approval decision.
- Customer network session listing is bounded to 1–100 rows.
- Knowledge chunk `token_count` is nullable to match persisted records.
- Commits: `83f3c73e6548b84b18ef39671c685ce46f1d49e8`, `0d9bf31108b63622d0c3787b5b68e4d771c2b375`, `390abbc76680683ad4ca4d27438c517bcdfd5b0a`, `37b544099e7593e2e65102291ea7a4b7404c6e09`, `89d49cebb165a6d88d507aba531278cd2c3b627f`, `f9364d435297a9e20ce3f17946856f6b08a6b3d9`, `251aa620a5b7b709219e827f28ce4ada9347d10d`, `61ba3229ae19ca05cfa58a6c8fa4d79fb5276b5b`.
- Currency display refinements: Token Ledger does not show a fabricated zero balance when no active wallet exists and Wi-Fi Session does not append a currency without an active wallet. Commits `554707e14e7b4183c52591cd715a0ad75a1e3244`, `4ffa37989d66bf522d6d4e19b8b572fc5b168051`, `b15271a86378667bbf1955ab9b5f1030722cee05`.

### Artifact navigation pagination
- Private artifact listing now uses stable `created_at + id` keyset pagination, emits `X-Next-Cursor`, and resolves Chat attachment run links only for the current page rather than a fixed global link slice.
- Added typed `artifactApi.listPage()` and updated the Files screen to load artifact pages incrementally without losing already-loaded items. Legacy Research/Tasks/artifact readers request a bounded first page of 100 items.
- Commits: `ffc1b645f1a12eb9ca49112df65d0c84915a88f3`, `05f905a01eeba8eb57cdf4c8d2c8d3c2fc0e03ba`, `89a49091aac90d73c375ce8862958f24ce37d5af`, `2e6b0195aa8e477651951b643d82da062073ca42`.

### Approval lifecycle response reconciliation
- Approval request is idempotent at the RPC layer. The API now reloads the persisted approval row by approval ID and authenticated user after the RPC returns, then returns the actual persisted status rather than always fabricating `pending`. This preserves already-approved or expired state on duplicate requests.
- Approval decision now has a response schema matching the RPC JSON fields (`id`, `run_id`, `tool_key`, `status`, `decided_at`, `expires_at`).
- Commits: `5d80bf59e1c392a61b3cb4595f9d707695f0c4b1`, `3056161f5220b20af80038b1f1b8536c126ca19a`, `d36481af6b137c1ce67d2fda4f53f0153fe7ec31`.

### Profile identity contract
- Added explicit response schemas to `GET /api/v1/me` and `PATCH /api/v1/me/profile`, matching the authenticated Supabase user envelope and owner-scoped profile record.
- Commit: `0def174f55612520f192872b5fb669d31108b97d` (UUID import correction: `9ebd0e2f2aec39921fb32e2bd0e0a2c17bf9148e`).

### Agent Run history navigation parity
- Research and Workflow now consume the cursor-based Agent Run page client and can append older runs without duplicating already-loaded IDs.
- Code Assistant's run selector and project association now use the same keyset page client rather than the legacy timestamp-only list call.
- Workflow refreshes the first durable run page after an approval decision and resets its cursor to the refreshed snapshot.
- Commits: `b10375b2fb9960e2b3833a947be78e06b51d3a34`, `3ecab359ccd27428c2b41a2d4e6b4669f9447b3e`, `1bdce9de5a401214151beee752b1b918906f2185`.
