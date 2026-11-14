# Phase 09 — Customer Task Lifecycle Streaming Increment

Date: 2026-11-14  
Branch: `main`  
Baseline HEAD: `74025edfd7f880d3e99cdcd102005bb8a9fe1965`

## READ / INSPECT

Re-read the controlling `AGENTS.md`, the Customer Dashboard acceptance matrix, current typed API client, Chat, Agent Studio, Tasks, Workflow Progress, Agent Run router and Worker runtime. The existing product already connects Chat message enqueue to durable Agent Runs and authenticated SSE; Agent Studio filters catalog entries to supported runtime keys; Tasks reads owner-scoped Agent Runs, steps, activity and artifacts; Workflow Progress reads runs, approvals and artifacts.

## Implemented

- Updated `components/views/tasks-view.tsx` to subscribe to the authenticated, replayable Customer Agent Run SSE stream when a non-terminal run detail is open.
- Lifecycle events (run start/progress, worker checkpoint, planning step, tool lifecycle, approval request/resume, and terminal events) trigger authoritative refresh of run snapshot, persisted steps and safe activity projections from FastAPI.
- Run status changes are reflected in task history without fabricating local task completion.
- Stream cancellation is tied to the selected run detail lifecycle; terminal runs stop streaming. Shared API client retains bearer refresh, reconnect and durable event cursor semantics.
- Existing screen layout, route, navigation, copy, styling and design tokens were not changed. This is a narrow behavior integration in an existing screen.

## Existing end-to-end source contracts confirmed

- Chat: authenticated Customer API creates/loads conversation, uploads attachments through FastAPI, sends an idempotent message enqueue, then consumes durable SSE and restores conversation sessions.
- Agent: Agent Studio only presents enabled catalog entries whose keys are supported by the actual enqueue contract (manus, planning, toolcall).
- Workflow: planning is selected through the same Chat → durable Agent Run path; Workflow Progress reads run lifecycle, approvals, steps and artifacts. It does not create a local fake workflow.
- Tasks: owner-scoped run listing/detail/cancel, safe steps/activity, artifacts, signed downloads; newly added live event synchronization for opened run details.
- Backend: FastAPI validates Customer principal and owner-scopes run access; Worker persists lifecycle events and terminal state through the durable repository/outbox path.

## Remaining gaps (Phase 09 is NOT complete)

- Customer manual retry/regenerate remains unavailable; no endpoint is exposed without a safe idempotent checkpoint/replay contract.
- No distinct generation-specific backend contract/screen action was found in current view inventory. Generate actions must map to actual supported agent/tool capabilities, not invented provider endpoints.
- Customer Memory consent/review/correction/deletion is not complete.
- Connector OAuth lifecycle, payment/subscription checkout/settlement, full OTP/gateway activation and complete device/session revoke remain gated on domain contracts/provider readiness.
- Tool execution remains gated where isolation, credentials, approval or policy are not verified.
- Full source parity with upstream OpenManusWeb must continue to be tracked separately; this increment does not claim complete backend parity.

## Verification / deployment

Per owner instruction, no tests, lint, typecheck, build, browser/API/worker runtime, provider calls, staging or deployment were run. No screenshots were captured because browser verification was not authorized. This is a source-level implementation increment only.

## Commit

- Customer Task live lifecycle stream: `3361e689ca919461181b77dec3a370d894ca3139`

## Next work

Continue Phase 09: perform a route/action-level source reconciliation for all remaining Customer navigation and close only contracts supported by existing backend/domain policy. Prioritize the generation capability mapping and safe retry/regenerate design, then Memory privacy lifecycle. Continue provider secret-reference/category controls and build independent Admin and Partner Portal app roots within this monorepo. Configure their Vercel projects only after those roots are complete. Phase 10/11 remain not accepted/blocked under the no-verification instruction.
