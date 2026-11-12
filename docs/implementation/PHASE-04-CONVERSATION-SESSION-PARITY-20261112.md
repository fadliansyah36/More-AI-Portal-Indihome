# Conversation Session Parity Increment — 2026-11-12

## Implemented

- Added authenticated `GET /api/v1/conversations/{conversation_id}/sessions?limit=50`.
- Validates ownership of the conversation before listing sessions.
- Filters durable `agent_runs` by both conversation ID and authenticated user ID.
- Returns lifecycle metadata (status, attempt, timestamps, heartbeat, cancellation request, checkpoint key) only; does not expose prompts, outputs, tool arguments or observations.
- Added typed `conversationSessions(conversationId, limit)` in the existing Customer API client.

## Commits

- FastAPI: `0d92d72980c979589bcce4cf2e895b69b8fa902d`
- Typed client: `3628d366256f47e3c28a4e258d42de7c1731c5f1`
- Tracker: `9d78a57e8bdba035b7a42b9ee069811bd036b07b`

## Phase status and limitations

This is a real API/client contract for reading persisted conversation sessions. It does not yet provide parity for upstream server session creation/update/delete, websocket channels, log/thinking tracker, or Flow Engine lifecycle. Workspace file upload/update/delete/rename still require a lease-fenced mutation contract; do not bypass immutable CAS metadata with direct table writes. Browser/Python execution remains fail-closed until isolated supervisor infrastructure is present.

## Verification boundary

No tests, typecheck, lint, build, OpenAPI generation, browser E2E, staging, or deployment were run. Source commits only; no runtime acceptance is claimed.

## Next execution

Continue Phase 04 with a durable Flow/session state model and lease-fenced workspace file lifecycle. Then close Phase 07 recovery gates, Phase 08 upstream agent/tool/provider parity, Phase 06 API/authorization contracts, and Phase 09 existing Customer screen bindings in the mandated order.
