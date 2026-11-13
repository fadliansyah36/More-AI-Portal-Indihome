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

## Phase 09 continuation — Tasks durable run inspection (2026-11-14)

### Implemented
- Connected each existing Tasks list item to its persisted Agent Run detail instead of leaving the checklist row inert.
- Detail view loads the owner-scoped run record, durable workflow steps, and the safe `/api/v1/agent-runs/{run_id}/logs` activity projection through the existing typed API client.
- Displays backend status/attempts, durable step status, event sequence, safe tool/phase/progress metadata, checkpoint key, and textual output only when the backend output contract supplies `output.text`.
- Cancellation uses the existing customer run cancellation endpoint and refreshes the durable run record; task status is reconciled from the refreshed backend state.
- Retry remains intentionally unavailable in the UI: source inspection did not establish a supported customer retry endpoint or worker retry contract that can be safely invoked from this screen. The UI explicitly explains this rather than inventing a route or simulating retry.
- Existing Tasks layout and visual system were retained; the change adds an in-place detail modal to the existing page.

### Contract and security notes
- Run detail is fetched through owner-scoped customer API; steps expose lifecycle metadata only.
- Activity uses the safe projection endpoint, not raw event payloads or private tool arguments/observations.
- Cancellation remains backend-authoritative; the UI does not mark a run cancelled until the API returns and the current run is refreshed.
- No Supabase schema, migration, RLS, storage policy, or production data was changed.

### Verification boundary
- Source inspection only. Per product-owner instruction, no build, lint, typecheck, automated tests, browser verification, live API/worker execution, staging, or deployment was performed.
- Tasks lifecycle UI is connected to existing durable run APIs; independent task CRUD and supported retry remain gaps until backend contracts exist and are documented.

### Next work (Phase 09 remains open)
1. Complete Files/artifacts lifecycle and authorization audit: workspace membership scope, immutable version history, soft-delete/restore, artifact ownership, run linkage, signed download scope and retention.
2. Connect safe RAG retrieval/citations to Chat UI only after confirming the actual persisted response and citation contract.
3. Audit every remaining Customer endpoint for principal/tenant authorization, response schema, pagination, and error consistency.
4. Complete lifecycle event coverage for planning, tool execution, approval decisions, checkpoints, and final outputs across Chat and Workflow screens.
5. Resolve durable retry contract from worker/outbox semantics before adding any retry action; do not replay a completed or ambiguous mutation from the client.
6. Update final Phase 09 acceptance matrix and unresolved-gap register. Phase 10/11 release verification remains blocked by the explicit no-test/no-staging instruction.

## Phase 09 continuation — Chat lifecycle activity, Files audit, and acceptance matrix (2026-11-14)

### Chat lifecycle activity
Commit: `05c5c9ae11d2df01628186e7d7f64ef56187981e`

- Chat now retains an in-memory per-message lifecycle activity list from the existing durable SSE stream and exposes it in a collapsed activity disclosure.
- The projection allowlists sequence, event name, timestamp, tool, phase, status, progress and checkpoint key. It deliberately does not render raw event payloads, tool arguments, provider observations, or checkpoint state.
- Checkpoint text remains a replaceable snapshot; replay does not append duplicate text.
- Approval-waiting lifecycle states are reflected in the assistant source label where the corresponding event is received.
- This UI is a safe presentation layer over the current stream. It is not evidence that every planner/tool event is emitted by the worker: current worker runtime source explicitly emits run.started, run.progress, run.completed, run.failed, run.cancelled and run.timed_out. Fine-grained tool/planning lifecycle event production and approval resume event parity remain gaps to be completed at the backend/worker boundary.
- The workflow screen separately consumes durable safe activity logs and owner-scoped tool approval records. Approval decisions use the durable decision RPC and reload the canonical approval row.

### Files and artifact lifecycle source audit
Inspected current customer UI and FastAPI routes:
- Workspace file UI already supports upload, paginated listing, immutable version history, signed download by current or historical version, soft-delete, and restore.
- FastAPI workspace routes call workspace membership/permission checks before file reads and lifecycle mutations. Delete/restore use expected-version guards; restore validates the previous object path and writes a new immutable version rather than overwriting history.
- Workspace signed download checks workspace access, deleted-state/version selection and storage path ownership before requesting a short-lived signed URL.
- Private artifact API lists only rows filtered by authenticated user, resolves chat attachment run linkage from the owner-scoped message-attachment junction, validates private bucket configuration, validates owner-prefixed storage paths and issues 60-second signed URLs only after `owned_record`.
- Artifact upload validates filename, size, MIME/signature for supported chat attachments, checks conversation ownership and explicit run ownership when supplied, stores a SHA-256 checksum, and compensates object upload if metadata persistence fails.
- Tasks/Workflow/Files surfaces use the artifact API for private run-linked artifact downloads. No browser direct-to-Supabase business-data access was introduced.
- Scope limitation: this is source inspection, not an exhaustive independent review of every workspace membership role, every Storage policy, or live signed URL behavior. No Storage/RLS policy was changed.

### RAG and citation contract findings
- Worker knowledge retrieval is tenant/user scoped through `moreai_match_knowledge_chunks`, passing authenticated user id, optional workspace id, vector, bounded match count and optional validated document IDs.
- Worker retrieval currently returns a JSON tool result with chunk id, document id, title, content, similarity and metadata. That is an internal tool result, not yet a canonical structured citation contract attached to the persisted Agent Run output.
- Chat UI renders citation records only if the final run output supplies structured `citations` with id, document_id, title and marker; it also accepts optional page/character offsets and similarity. It does not fabricate citations from model prose.
- Therefore RAG retrieval exists, and conditional citation rendering exists, but structured evidence provenance from retrieved chunks through runtime output to persisted response is still an acceptance gap. A future backend contract must bind citation ids to retrieved chunk/document ids and sanitize metadata before it is persisted or returned.

### Durable retry findings
- Worker dispatcher classifies retryable upstream timeout, transport failures, and HTTP 429/5xx as retryable execution errors; attempt and max_attempts are passed into the runtime context.
- The durable worker/outbox has separate leased at-least-once event publication retry with event-id deduplication. This is not a customer Agent Run retry action.
- No customer-facing manual retry endpoint or safe replay contract was confirmed in the inspected customer routes. Do not expose a client retry button until a backend operation defines idempotency, terminal-state eligibility, fresh run identity/attempt semantics, billing/entitlement revalidation, workspace authorization, attachment/artifact linkage, and audit events.
- Automatic worker retry and outbox retry must remain distinct concepts in UI copy and acceptance evidence.

### Phase 09 acceptance matrix (source-level status)
| Capability | Source-level status | Remaining acceptance gap |
|---|---|---|
| Customer Chat enqueue | Connected to FastAPI durable enqueue and idempotency key | Runtime/provider execution not exercised |
| Chat session recovery | Implemented from persisted session/events and SSE cursor | Runtime replay/race behavior unverified |
| Chat progress/checkpoint | Safe activity disclosure and checkpoint text snapshot | Backend fine-grained event production incomplete |
| Planning/tool lifecycle | UI can display allowlisted event metadata | Worker does not yet emit a complete normalized planning/tool event taxonomy |
| Tool approval | Durable list/decision APIs and workflow UI exist | End-to-end pause/decision/resume lifecycle unverified; event parity gap |
| Workflow steps/cancellation | Owner-scoped step list and cancellation wired | Live worker cancellation semantics unverified |
| Tasks | Durable Agent Run detail, steps, activity, output and cancellation | No independent task CRUD or manual retry contract |
| Workspace Files | Upload/list/version history/signed download/soft-delete/restore UI and API routes exist | Exhaustive role/Storage policy review and runtime verification pending |
| Artifacts | Owner-scoped list/upload/signed download and run linkage | Retention/deletion/version semantics not evidenced as a complete artifact lifecycle |
| Knowledge ingestion | Upload/list/detail/chunk metadata/retry/archive routes and UI exist | Live ingestion and workspace-role verification not run |
| RAG retrieval | Tenant-scoped pgvector retrieval exists in worker tool | Structured citations are not yet guaranteed in persisted run output |
| Customer authorization | Inspected routes use customer principal and owner/workspace checks in key flows | Full endpoint-by-endpoint authorization/response contract inventory still pending |
| Supabase schema/RLS | Existing migrations provide durable lifecycle and scoped data structures | No schema/RLS changes in this continuation |
| Release acceptance | Not performed | Explicitly blocked by no-test/no-staging instruction |

### Remaining gaps and next implementation order
1. Normalize and emit durable worker events for planning start/complete, tool start/complete/failure, approval required/decision/resume, checkpoint, cancellation requested, and terminal output. Keep public event payloads allowlisted and raw payloads private.
2. Define a structured RAG citation contract from retrieved chunk/document identity through agent result persistence and customer response; keep citation evidence bound to owner/workspace scope.
3. Finish endpoint-by-endpoint Customer authorization and response contract inventory, including shared Agent Run logs/events, workspace role permissions, artifact endpoints, knowledge endpoints, tool approvals, billing/usage and remaining customer routers.
4. Decide whether artifact deletion/versioning is a required product lifecycle; current artifact surface is immutable/private but no complete user-facing delete/retention contract was evidenced.
5. Define manual Agent Run retry only if the backend supports a safe new-run/idempotent retry operation; worker automatic retry and outbox retry are not manual retry.
6. Finalize Phase 09 acceptance matrix after source implementation. Runtime acceptance remains intentionally not performed.

### Verification boundary
Only repository source inspection and source edits were performed. No tests, lint, typecheck, build, browser verification, live API calls, worker execution, Supabase mutations, staging, or deployment were performed. Do not treat this report as runtime acceptance evidence.


## Phase 09 continuation — Durable agent/planning and approval-request lifecycle events (2026-11-14)

### Implemented on `main`
- Worker runtime now emits durable `agent.execution.started` and `agent.execution.completed` events around the registered agent dispatcher boundary.
- Runs dispatched with the `planning` agent key additionally emit `planning.started` and `planning.completed` phase events.
- Successful cancellation after dispatch emits `agent.execution.cancelled` before the existing terminal `run.cancelled` event.
- Worker tool-approval handling now persists `tool.approval_requested` before invoking the pause RPC, while the worker still owns the run lease. The event contains only the canonical tool key and SHA-256 hash of arguments; raw arguments and observations are not published.
- Event keys include run/attempt identity for agent phase events and a stable arguments hash for approval request deduplication.

### Source files changed
- `apps/worker/app/runtime.py`
- `apps/worker/app/client.py`

### Contract and limitations
- These are durable runtime-boundary and approval-request events. They do not claim that individual OpenManus planner decisions or each tool invocation now emit start/completed/failed events.
- Approval decision and resume events still need a transactionally durable API/database-side event path. The approval RPC atomically updates approval/run state and releases/requeues execution; appending from the old worker after that point would violate lease ownership, so no unsafe post-pause worker write was added.
- Tool start/completed/failed events still require instrumentation at the shared tool execution boundary, preserving tool policy checks and approval pause behavior.
- Manual customer retry remains unsupported until an idempotent new-run contract is implemented. Worker automatic retry and outbox publication retry remain separate.
- No frontend UI changes, Supabase migrations, production data changes, staging or deployment were made.

### Verification boundary
Per explicit instruction, no tests, lint, typecheck, build, browser verification, live API calls or worker execution were performed. This report records source edits only; runtime behavior is unverified.

### Next implementation order — Phase 09 remains open
1. Instrument the shared tool execution boundary to persist safe `tool.started`, `tool.completed`, and `tool.failed` events with stable per-call keys and no raw arguments/observations.
2. Add approval decision/resume events transactionally in the database RPC or an equivalent lease-safe durable event path.
3. Carry structured RAG citations from retrieved chunk/document IDs through final Agent Run output persistence and the customer response schema.
4. Finish endpoint-by-endpoint customer authorization/response contract inventory and reconcile remaining UI actions against supported backend contracts.
5. Update the acceptance matrix after source implementation; Phase 10/11 verification remains intentionally not performed under the current instruction.


### Lifecycle terminal-state completion
A follow-up worker change adds `agent.execution.timed_out` when the worker run deadline expires, `agent.execution.cancelled` when cancellation wins the dispatch race, and `agent.execution.failed` for classified and unexpected execution failures. These are attempt-scoped idempotent event keys and contain only the agent key, safe error code/classification and retryable flag. Lease-loss paths deliberately emit no terminal event because a stale worker no longer owns the run. Planning events are emitted only for the `planning` runtime key; other agent keys are not mislabeled as planning.

Additional source commit: `52c38e1fac033d5521b4d54969aa9b9b48c82812`.


## Phase 09 continuation — Planning steps, tool outcomes, approval decisions, and API activity projection (2026-11-14)

### Implemented on `main`
- `PlanningAgentRuntime` now publishes durable step events: `planning.step.approval_required`, `planning.step.approval_resumed`, `planning.step.started`, `planning.step.completed`, and `planning.step.failed`. Payloads contain bounded step index, executor agent key, risk/status and exception class only; objective text, prompts, tool arguments and model observations are excluded.
- `apps/worker/app/registry_factory.py` wires the existing durable `WorkerRpcClient.append_run_event` publisher into the Planning runtime.
- Durable OpenManus tool execution now distinguishes `tool.completed`, `tool.failed`, and `tool.timed_out` instead of reporting every settled tool outcome as `tool.completed`. Existing `tool.started` and `tool.cancelled` remain.
- Approval lifecycle now persists `tool.approval_requested` before the pause RPC releases the worker lease. When the durable run resumes and the worker observes the canonical approval status, it publishes `tool.approval_granted`, `tool.approval_denied`, `tool.approval_expired`, or `tool.approval_consumed` before continuing/settling the approval.
- FastAPI safe run-activity projection now allowlists agent key, planning step index/risk and safe error code/type fields, and maps the expanded agent/planning/tool/approval event taxonomy to customer-safe activity labels. The `/thinking` projection includes the new event types. Raw event payloads remain private.

### Source files changed
- `engine/agents/planning_runtime.py`
- `apps/worker/app/registry_factory.py`
- `engine/agents/durable_tool_runtime.py`
- `apps/worker/app/client.py`
- `apps/api/app/routers/agent_runs.py`

### Commit sequence
- `0c299f540889fe4b5b1ca03f0f5f14cba7d05454` — planning step lifecycle publisher
- `a194ea73cf4632bfc9ad5c002c23c7597d039c0b` — worker planning publisher wiring
- `9ee8365c73b345116c458d06ec5e6a6aa33e2d69` — distinct tool failure/timeout event types
- `0956647345f7692a93e79e5f7c3412e9020da246` — approval decision/resume event publication
- `ee33e5509be4abe5355872efef208be24e0e7988` — safe FastAPI activity projection

### Remaining gaps
- Customer-facing activity consumers must be reconciled with the expanded event contract and any event types not currently rendered should receive a clear, non-sensitive label. Chat's SSE path receives raw event types but uses a safe metadata allowlist; Workflow/Tasks use the safe logs projection.
- Approval decision events are published by the resumed worker after it observes the committed approval status, not atomically inside the decision RPC. A crash between decision commit and worker resume can delay the activity event; durable approval state remains canonical. A future transactional DB-side event write would close this observability gap.
- Manual customer retry is still intentionally not implemented; there is no verified safe replay/new-run contract.
- Structured RAG citations are assembled by the runtime from retrieved chunk/document IDs and persisted in the final output where present; remaining work is to verify the customer API output contract and source markers against all retrieval/tool response variants, without fabricating citations.
- Full endpoint-by-endpoint customer authorization and response contract inventory remains open.

### Verification boundary
No tests, lint, typecheck, build, browser verification, live API calls, worker execution, Supabase schema/data mutation, staging or deployment were performed, as explicitly instructed. Changes are source-level implementation only and are not runtime-verified.

### Phase status and next phase
Phase 09 remains **in progress**. Continue Phase 09 until the remaining API/UI contract and authorization inventory, citation provenance review, and approval event durability gaps are resolved. After Phase 09 is complete, the dependency-ordered next phase is Phase 10 — End-to-End Integration Verification; Phase 11 — Integration Release Gate follows Phase 10. Neither phase is being marked complete or executed under the current no-test/no-staging instruction.


## Phase 09 continuation — Customer event consumers and citation provenance (2026-11-14)

### Source changes committed to `main`
- `c562378b0d5d9e53e4e1f54c086e37f4ef33b1c2` — ChatView now labels the durable agent execution, planning-step, tool outcome, and approval lifecycle event taxonomy. Safe metadata fields (agent key, step index, risk and error code) are retained in the activity model; raw event payloads remain excluded.
- `e52a36cd1ec402373d58767c99e87c5332d05366` — FastAPI thinking projection and authenticated WebSocket replay now include the expanded lifecycle event family and safe metadata fields. This closes the earlier mismatch where REST `/thinking` included expanded events but WebSocket initial/replay projections omitted them.
- `329a6eeaf490f1de73a9ef56447054f3317ff7a0` — RAG final-output citation assembly now includes only retrieved chunk IDs explicitly referenced by the final response marker `[source:<chunk_id>]`. Persisted citation objects contain the stable chunk/document IDs, title, marker, bounded similarity and validated page/character offsets; arbitrary retrieval metadata is no longer copied into the public citation object.
- `1a55db2bfca2ea745768638df6b68dcd00c57239` — corrected the source-marker parser so bracketed citation markers are matched as intended.

### Updated source-level acceptance matrix

| Area | Source-level state | Runtime acceptance |
|---|---|---|
| Chat durable conversation/session recovery | Implemented against owner-scoped API, checkpoint restore and resumable SSE cursor | Not run |
| Chat agent/planning/tool/approval activity | Expanded event labels and safe metadata consumer implemented | Not run |
| Workflow activity and durable steps | Safe logs projection, step listing, approval history and cancellation wired | Not run |
| Tasks run detail | Owner-scoped run/step/log detail and cancellation wired; no unsupported manual retry | Not run |
| Approval decision transaction | Decision and pause/resume state are committed by existing RPC; event publication is still worker-observed after resume, not in the same DB transaction | Open |
| RAG citations | Final citations are filtered by exact final-response source markers and carry chunk/document provenance | Not run; all retrieval response variants and API/UI path still need runtime acceptance |
| Customer API authorization/response contracts | Existing inventory covers many Customer routes; endpoint-by-endpoint review across all shared and Customer routers remains open | Not run |
| Supabase data/RLS/schema | No schema/data/RLS changes in this increment | Not run |

### Approval transaction boundary — explicit remaining blocker
The current `moreai_decide_tool_approval` RPC atomically updates the approval row, approval-pause row, run status/resume flag and checkpoint state. The durable event stream is not yet updated in that same transaction. Worker publication after it reclaims the resumed run is lease-safe but can be delayed by a crash before the worker observes the committed decision. Closing this gap requires a forward-only Supabase migration that adds the approval decision/resume event rows inside the existing RPC transaction while preserving the current pause/resume and worker lease invariants. No applied migration was edited and no live Supabase schema was changed in this increment.

### Verification and release boundary
No tests, lint, typecheck, build, browser checks, API probes, worker execution, Supabase schema/data mutation, staging or deployment were run. All entries above are source inspection/implementation only. Existing UI files changed only to surface backend lifecycle events in the current Chat activity area; no layout, color, typography, spacing or navigation redesign was made. Screenshot regression evidence is intentionally absent under the no-browser-verification instruction.

### Next implementation order
1. Add the forward-only database migration for transactionally appending approval decision/resume events in `moreai_decide_tool_approval`; keep service-role-only execution and owner/run consistency checks.
2. Finish endpoint-by-endpoint authorization and response-schema audit for Customer, shared Agent Run, workspace, artifacts, Knowledge, approvals, billing/usage and notifications.
3. Reconcile all retrieval/tool response variants to the structured citation provenance contract and ensure Chat history restoration receives the same citation envelope.
4. Complete the UI-to-API action inventory and source-level acceptance matrix, marking unavailable provider-backed actions as unavailable rather than simulated.
5. Phase 09 remains open until the above source work is complete. Phase 10 — End-to-End Integration Verification is next only after Phase 09, and is not authorized/performed under the current no-test instruction; Phase 11 follows Phase 10.


## Phase 09 continuation — atomic approval events, Customer authorization and RAG history (2026-11-14)

### Approval decision/resume transaction
- Added forward-only migration source `supabase/migrations/20261114090000_moreai_atomic_approval_decision_events.sql`.
- The replacement `moreai_decide_tool_approval` RPC now appends `tool.approval_granted`, `tool.approval_denied`, or `tool.approval_expired` to `agent_run_events` and the canonical `outbox_events` in the same database transaction as approval/pause/run/checkpoint updates.
- When the run transitions from `waiting_approval` to `queued`, the same transaction also appends `run.resume_queued`. The helper serializes per-run sequence allocation, uses stable event keys, checks idempotency conflicts, and writes the same outbox envelope used by the worker event publisher.
- The worker no longer republishes decision/grant/deny/expire events after resuming. It only publishes `tool.approval_consumed` after the single-use consume RPC succeeds. Consumption is still worker-observed, not transactionally emitted by the consume RPC.
- FastAPI REST thinking, initial/replay WebSocket projections, and Chat activity labels now include `run.resume_queued`.
- **Migration is committed but NOT applied to Supabase.** No live schema mutation was performed. Until the migration is applied through an authorized database-change workflow, production still uses the previously deployed RPC and atomic event behavior is not active there.

### Customer API authorization and response-contract source audit
A source-level route inventory was performed across the Customer/shared Customer API routers:
- 77 route handlers were found across `agent_runs.py`, `artifacts.py`, `catalog.py`, `conversations.py`, `customer.py`, `knowledge.py`, `learning.py`, `notifications.py`, `tool_approvals.py`, and `workspaces.py`.
- All 77 declared route signatures require `customer_principal`; the two Customer WebSocket paths authenticate the bearer token and explicitly resolve `require_customer_context` before accessing run/conversation data.
- The Customer principal rejects active Partner memberships and privileged Platform roles, so those identities must use their own API namespaces.
- Owner-scoped access is enforced through authenticated user filters/owned-record checks for conversations, runs, approvals, artifacts, knowledge documents, notifications, learning progress, wallet/usage and customer network sessions. Workspace access additionally resolves owner/member membership and permission keys.
- Every JSON Customer route has an explicit response model except the two SSE streaming transports. The binary speed-test download route is intentionally transport-specific. WebSockets also use their message envelope rather than JSON response models.
- This is a source review, not a live cross-tenant/RLS proof. The canonical service-role repository bypasses browser RLS by design, so backend owner checks remain security-critical; live RLS and cross-tenant denial evidence is still outstanding.

### Event payload and SSE privacy correction
- Conversation session event replay now preserves only the safe allowlist, including agent key, step index, risk and error code.
- Customer Agent Run SSE now projects event payloads through the same safe activity allowlist used by FastAPI logs/thinking. Private tool arguments, observations, raw checkpoint bodies and worker internals are not serialized to the browser.
- Terminal SSE output is restricted to final user-visible text and validated structured citations; error output is reduced to a bounded error code.
- These are source-level changes only; no browser/API verification was run.

### RAG retrieval → final response → conversation history
- The Knowledge Search tool now returns an explicit `citation_marker` for each valid chunk UUID, and the runtime prompt requires the model to use that exact marker adjacent to claims grounded in retrieval.
- The final-output assembler accepts only marker IDs actually present in the final model response, matches them to the retrieved chunk records, and persists the exact chunk ID, document ID, title, similarity and validated page/character offsets.
- Machine markers are removed from user-visible prose after citation extraction; the structured citations remain in Agent Run output.
- Customer conversation detail and paged message endpoints now join assistant messages to owner-scoped Agent Run output by `run_id`, validate citation identity/marker/metadata, and return a typed `citations` array. Chat restore and older-message pagination restore the citations; resumed Chat stream completion also restores final citations.
- This preserves provenance through the persisted run output and conversation message's run link; it does not duplicate citation JSON into the conversation_messages row.

### UI changes and preservation
- UI files changed: `components/views/chat-view.tsx` and `lib/api/client.ts`. These changes only add lifecycle labels, typed citation metadata, and restoration of citations for historical/resumed Chat messages.
- No page/layout/navigation, color, typography, spacing, component hierarchy or existing interaction redesign was made. Screenshot comparison was not performed because browser verification is explicitly prohibited in this execution.

### Source commits in this increment
- `dd67833335b925ea3fbc4754fff4f5cf44b37f12` — atomic approval decision/resume migration source.
- `7f24463448c1403f3011774ca9b63e8d68105342` — FastAPI run resume event projection.
- `c68cb1e5eb94da27b33f51441610c5155de26658` — Chat resume activity label.
- `b4c61f1f9c607532e40075f50a5ba594bb9e9e1e` — safe metadata in conversation session replay.
- `da032140feff29cec644d86bc2d9051a58e13290` — safe Customer SSE activity projection.
- `2a85c4d441731618d07baed7065f2250b65e9515`, `fe451a2ecc49c5a39c2d7b1702cf292152e0df1a`, `65b61cd6cd0d8f1bb8640a490657b9b534f56784` — owner-scoped conversation citation history and safe terminal output.
- `d3d0011ff97743b6cceebfa74191936bf774969f`, `c7cc9a1ef0a4fd15f0f010bdf2e7349f7435c977`, `174f8c120220faa5ff375fc78b733d992f72d948` — typed and restored citations in Chat.
- `49457b1d7cfeb99c73c4bb2f0877fbffce22505a`, `f386c89628d5195bd566e8cebe84b6efc17f4868`, `eb4c829707dbe754a147909d42f2344b80f15c14`, `e129c47a481aa0a13c80de7c8085b495e73d3a91` — exact retrieval markers, prompt contract and marker-free user-visible final text.
- `f242bc10e49145d4b9bcc5e54066af8aabaeaf48` — avoid duplicate worker approval decision events.

### Updated source-level acceptance matrix

| Area | Source-level state | Runtime acceptance |
|---|---|---|
| Approval decision event | Migration source atomically appends decision event with approval state | Not applied; not run |
| Approval resume event | Migration source appends `run.resume_queued` in same transaction as run queue/checkpoint state | Not applied; not run |
| Approval consumption event | Worker emits after successful one-time consume; not atomic with consume RPC | Not run |
| Customer route authentication | 77/77 route signatures use customer principal; WebSockets explicitly resolve Customer context | Not run |
| Customer response contracts | JSON routes typed; SSE and binary transports intentionally custom | Not run |
| Customer SSE privacy | Safe event projection and bounded terminal output implemented in source | Not run |
| RAG retrieval marker | Tool returns exact marker and prompt requires exact marker | Not run |
| RAG final output provenance | Final response markers resolve to exact retrieved chunk/document metadata | Not run |
| Chat history citations | Owner-scoped Agent Run output joined to assistant message by run_id; citations restored in initial and paged history | Not run |
| Workflow/Tasks lifecycle | Safe run activity projection contains new event family; Workflow/Tasks use run activity contracts | Not run |

### Remaining Phase 09 blockers
1. The new Supabase migration must be reviewed/applied through an authorized migration process before atomic approval events are active in the canonical database. This execution deliberately did not mutate Supabase.
2. The Customer API review is source-level only. Live owner/member/partner/platform and cross-tenant denial proof remains outstanding.
3. Citation behavior still needs provider/worker execution acceptance across manus, planning, toolcall and checkpoint recovery variants. No real tests or provider runs were performed.
4. Complete the remaining screen/action inventory against the latest PRD and ensure every visible action is either connected to a real endpoint or explicitly unavailable; no simulated provider features.
5. Finalize acceptance matrix and implementation report after the remaining source gaps are closed.

### Verification boundary
No tests, lint, typecheck, build, browser checks, API probes, worker execution, migration application, Supabase schema/data changes, staging or deployment were performed. Phase 09 remains **IN PROGRESS**, not complete. Phase 10 is dependency-next only after Phase 09 source completion and when runtime verification is separately authorized; Phase 11 follows Phase 10.
