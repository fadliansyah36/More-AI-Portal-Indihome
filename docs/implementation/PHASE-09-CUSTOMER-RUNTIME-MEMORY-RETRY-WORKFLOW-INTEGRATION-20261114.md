# Phase 09 — Customer Runtime, Memory Privacy, Retry & Workflow Integration

Date: 2026-11-14  
Branch: `main`  
Starting HEAD: `30f4df8fc6dacbf67af769c3f23d1e1055b6988b`  
Source implementation HEAD before this report: `86b176dcb5fc2b7412c244141323aa6c9c1fe3ca`

## Owner constraints

- Direct implementation on `main`.
- No staging.
- No tests, lint, typecheck, build, browser/API/worker runtime verification, provider calls or deployment.

These constraints were observed. Source review and connector metadata inspection were not used as substitutes for runtime acceptance.

## Implemented in this increment

### 1. Personal Memory privacy lifecycle

- Added `moreai_customer_memory_preferences` and `moreai_customer_memories`.
- Added owner-scoped RLS policies, server-only table privileges and consent/clear RPCs.
- Applied migration `20261114010000_moreai_customer_personal_memory_privacy.sql` directly to the bound MoreAIdb Supabase project. Supabase returned `success: true`.
- Added FastAPI customer APIs for state/review, explicit consent enable/disable, user-authored memory create, correction, retention changes, per-item deletion and atomic clear-all deletion.
- Retention is limited to 30/90/180/365 days. Expired records are excluded from runtime context, opportunistically purged on the owner's memory read, and periodically deleted by a worker maintenance RPC (default every six hours; configurable within 1–24 hours).
- Added the Personal Memory panel to existing Profile Settings: consent toggle, add, review, edit, retention, delete one and delete all.
- Conversation transcript storage remains separate from Personal Memory. No chat, attachment or workspace content is silently ingested.
- Added `SupabasePersonalMemoryStore` to the worker. Manus/ToolCall execution loads at most 20 active records only when the owner has current enabled consent. Records are bounded and injected as explicitly untrusted context, never as policy or instructions.

### 2. Safe Chat regenerate and Task retry

- Added owner-scoped `POST /agent-runs/{run_id}/retry` using the existing atomic chat enqueue RPC and a mandatory idempotency key.
- Manual rerun is limited to failed/timed-out/expired runs. Cancelled and successful runs are not manually replayed.
- Before re-enqueue, the API inspects durable tool events. If a side-effecting tool started/completed/failed or the tool identity is missing, the rerun is rejected to avoid duplicate external effects.
- Added Chat retry action for eligible failed runs and Task detail retry action.
- This action creates a **new Agent Run**, not a checkpoint resume. Existing worker automatic retry, lease recovery and approval resume remain the checkpoint-aware recovery paths. The UI/API do not claim manual rerun resumes a previous checkpoint.

### 3. Agent Studio runtime and tool catalog

- Agent API now exposes the three code-registered customer runtimes: `manus`, `planning`, and `toolcall`, even when the `agent_definitions` table has no seeded rows.
- Existing database definitions can customize display name/description or disable a registered runtime. Unregistered runtime keys are not advertised.
- Agent response now includes capability tags and mapped tool keys derived from the OpenManus tool catalog.
- Corrected default tool-to-runtime mapping for the three registered runtimes.
- Added typed tool catalog client and Agent Studio policy display with risk/approval metadata. Conditional browser, sandbox, search and knowledge tools are not presented as active merely because they exist in the catalog.

### 4. Workflow execution visibility

- Workflow Progress now subscribes to the authenticated durable Agent Run SSE stream while a run is expanded.
- Lifecycle events refresh owner-scoped run snapshots, workflow steps and safe activity projections. Terminal state closes the stream.
- Existing Task detail SSE remains the Customer Task lifecycle source.

### 5. Create Studio routing carried forward

- Text/document authoring and translation route through Manus.
- Multi-step document summary, presentation planning and video storyboard route through Planning.
- Image generation remains fail-closed because no verified media generation provider/adapter is available. Video handoff creates a text script/storyboard only.

## Principal files changed

- `supabase/migrations/20261114010000_moreai_customer_personal_memory_privacy.sql`
- `apps/api/app/repositories/supabase.py`
- `apps/api/app/routers/customer.py`
- `apps/api/app/routers/catalog.py`
- `apps/worker/app/memory_store.py`
- `apps/worker/app/registry_factory.py`
- `engine/agents/durable_tool_runtime.py`
- `engine/tools/catalog.py`
- `lib/api/client.ts`
- `types/moreai.ts`
- `components/views/personal-memory-settings.tsx`
- `components/views/profile-settings-view.tsx`
- `components/views/chat-view.tsx`
- `components/views/tasks-view.tsx`
- `components/views/agent-studio-view.tsx`
- `components/views/workflow-progress-view.tsx`

## Verification and release boundary

- Supabase migration application returned success.
- No tests, lint, typecheck, build, browser, API, worker, provider or end-to-end runtime verification was run.
- No staging or deployment was performed.
- Therefore source implementation is committed, but runtime behavior and Phase 09 acceptance remain unverified.

## Remaining Phase 09 work

1. Reconcile every remaining Customer action against FastAPI contracts and remove any ungrounded demo/fallback behavior.
2. Complete agent-definition/configuration management and dynamic worker capability/health reporting; the current Agent Studio catalog is the code-registered runtime/tool policy view, not a custom-agent editor.
3. Integrate actual image/video generation only after a provider contract, credentials, entitlement, metering and artifact adapter are available.
4. Finish remaining customer workflow/run lifecycle edge cases and verify the retention maintenance job once runtime verification is permitted.
5. Complete provider-gated payment, EduTech, OTP/gateway and support contracts only against available vendor integrations.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED** because verification is explicitly disallowed. Phase 11 remains **BLOCKED**.
