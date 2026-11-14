# Phase 09 — Customer Dashboard Integration Continuation

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Source-only continuation commit: `75848ffb91de0f5264c30a1f6b81a66a5ecfdbe4`

## Objective

Continue reconciling the existing Customer Dashboard with FastAPI, the OpenManus-backed runtime/worker, and canonical Supabase while preserving the protected UI.

## Repository and architecture revalidated

- Main repository default branch is `main`.
- `AGENTS.md` requires OpenManusWeb to remain the authoritative backend source, FastAPI to remain the trusted business API, Supabase PostgreSQL to remain canonical persistence, and the existing Next.js Customer UI to remain the product frontend.
- Browser-side Supabase use is restricted to Auth. Business data, Storage, RPC, Realtime and provider operations must remain server-side behind FastAPI.
- Current acceptance matrix classifies Customer UI integrations as source-connected, partial/gated, or unavailable/fail-closed. Runtime acceptance remains NOT VERIFIED.

## Source correction implemented

File: `components/views/agent-studio-view.tsx`

The selected Agent detail previously rendered a static green `Enabled` badge even if the live worker capability snapshot showed that the runtime was offline. The badge now reflects `runtimeAvailable`:

- `Runtime aktif` when the backend reports an available runtime.
- `Worker offline` when no healthy worker is advertising that runtime.

The existing launch button remains disabled when the runtime is unavailable. No visual redesign, layout/navigation change, global token change, or new frontend shell was introduced.

## Broader Customer Dashboard reconciliation status

The current repository acceptance matrix and action inventory continue to identify these source-level areas:

- Chat: conversation restore, enqueue, attachments, authenticated SSE/replay, cancel, safe retry, citations.
- Agent Studio: runtime catalog, saved Agent configuration, worker capability snapshots and tool allowlists.
- Workflow/Tasks: durable run history, progress, dependency projection, approval decisions, cancellation, retry semantics, events and artifacts.
- Files/Artifacts: owner-scoped workspace/file lifecycle, immutable versions, private artifacts and signed downloads.
- Analyse/Knowledge/RAG: document ingestion, chunk pagination, selected-document retrieval and provenance.
- Personal Memory: consent, owner-scoped CRUD, worker consent filtering and retention purge implementation.
- Create Studio: Chat handoff and file artifact path; image/video generation remain gated on real provider credentials, price/metering, entitlement/quota and artifact configuration.
- Wallet/usage: read-only balance, entitlement, ledger and usage views; checkout/top-up settlement is unavailable without payment provider contracts.
- Partner Wi-Fi/OTP/gateway, OAuth connectors, full device-session revocation and support-ticket provider flows remain partial or unavailable until their real external contracts and credentials exist.

## Known integration boundaries and gaps

1. Model/provider routing is server-side and remains PARTIAL/GATED; the browser must not call provider APIs or expose secrets.
2. Tool catalog visibility is not proof of executable capability. Worker heartbeat, adapter registration, policy, isolation and approval remain authoritative.
3. Manual retry creates a new Agent Run only for safe replayable failed runs. Automatic retry and approval continuation recover the existing durable run/checkpoints. No manual in-place checkpoint rewind is exposed.
4. External payment, OTP/gateway, connector OAuth and support provider flows must fail closed until provider contracts/credentials and security requirements are satisfied.
5. Classroom/teacher governance and some institutional EduTech features remain outside the completed learner curriculum core.
6. A static source audit cannot prove production worker health, LLM credentials, provider billing, RLS denial paths, event replay correctness or end-to-end persistence.

## Verification boundary

Per product-owner instruction, no tests, lint, typecheck, build, browser screenshots, API probes, worker execution, provider calls, staging or deployment were performed. This report records source inspection and a targeted source correction only. It does not claim runtime acceptance or Phase 09 completion.

## Phase status and dependency

Phase 09 remains **IN PROGRESS**. The Customer Dashboard integration must not be marked complete while source-level action/contract gaps and provider-dependent gates remain unresolved. Phase 10 E2E verification and Phase 11 release gate remain dependency-next and are intentionally not executed under the current instruction.

## Tasks lifecycle UI correction — 2026-11-14

- Fixed the Tasks view's projection of terminal Agent Run states. Only `succeeded` is presented as successful completion; failed, cancelled, timed-out and expired runs remain terminal but are not shown with success styling.
- The Active filter now excludes all terminal states; the Selesai filter shows terminal outcomes while preserving their actual status labels.
- Removed nested button markup in the task card so the card itself remains the single interactive detail target.
- Added optional canonical `status` to the TaskItem presentation type.
- Commits: `41d394731bbcc512ca35ebb2cd2c63f64f9740f8`, `e2cff38d614f87dcda1013f777849af8a358717b`.
- Not browser-verified; all runtime acceptance remains NOT VERIFIED.

## Chat model-routing transparency — 2026-11-14

- The FastAPI `/api/v1/models/capabilities` endpoint and typed client were present but the Customer Chat composer did not expose the enabled model registry.
- Added a compact, collapsible **Model & capability tersedia** section to Chat. It reads enabled provider/model names and normalized capability tags from the authenticated catalog endpoint.
- The UI explicitly communicates that actual model selection remains automatic in the backend Model Router, based on task/capability/policy. It does not let a customer bypass provider routing, entitlements or quotas.
- Registry failures are displayed as a non-blocking warning and do not fabricate available models or imply that generation is possible.
- Source commit: `33ea20b19a7bbe4d064ace8da8f9c83c336c9b09`.
- Source-only change; no browser verification, API probe, tests, lint, typecheck or build was performed.

- Follow-up copy correction commit: `83b694b410606d4e9c86d87654c430a87ea8cfc0`. The model registry panel distinguishes enabled provider/model registry entries from per-customer entitlement; actual execution remains subject to entitlement, quota, router and worker policy.


## Manual retry policy parity — 2026-11-14

- Compared the Tasks retry action against FastAPI `POST /api/v1/customer/agent-runs/{run_id}/retry`.
- Backend permits manual new-run retry only for `failed`, `timed_out`, and `expired`, and independently blocks retries when execution is disabled, the original conversation/runtime is unavailable, or a side-effecting tool was reached. `cancelled` is terminal but not manually retryable.
- Tightened the Tasks handler guard to the same exact status allowlist; the detail button and handler now agree with the FastAPI contract. Backend safety checks remain authoritative.
- Commit: `79378c9aa6c12f52ce81268335552efbaea39527`.
- Source-level only; no runtime verification or prohibited checks were performed.


## Customer action-to-endpoint audit continuation — 2026-11-14

Source inspection continued across Tools Catalog, Knowledge Library, Files, Notifications, Profile/Preferences, Personal Memory, Workflow Progress, Agent Studio and Chat:

- Tools Catalog reads the platform tool registry and displays registration/worker/policy metadata; it is informational and does not claim that a catalog entry is customer-entitled or directly executable.
- Knowledge Library upload, pagination, document detail/chunk paging, retry and archive actions call the authenticated FastAPI knowledge API. Retry is restricted by backend to owner-scoped failed file documents with a retained private source object; archive is restricted to ready/failed and remains a soft archive. UI local projection follows the returned accepted state; ingestion completion remains worker-owned.
- Files view uses artifact/workspace APIs for listing, upload, version history and downloads; no browser-side Storage access was identified in the reviewed component.
- Notifications mark-read and mark-all-read await API success before changing the local projection. Profile identity/preferences and Personal Memory mutations use their respective FastAPI clients; Supabase browser client is used only as an Auth identity fallback.
- Workflow Progress consumes durable run, approval, step/activity, artifact and stream APIs. Approval decision is persisted through the backend atomic decision path; the UI refreshes runs after success and separately reports refresh failure without undoing the durable decision.
- Agent Studio reads published agents and tool registry, persists customer agent configurations through create/update/delete APIs, and hands the selected configuration ID to Chat. Chat includes that ID in the message enqueue contract so FastAPI can apply the stored configuration.
- Create Studio remains a prompt-to-Chat handoff. It checks worker-reported media capabilities and explicitly avoids claiming image/video/file artifacts before backend tools return persisted results. It does not yet implement a standalone customer media job lifecycle or expose a complete credit reservation/metering ledger for those jobs.

This is source-contract inspection only. It does not establish live Supabase/RLS behavior, worker execution, provider credentials, media billing, UI behavior, or end-to-end success. No tests, lint, typecheck, build, browser/API probes, worker execution, provider calls, staging or deployment were performed. Phase 09 remains IN PROGRESS.

## Workflow retry recovery action — 2026-11-14

- Added an explicit **Retry sebagai run baru** action in Workflow & Agent Runs for only `failed`, `timed_out` and `expired` runs.
- The action calls the existing authenticated FastAPI `POST /api/v1/customer/agent-runs/{run_id}/retry` contract with a fresh idempotency key. It does not locally reset or mutate persisted checkpoints.
- After an accepted retry, the UI reloads the canonical run page and clears stale detail projections for the original run. The new run remains authoritative in the server response.
- Backend replay-safety, execution-enabled, conversation ownership, runtime availability and side-effect checks remain mandatory; a UI-eligible status does not guarantee the backend will accept replay.
- The action is serialized with the existing per-run action lock and surfaces backend errors without fabricating a new run.
- Source commit: `913b0cd422ccec76bf82c47c62f90ec91f48599f`.
- This does not add manual checkpoint rewind. Automatic retry/approval continuation continue to use backend-owned durable recovery semantics.
- Source-only implementation; no tests, lint, typecheck, build, browser/API probes, worker execution, provider calls, staging or deployment were performed.

## Durable workflow checkpoint visibility — 2026-11-14

- Workflow detail now retrieves the authenticated Agent Run event endpoint in addition to step/activity/progress projections.
- It renders only checkpoint projections supplied by FastAPI's `_event_with_checkpoint_state` safe serializer. Private tool arguments, observations and credential-bearing fields remain excluded by the backend.
- Checkpoint snapshots refresh when the durable event stream reports planning/tool/checkpoint/run lifecycle changes; event retrieval is performed alongside the existing run/step/activity/progress snapshot.
- This is observability and recovery-state visibility, not a client-side resume or checkpoint mutation control. Worker remains the authority for checkpoint reconciliation, dependency execution and recovery.
- API client event type now models the nullable safe checkpoint payload.
- Source commits: `16fd19ac39160fe629f2b52c4bc3b2d16df5aef8`, `58a63b417567b238db3f87587c1f05ae1ca72732`, `139f5af87f4861eec3ba1c0ba86c1fca010daf8a`.
- Source-only; no tests, lint, typecheck, build, browser/API probes, worker execution, provider calls, staging or deployment.

## Media adapter and Agent Studio runtime-policy reconciliation — 2026-11-14

Source inspection of `apps/worker/app/registry_factory.py`, `engine/tools/media.py`, `engine/tools/video.py`, `apps/worker/app/llm_accounting.py`, `apps/worker/app/dispatcher.py` and `engine/agents/durable_tool_runtime.py` refines the remaining media/runtime gap:

- Image and video adapters already exist in the worker registry. They are registered only when media billing, provider credentials, entitlement/quota keys, currency/credit conversion, explicit price maps and artifact storage are configured. Provider calls are not made during this source review.
- Both adapters use idempotent request claims and atomic credit/quota reservation through the shared accounting RPC contract, persist provider results and settle actual usage. Failure paths retain reservations when provider outcome is unknown rather than releasing credits unsafely.
- Video generation persists provider task ID/status and artifact receipt in run checkpoints, polls the provider task, validates the output host/content type/size, stores the binary artifact, then records and finalizes usage. Image generation persists the generated image as a run artifact and stores the provider result for recovery/settlement.
- These media operations are currently tools inside a durable Agent Run, not a separately exposed customer media-job resource/API. The Customer UI can track the parent Agent Run and its persisted artifacts, but does not yet expose a dedicated media task view/status model. The remaining work is to reconcile the user-facing job lifecycle, safe provider/task status projection and artifact presentation with the durable run, not to invent a parallel media engine or duplicate billing ledger.
- Agent Studio's supported saved-config runtimes (`manus`, `toolcall`) match FastAPI's request/response contract. FastAPI validates configured tools against the runtime catalog; the worker validates the saved runtime/config identity and narrows actual tool definitions to the saved allowlist while retaining mandatory completion/termination primitives. Saved instructions are injected as user-level preferences and cannot override trusted system policy. The current UI further limits selectable tools to the live worker's reported tool keys; actual runtime remains the final enforcement boundary.
- This source review does not prove that deployment environment variables, provider credentials, wallet policies, worker heartbeats, provider tasks or live artifact storage are configured correctly. No provider API or Supabase mutation was executed.

Remaining media work: add a customer-facing durable media-job projection over Agent Run/checkpoint/artifact data, clarify queued/submitted/processing/succeeded/failed/unknown outcomes, and make recovery/refresh behavior explicit without duplicating run or credit records. Phase 09 remains IN PROGRESS.

## Customer-facing media lifecycle projection — 2026-11-14

- Workflow & Agent Runs now detects image/video generation from the persisted run activity tool projection (`image_generate` / `video_generate`) and correlates it with artifacts whose metadata identifies `media_type=image|video` and the same `run_id`.
- The expanded run detail displays a media lifecycle panel. A persisted media artifact is shown as succeeded and exposes its existing owner-scoped signed-download action. When the media tool is present but no artifact is yet available, the panel reports processing for an active parent run, failed for a failed parent run, or unknown for other terminal outcomes.
- The panel deliberately does not infer provider task states (submitted/polling) from absent fields. FastAPI's current safe checkpoint projection excludes provider task identifiers/status and provider internals; the UI labels that limitation and directs the user to durable run/checkpoint details. This avoids exposing private worker state or inventing a separate media job record.
- This is a source-level Customer UI integration over existing Agent Run, activity, artifact and signed-download APIs. No new database table, billing ledger, provider call or media execution endpoint was added.
- Implementation commit: `77ce09d64b0ddd097a9ba4d134a59ebec5039015`.
- Source-only; no tests, lint, typecheck, build, browser/API probes, worker execution, provider calls, staging or deployment.

## Customer benefits, wallet, profile/security and service audit — 2026-11-14

Source audit of `benefit-credit-view.tsx`, `account-upgrade-view.tsx`, `profile-settings-view.tsx`, `personal-memory-settings.tsx`, `security-settings-view.tsx`, `notifications-view.tsx`, and `files-view.tsx`:

- Benefit & AI Credit Center reads active wallets, entitlements, quotas, usage, currency-scoped ledger pages and network sessions from authenticated Customer FastAPI endpoints. History pagination merges server pages without duplicate IDs. Balances are not summed across currencies.
- Top Up is explicitly unavailable and does not mutate wallet state. Account Upgrade reads entitlement state but checkout/subscription activation is explicitly blocked until a real payment contract exists. This is intentional; no fake checkout or local balance mutation is introduced.
- Profile identity, locale and notification preferences use FastAPI. Supabase browser access in profile view is an Auth-only fallback for identity when the business API is unavailable.
- Personal Memory consent and CRUD operations use Customer FastAPI; mutations are applied to the UI only after server success.
- MFA factor enrollment/challenge/verification and factor removal use Supabase Auth MFA APIs. These are authentication-provider operations, not direct business database writes.
- Notifications list, pagination, mark-read and mark-all-read use FastAPI and only update the local projection after accepted responses. Destination routing is a UI navigation concern.
- Files view reads artifacts and workspace files/version history through FastAPI and downloads through signed artifact/workspace endpoints. No browser Storage service-role or direct business table access was observed in these components.
- Security boundaries: no payment checkout, partner voucher redemption, OTP delivery, captive gateway/device control, or external support-ticket provider is claimed as operational without corresponding real provider/business contracts. The benefit view's voucher/ledger navigation is not itself proof of redemption workflow completion.

Remaining follow-up is to reconcile the separate voucher redemption and partner-specific benefit actions with their exact backend endpoints and to distinguish unavailable external service integrations from completed account/profile functionality. No payment or external service call was made.
