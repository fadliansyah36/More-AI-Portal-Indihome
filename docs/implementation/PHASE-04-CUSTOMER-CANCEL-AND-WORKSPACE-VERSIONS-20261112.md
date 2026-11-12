# Customer Workflow Integration Increment — 2026-11-12

## Objective
Continue the operational Customer → FastAPI → durable OpenManus worker → Supabase → streamed result path without replacing or restyling the MoreAI UI.

## Changes committed to main

### 1. Customer Chat durable cancellation
File: `components/views/chat-view.tsx`
- Exposes a stop action while a durable agent run is active.
- Calls the authenticated `POST /api/v1/agent-runs/{run_id}/cancel` API through the existing typed Customer API client.
- Displays cancellation-request state and retains the existing stream until the worker reports its durable terminal event.
- Renders a terminal cancelled result as a normal run outcome rather than presenting it as an API failure.
- Preserves the existing Chat screen layout; only adds a contextual stop control during active execution.

### 2. Customer workspace version history UI
File: `components/views/files-view.tsx`
- Adds a version-history action to each listed workspace file.
- Loads version metadata through the existing authenticated FastAPI workspace version endpoint.
- Shows version number, current-version marker, commit timestamp, size and SHA-256.
- Downloads a selected historical version using a short-lived signed URL from the existing FastAPI endpoint.
- Does not access Supabase Storage directly from the browser and does not expose service-role credentials.
- Keeps the existing artifact library and visual language intact.

## Git commits
- `0544d3935928d17d2ec2d135ecfe4b0948e4c2b8` — Customer durable run cancellation.
- `02f75d13983cf7791329f909882b126ccfb79ce8` — Customer workspace version history UI.

## Existing backend capability reused
- Worker cancellation is persisted and observed by the durable worker heartbeat/cancellation loop.
- Workspace historical versions are immutable metadata records; historical bytes remain in private Storage.
- Workspace restore already exists as an OpenManus runtime tool that verifies source byte length and SHA-256, then writes restored bytes as a new lease-fenced CAS version and requires approval.
- No direct client-side database or Storage mutations were added.

## Verification boundary
Per product-owner instruction, no tests, lint, typecheck, build, live API execution, browser checks, migration application, staging or deployment were performed. The UI change has not received before/after screenshot regression review. This report records source changes only; it does not claim runtime or security acceptance.

## Remaining work / phase status
Phase 04 remains in progress. Outstanding items include complete file lifecycle UX and mutation contract, upstream server/session parity, Flow Engine parity and end-to-end browser supervisor enforcement/approval wiring. The browser supervisor and egress proxy exist in source but require deployment topology/egress acceptance before activation.

After Phase 04, continue in dependency order:
1. Phase 07 — approval continuation, retry/timeout/cancellation races, lease recovery and outbox/event replay.
2. Phase 08 — full upstream agents/tools/provider fallback/orchestration/memory/RAG and accounting.
3. Phase 06 — FastAPI/OpenAPI contract and authorization completion.
4. Phase 09 — remaining Customer screens connected to real APIs.

Phase 10/11 remain blocked until verification and release work are authorized.
