# Phase 09 — Customer Conversation, Pagination & Screen Data Integrity

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: source-level integration and contract corrections only. Existing Customer UI visual system and navigation remain protected; no real tests or staging.

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
