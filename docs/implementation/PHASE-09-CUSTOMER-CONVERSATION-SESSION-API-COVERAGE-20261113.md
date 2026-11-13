# Phase 09 — Customer Conversation Session API Coverage

Date: 2026-11-13
Target branch: `main`
Source commit: `c3abf5fd606067e13ef752e5e115415ac2588979`

## Scope

Expose the already-implemented FastAPI conversation and durable-session lifecycle contracts through the existing typed Customer API client. This is a backend-contract/client integration increment; it does not add or redesign a Customer screen.

## Existing API contracts reconciled

The client now exposes the following existing FastAPI operations:

- `GET /api/v1/conversations/{conversation_id}/sessions` — owner-scoped durable session listing with keyset cursor metadata.
- `GET /api/v1/conversations/{conversation_id}/sessions/{run_id}` — retrieve a session only when both conversation and run belong to the authenticated Customer.
- `POST /api/v1/conversations/{conversation_id}/sessions/{run_id}/cancel` — request cancellation after the same dual ownership checks.
- `GET /api/v1/conversations/{conversation_id}/sessions/{run_id}/events` — retrieve safe, sequenced lifecycle events after the cursor.
- `PATCH /api/v1/conversations/{conversation_id}` — update conversation title/status.
- `DELETE /api/v1/conversations/{conversation_id}` — archive a conversation (the API's delete operation is a soft archive).

## Client changes

Updated `lib/api/client.ts`:
- Added reusable `CustomerConversationSession` and `CustomerConversationSessionEvent` contracts.
- Added `customerApi.conversationSessions()`, preserving the response cursor from `X-Next-Cursor`.
- Added `customerApi.updateConversation()` and `customerApi.archiveConversation()`.
- Added `customerApi.cancelConversationSession()` and `customerApi.conversationSessionEvents()`.
- All calls use the existing authenticated FastAPI fetch boundary; no direct browser Supabase data access was introduced.

## Security and UI

No FastAPI route, database schema, migration, RLS policy, storage policy, provider configuration, credential, page, component, navigation, layout or style was changed. The client methods target existing routes whose backend dependencies enforce Customer identity and conversation/run ownership. Existing UI behavior is preserved.

## Validation and deployment

Per explicit product-owner instruction, no tests, lint, typecheck, build, browser checks, screenshots, API probes, worker execution, staging, migrations or deployment were performed. The commit is source-level contract coverage only; runtime behavior remains unverified.

## Phase status and next work

Phase 09 remains **IN PROGRESS**. Continue auditing every Customer view and typed client action against FastAPI schemas and Supabase ownership/data contracts. Next provider-independent targets are any remaining missing typed client methods and lifecycle seams for conversations, runs, workspace files, artifacts, approvals, wallet/ledger, quotas, learning progress and notifications. Gateway/OTP, media generation, payment settlement, authoritative EduTech catalog/video delivery and support remain blocked pending official provider specifications and secure configuration. Phase 10 is not accepted under the no-testing constraint; Phase 11 remains blocked.
