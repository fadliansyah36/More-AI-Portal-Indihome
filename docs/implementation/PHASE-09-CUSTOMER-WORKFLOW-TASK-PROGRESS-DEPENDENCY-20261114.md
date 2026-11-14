# Phase 09 — Customer Workflow & Task Lifecycle Projection

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`

## Owner constraints

- Implement directly on `main`.
- No staging or deployment.
- No tests, lint, typecheck, build, browser checks, API/worker runtime verification or provider calls.

These constraints were observed.

## Source findings

### Active planning runtime

The worker registry registers `PlanningAgentRuntime` from `engine/agents/planning_runtime.py`, not the separate `engine/orchestration/planning.py` adapter.

The registered runtime already:
- persists the plan manifest and step input/output to Supabase;
- validates unique dependency indexes and requires dependencies to refer to earlier steps;
- validates that every step's selected execution Agent is registered;
- restores plan state from checkpoints and durable step rows;
- skips steps already persisted as succeeded during worker recovery;
- checks prerequisite completion before executing a dependent step;
- routes high/critical risk and tool-dependent steps through the durable approval gate;
- records approval-required, started, completed and failed events.

This increment did not replace that engine or change its execution semantics.

### Customer projection gap

Both Customer and shared Agent Run step endpoints previously returned only lifecycle status and timestamps, so the Customer Dashboard could not show the plan's dependency graph. The existing progress endpoint was also not exposed through the typed frontend client or rendered in Task/Workflow detail.

## Implemented

### 1. Safe dependency projection

Updated:
- `apps/api/app/routers/customer.py`
- `apps/api/app/routers/agent_runs.py`

Both step endpoints now:
- read private step input server-side;
- validate dependency indexes as non-boolean integers;
- keep only indexes earlier than the current step;
- deduplicate and sort dependencies;
- return only the safe `dependencies: number[]` projection.

The endpoints still exclude step objectives, prompts, tool arguments, provider observations, outputs and errors.

### 2. Typed progress API

Updated `lib/api/client.ts`:
- added `CustomerAgentRunProgress`;
- added `customerApi.getRunProgress(runId)` for the existing owner-scoped `GET /api/v1/agent-runs/{run_id}/progress` route.

### 3. Existing Customer UI integration

Updated:
- `components/views/tasks-view.tsx`
- `components/views/workflow-progress-view.tsx`

Task detail and Workflow detail now:
- fetch the durable progress snapshot;
- refresh it together with the run, steps and safe activity after SSE events;
- show percentage, completed/total steps and the current persisted step;
- display dependency prerequisite step numbers in the existing step list.

No new navigation surface or replacement UI system was introduced. Existing layout, typography and red primary-action tokens were retained.

### 4. Retry semantics clarification

Updated the Customer retry endpoint documentation:
- manual retry creates a new durable Agent Run after verifying the source run is failed/timed-out/expired and has no side-effecting tool activity;
- it preserves attachment references and the immutable saved Agent configuration snapshot;
- it is not an in-place checkpoint rewind;
- automatic worker retries and approval continuation remain the mechanisms that resume the original run/checkpoints.

No same-run manual rewind was added because re-executing a partially completed side-effecting tool without a verified tool-specific recovery receipt could duplicate external effects.

## Customer action audit reconciliation

The Customer action inventory and acceptance matrix were updated.

These remain intentionally fail-closed until real provider contracts/credentials exist:
- payment checkout, webhook settlement, refund and credit top-up;
- authoritative EduTech catalog, enrollment, lesson delivery and protected video;
- captive consent, OTP send/verify and gateway session activation;
- partner gateway device controls;
- Support ticket creation and lifecycle.

The UI must not report any of those as successful based on local state or an informational toast.

## Media provider status

OpenAI Image API generation remains a viable provider integration, but no server-side API credential or media-specific entitlement/credit reservation/metering configuration was supplied in this implementation context. It must not be activated as an unmetered tool.

OpenAI's Sora Videos API and Sora 2 models were removed on 2026-09-24 with no one-to-one replacement. Therefore an OpenAI Sora video adapter cannot be built as a live integration. A current supported video provider must be selected and configured with server-side credentials.

Official references:
- [OpenAI Image Generation API](https://developers.openai.com/api/docs/guides/image-generation)
- [OpenAI API deprecations](https://developers.openai.com/api/docs/deprecations)

## Documentation

- [Customer Dashboard Integration Acceptance Matrix](./PHASE-09-CUSTOMER-DASHBOARD-ACCEPTANCE-MATRIX-20261114.md)
- [Customer Action ↔ FastAPI Contract Inventory](./PHASE-09-CUSTOMER-ACTION-API-INVENTORY-20261113.md)
- [Phase Tracker](./PHASE-TRACKER.md)

## Verification boundary

- No tests, lint, typecheck, build, browser checks, API/worker runtime checks, provider calls, staging or deployment were run.
- This report records source integration only. It does not claim runtime acceptance.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED**.
