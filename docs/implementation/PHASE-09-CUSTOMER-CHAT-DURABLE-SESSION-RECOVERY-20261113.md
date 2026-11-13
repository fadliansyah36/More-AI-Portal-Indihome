# Phase 09 — Customer Chat Durable Session Recovery

Date: 2026-11-13  
Branch: `main`  
Baseline commit: `d9716ff444dd7bc33301d68d8c83b0af5437bf48`  
Implementation commit: `f1c0068f34c64f8de15ed4b6666852c89d536f7c`

## Scope

Close the identified ChatView recovery gap without changing the established MoreAI × IndiHome visual system or bypassing FastAPI.

## Implemented

- On restoration of the latest active conversation, load its durable session page through the existing typed Customer API client.
- Select the latest resumable session across queued, pending, running, approval-waiting and cancellation-requested states.
- Retrieve session detail, persisted session events and current Agent Run state through owner-scoped FastAPI routes.
- Derive the replay cursor from the persisted event page and restore the latest checkpoint text snapshot before reconnecting.
- Reconnect the existing authenticated SSE stream with the durable sequence cursor. The shared stream client supplies `Last-Event-ID`, refreshes the Supabase Auth token on reconnect, and resumes from the last delivered event.
- Reconcile succeeded, failed, cancelled, timed-out and expired terminal states into the restored assistant message.
- Preserve message identity where a persisted assistant message references the run; otherwise use a stable run-derived local key for the in-progress assistant message.

## Files changed

- `components/views/chat-view.tsx`

No API endpoint, Supabase schema, migration, RLS policy, provider configuration, deployment or staging changes were made. Existing typed API contracts in `lib/api/client.ts` and existing FastAPI session/SSE routes were reused.

## UI preservation

The change is confined to the ChatView conversation restoration lifecycle. Existing component structure, copy, typography, spacing, colors, controls and responsive styling were not intentionally changed. Product owner explicitly authorized proceeding without the AGENTS.md before/after screenshot gate for this integration work.

## Verification boundary

No tests, lint, typecheck, build, browser checks, API probes, worker execution, staging or deployment were run, per product-owner instruction. This is a source implementation report, not runtime acceptance evidence. The reconnect behavior, session/event response compatibility and concurrent session race handling remain unverified at runtime.

## Remaining Phase 09 scope

1. Verify and complete Agent Studio selection/planning/tool activity and run result presentation against actual durable run/step/event contracts.
2. Reconcile Workflow and Tasks actions, approvals, retry and cancellation with durable run lifecycle.
3. Complete Files, Knowledge, ingestion and RAG workflow UI/API authorization reconciliation.
4. Complete Customer Dashboard action/response authorization inventory and acceptance documentation.

## Next phase

Continue Phase 09 — Customer Dashboard Integration Completion, next focusing on Agent Runtime and Workflow/Tasks integration. Phase 10 runtime/end-to-end verification and Phase 11 release gate remain unperformed and must not be marked complete.


## Incremental continuation — Workflow run controls and step visibility

Commit: `22f9c00d6d5bfc2a68d42eb246cc7a5b7b174928`

Updated `components/views/workflow-progress-view.tsx`:
- Added on-demand retrieval of durable workflow steps through the existing owner-scoped Customer API method.
- Exposed step sequence, key, status, start and finish timestamps in an expandable run detail section.
- Added cancellation action for non-terminal runs and reconciled the returned cancellation status in the local run list.
- Reused the existing API client contracts; no new route, schema, or direct browser-to-Supabase access was introduced.

No tests/build/lint/typecheck/browser/API/worker execution, staging or deployment were run. The added actions are source-level integrations only and require later authorized runtime acceptance.


## Incremental continuation — Runtime key contract alignment

Commits:
- `13733be8ca95747a99077b2c8bd2411e0119c42b` — app-level selected runtime key propagation
- `491217a0dfe581ea69111d4f4852ad6365c31b48` — ChatView transport type
- `fe5b9d3584fa4293000e7d30db77ff4693cac069` — Agent Studio catalog/runtime alignment

Source inspection confirmed the FastAPI `MessageCreate.agent_key` contract is currently constrained to `manus | planning | toolcall`. The Agent Studio now only offers enabled catalog entries whose keys are accepted by that transport contract, and the parent navigation preserves all three supported keys rather than coercing every non-planning agent to `manus`. ChatView's selected key type now matches the backend contract.

This is a compatibility alignment, not proof that every upstream OpenManus agent type has been exposed through the customer message API. Any additional catalog/runtime key requires a coordinated FastAPI request schema, enqueue/RPC and worker dispatch update before the frontend may advertise it as runnable.

## Remaining Phase 09 acceptance gaps (source inspection only)

- Agent Runtime: inspect and reconcile planner/tool event payload contracts against the customer-safe event stream; ensure planning decisions, tool progress, approvals, checkpoints and final output render from persisted events, not inferred client state.
- Tasks: task list is currently a projection of Agent Runs; there is no independently evidenced customer task CRUD/retry contract in the inspected surface. Keep it truthful as run-backed work until a durable task API is confirmed. Do not implement retry against an unverified route.
- Workflow: durable step listing and cancellation are wired; retry remains unavailable in the inspected customer run routes. Tool approval decisions exist, but event-to-run refresh and lifecycle parity still need source reconciliation.
- Files: workspace file and artifact surfaces already use authenticated API clients; finish checking upload/download authorization, run linkage, lifecycle and error contracts across every customer path.
- Knowledge/RAG: ingestion list/upload/retry/archive is present. Confirm document detail/chunk retrieval and ingestion lifecycle exposure, workspace scoping, and how retrieval citations/evidence are represented in Chat UI before claiming RAG is fully integrated.
- Authorization: reconcile all customer routes, shared `/api/v1/agent-runs` endpoints, workspace membership checks, artifact ownership and knowledge workspace access. Do not assume a route is customer-safe solely because a frontend API method exists.

No test, lint, typecheck, build, browser, API, worker, staging or deployment activity was performed, per owner instruction. The evidence here is repository source and API contract inspection only.


## Incremental continuation — Safe activity timeline and Knowledge chunk visibility

Commits:
- `261a7aee47b6f8be5d4ef5295bbce3c6a5200e31` — typed customer run activity contract
- `6ba5b9f130bf2952ce695597936af55ccb6d17a9` — Workflow activity timeline
- `b3aff663b8e4c3e9ba2e2c618919fd8ad0e46bf8` — Knowledge chunk detail panel
- `0fe7059ba955f2aa7b3684fd22df2affda349532` — zero-valued chunk cursor guard

Workflow now requests the owner-scoped `/api/v1/agent-runs/{run_id}/logs` safe activity projection, not the raw event payload endpoint. It renders sequence, event label, tool name, timestamp, level and progress where provided. This avoids exposing raw tool arguments/observations through the UI.

Knowledge Library now exposes document ingestion detail and paginated chunk metadata through the existing `knowledgeApi.get/chunksPage` contract. It shows chunk index and token count only; it does not expose private chunk content or embeddings.

No test, lint, typecheck, build, browser, API, worker, staging or deployment activity was performed. Source changes remain unverified at runtime.
