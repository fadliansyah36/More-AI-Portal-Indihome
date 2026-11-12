# Phase 07 Frontend Durable SSE Reconnect — 2026-11-12

## Scope

Implemented the frontend transport counterpart for the durable event replay contract already added to FastAPI. Existing UI components and visual design were not changed.

## Source and commit

- Target branch: `main`
- Source file: `lib/api/client.ts`
- Commit: `500510bbb041dc235d3b7a832d3dc314a6d86fc6`
- Tracker: `docs/implementation/PHASE-TRACKER.md`
- Capability inventory: `docs/implementation/openmanus-backend-capability-map.json`

## Implementation

The existing `moreAiApiStream` helper now accepts optional stream settings:
- `after`: initial durable event sequence cursor.
- `signal`: cancellation for active fetch/read and reconnect wait.
- `maxReconnects`: bounded reconnect attempts.
- `reconnectDelayMs`: bounded initial backoff delay.

On each connection/reconnection, it:
1. refreshes the Supabase Auth session and obtains the current access token;
2. sends `Last-Event-ID` when a numeric event cursor has been delivered;
3. parses event IDs and advances the cursor monotonically;
4. reconnects from the last delivered sequence after the server's `stream.timeout` boundary or transient network/5xx errors;
5. applies bounded exponential backoff;
6. does not retry terminal authentication, authorization, missing-resource or contract-validation errors;
7. stops after terminal run events (`run.completed`, `run.failed`, `run.cancelled`).

The token is not written into the cursor, event payload, or persistent client state.

## UI preservation

No page, route, component, CSS, token, navigation, copy or layout was modified. This is a transport-only client increment. The repository search found no current call site invoking `moreAiApiStream`; wiring it to a visible workflow component remains separate work and should preserve the existing screen contract.

## Verification boundary

No tests, lint, typecheck, build, browser QA, authenticated API call, SSE reconnect, worker/runtime, provider call, database migration or staging verification was run. This follows the existing testing/release gate. The implementation is committed source, not runtime acceptance.

## Remaining Phase 07/09 work

- Wire the stream helper into the existing workflow progress UI using the last durably processed event cursor and component lifecycle AbortSignal.
- Verify duplicate/out-of-order event handling and terminal-state convergence against persisted run state.
- Verify server disconnect/reconnect, replay after worker restart, outbox retry/dead-letter, lease expiry and cancellation races.
- Complete approval resume and adapter cancellation acceptance.
- Keep Phase 10 BLOCKED and Phase 11 NOT STARTED until test authorization and all acceptance evidence exist.

## Deployment

Vercel Git integration automatically deployed this source commit to both Production projects:
- Frontend: `dpl_DbSaKgdd8UJbhKPxERMkL1VmcwaR` — READY, aliases include `moreai.web.id` and `www.moreai.web.id`.
- API: `dpl_Hn8LSHR5Q6zxgEmy8u5Dn8NKT9Nw` — READY, alias includes `more-ai-api-more-ai.vercel.app`.

The deployments use source commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6`. Later documentation-only Production builds were canceled to preserve the release gate. No live HTTP/API/SSE/CORS or E2E verification was run; Vercel READY confirms deployment state, not runtime acceptance.
