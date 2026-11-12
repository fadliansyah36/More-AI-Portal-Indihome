# Customer OpenManus Streaming Integration Increment — 2026-11-12

## Objective
Correct the existing Customer Chat stream consumer so it follows the actual FastAPI durable event contract emitted by the OpenManus worker.

## Evidence from implementation contract
- Worker publishes durable checkpoint progress using event type `run.progress` through `WorkerRpcClient.append_run_event`.
- FastAPI `GET /api/v1/agent-runs/{run_id}/stream` forwards the persisted `agent_run_events.event_type` as the SSE event name and attaches an owner-safe checkpoint projection as `data.checkpoint`.
- The previous Customer Chat consumer listened for `worker.checkpoint`, which is not the current durable worker event type. Therefore it could not consume progress checkpoint snapshots from the current backend contract.

## Change implemented
- Updated `components/views/chat-view.tsx` to consume `run.progress`.
- Kept `worker.checkpoint` as a backward-compatible event alias.
- Treated checkpoint text as a persisted snapshot and replaced the displayed snapshot rather than appending it, preventing duplicate text if Last-Event-ID replay redelivers a progress event.
- Kept terminal handling for `run.completed`, `run.failed`, and `run.cancelled`.
- Preserved the existing Customer Chat layout, styles, controls and navigation.

## Git
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main`
- Commit: `a116c858e7ecd7f79068b184c4b8d23853417cc1`
- File: `components/views/chat-view.tsx`

## Verification and deployment
- No real tests, staging or deployment were performed, per product-owner instruction.
- This is a source-level contract alignment, not runtime verification.
- Existing chat final output still comes from the terminal durable run event (or authenticated run status retrieval after stream timeout); the worker currently persists final assistant text in its final checkpoint/output rather than emitting token-by-token deltas.
- No claim of full streaming-token support is made.

## Overall integration status
This increment improves one critical edge in Customer Frontend → FastAPI → durable worker → persisted event stream → Customer Frontend. It does not complete Phases 04, 07, 08, 06, or 09, and does not prove the full production path.

## Next implementation
Continue Phase 04 with the remaining OpenManus backend parity and workspace/session/Flow/security work, then Phase 07 durable lifecycle, Phase 08 LLM/tools/orchestration/memory/RAG, Phase 06 API contracts/authorization, and Phase 09 full Customer screen integration. Provider, entitlement, worker health and sandbox controls remain fail-closed until verified.
