# Phase 09 — Customer Agent Run Stream Terminal Lifecycle

Date: 2026-11-13
Target branch: `main`
Implementation commits:
- `414f751d6cf985c5d4416664c6e41de81b979e34` — recognize the durable worker `timed_out` state as terminal in the Customer SSE endpoint and emit the matching `run.timed_out` event when no terminal event remains to replay.
- `078fe6bf78277e4fb785fae8d07532872a45c4c1` — close the Customer SSE connection immediately after replaying a persisted terminal lifecycle event, preventing the same terminal event from being emitted again on the next polling iteration.

## Scope and reason

The durable worker already records timeout as a first-class terminal state and emits `run.timed_out`. The Customer-specific SSE endpoint at `GET /api/v1/customer/agent-runs/{run_id}/stream` did not include `timed_out` in its terminal-state fallback. A timed-out run could therefore keep the stream open until the requested stream window expired. In addition, persisted terminal events were yielded without ending the stream, allowing the following poll to emit a second synthetic terminal event.

## Implementation

- Added `timed_out` to the Customer SSE terminal status set.
- Mapped the timeout terminal state to the existing `run.timed_out` event contract; succeeded, cancelled, failed and expired mappings remain intact.
- Return from the stream generator immediately after replaying a persisted terminal event (`run.completed`, `run.failed`, `run.cancelled`, or `run.timed_out`).
- No UI files, routes, navigation, styles, database schema, migrations, provider configuration, or credentials were changed.
- The existing frontend stream URL and event transport remain unchanged.

## Data flow

Existing Customer frontend stream client → authenticated Customer FastAPI SSE endpoint → owner-scoped durable run/events in Supabase → replayable terminal event → stream closes.

## Security and compatibility

- The endpoint still verifies run ownership through `customer_principal` and `owned_record`.
- No event payload fields or authorization behavior were widened.
- No browser-to-Supabase business-data access was introduced.
- This is a lifecycle correctness increment, not proof of full OpenManus runtime parity or real provider operation.

## Validation and deployment

Per product-owner instruction, no tests, lint, typecheck, build, browser checks, live API calls, worker execution, provider calls, staging, migration, or deployment were performed. This report records source changes only; runtime behavior remains unverified.

## Phase status and next work

Phase 09 remains **IN PROGRESS**. This patch closes one Customer stream lifecycle gap only. Continue the full Customer action-to-API inventory against every existing Customer view and backend contract, prioritize provider-independent domain contracts, and keep provider-dependent gateway/OTP, media generation, payment settlement, authoritative EduTech catalog/video delivery, and support actions blocked until official provider specifications and credentials/configuration are supplied. Phase 04, 06, 07 and 08 dependencies remain open; Phase 10 is not accepted under the current no-testing instruction and Phase 11 remains blocked.
