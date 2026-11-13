# Phase 09 — Customer Workspace, Quota & Run-State Reconciliation

Date: 2026-11-13  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Scope: source-level integration corrections across existing Customer UI, FastAPI and Supabase-backed contracts. No UI redesign.

## Implemented

### 1. Unified Agent Run status semantics
- Added `lib/api/agent-run-status.ts` as the shared frontend source for active/terminal classification and localized labels.
- Home, Research, Tasks and Workflow now consume the shared status semantics.
- `timed_out` and `expired` are terminal in every listed view; Tasks no longer leaves them in the active filter and Workflow counts them as terminal.
- Research now labels statuses consistently and describes terminal runs without output as non-successful terminal results.
- FastAPI Agent Run logs/thinking now includes `run.expired` and classifies it as an error-level terminal activity.
- Commits: `ced4b1a923fc5e04b401866a7c13c08b866cff14`, `56cf19aaae82bc2e9bc931b4b9f37f71bfc3bb1d`, `374d357f7cbd90b7e965fce74abf824e8c604d1f`, `6a295a7abee94aab0eb59d0862be032799a97f26`, `cf807f5d25de3cf68f3a8bfbfaba432a9076d879`, `4d1d98a1b0665bf1490615f18230bde16df0b5e9`, `441fd1928e913684dccd37f8dcd6f6602c7e8b78`, `1ca40c925c4c25dc24626e02c5f08a66eb27f9b4`.

### 2. Workspace lifecycle guard and typed upload response
- Workspace archive now checks queued, pending, running, awaiting_approval and waiting_approval runs before allowing an archive.
- Customer workspace CAS upload has an explicit TypeScript response contract matching the Supabase RPC result fields: workspace/file IDs, path, version, Storage path, SHA-256, byte size, update time and replay indicator.
- Existing owner-only rename/archive/member removal and member-scoped file access remain intact.
- Commits: `2362b390c25c6ff5ec96e06e75eef6201e9f0858`, `d3cbc03070f929209654e2eecef29d6b38ea7352`.

### 3. Wallet currency correctness
- Benefit Credit no longer sums wallet balances across currencies.
- It displays one active primary wallet, matching the Home screen's active-wallet selection.
- Commits: `2746c8726ebcbb83a540a740e064e3c67eba2e13`, `0e8d4ead0e54c30cf08a8059820844cab4aac337`, `0d162ced6c31660206e56947dc20e76eb5302144`, `81db20e0fffca4db13f384aeca65d179188819d6`.

### 4. Quota scope and active-window correctness
- Customer quota reads now include enabled platform/global policies as well as user policies.
- Usage rows are retrieved by exact policy ID and the active time window computed using the same epoch-window boundary as the quota reservation RPC; the previous user-only usage filter could hide platform/global consumption.
- Added `CustomerQuotaResponse` and `CustomerQuotaUsageResponse` Pydantic response schemas to the FastAPI route.
- Commits: `2479c408e57c727c1adf88f124fd6f2b22d8e332`, `bbf67837e35a9c9d9d1d95775140eb6bd3943ffd`, `a1b85e52b348a88d87ecc3c7abeec26410c2c069`.

## Authorization and contract review
- Workspace routes use `customer_principal`; workspace file/version operations verify active owner/member access; rename, archive and member removal require owner authority.
- Wallet, ledger, usage, entitlement and quota routes resolve the Customer context server-side before selecting records for the authenticated user.
- Learning progress and tool approvals use `customer_principal` and pass the authenticated user ID into server-side RPCs.
- Artifact list/upload/download use Customer principal and owner-scoped artifact metadata; signed URLs are generated server-side against private Storage.
- Notification and profile routes remain user-scoped shared account resources; Supabase browser use remains Auth-only in Customer screens.
- This is a source inspection, not a security acceptance or live RLS proof.

## UI/UX impact
- Existing page layouts, visual hierarchy, colors, typography, navigation and interactions were not redesigned.
- Changes to existing screens are limited to Agent Run status labels/classification and preventing cross-currency wallet arithmetic.
- No screenshots were generated because the requested execution boundary excludes browser/runtime checks.

## Verification boundary
- Changes were committed directly to `main`.
- No tests, lint, typecheck, build, browser checks, screenshots, API probes, worker execution, staging, migrations, or deployment were run for this increment.
- No claim is made that production runtime behavior has been verified.

## Remaining Phase 09 work
- Continue route-by-route response-model and authorization reconciliation for all Customer-facing endpoints, especially conversation/session, workspace, artifact and notification contracts.
- Finish lifecycle navigation and refresh consistency for workspace files/versions, run artifacts and approvals where existing screens expose the actions.
- Review quota/wallet/ledger pagination and idempotency contracts without changing immutable financial ledger semantics.
- Provider-dependent Gateway/OTP, EduTech catalog/video, payment settlement and support adapters remain blocked until official provider contracts, credentials and server-side integration details are available; do not introduce mocks.
- Phase 09 remains IN PROGRESS. Phase 10 must not start until the Customer API integration gaps are closed and documented.

### 5. Additional API contract alignment
- Corrected the Customer speed-test upload response type to match FastAPI's actual `{ status, received_bytes, server_receive_ms }` payload.
- Added `workspace_restore_version` to the frontend tool-approval request union to match the FastAPI `ApprovalRequest` Literal contract.
- Commits: `760b6f50b5e9abb4eede4f562349fb195cbd0fd9`, `532286dc5454a1007a2873ac55ced312d32e5bb7`.

### 6. Deleted workspace file download semantics
- Workspace file signed-download now reads `deleted_at` and refuses to issue a link for a deleted current version. Explicit prior immutable versions remain addressable through version history.
- Commit: `2b54081947a234194e8d759e1a2ba2379d0b0771`.

### 7. Customer workspace CAS recovery
- The existing Files screen now refreshes the selected workspace file list after a failed CAS upload attempt. This reconciles the client version after a version conflict or an ambiguous response where the server may already have committed the immutable version.
- No layout or visual behavior was changed.
- Commit: `937fb8c4283d0ffd73257710a20d263ba1bbfa0f`.
