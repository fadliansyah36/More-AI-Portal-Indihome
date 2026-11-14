# Phase 09 — Agent Configuration, Dynamic Capability Registry & Create Studio

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Source HEAD before documentation: `04432e27448e7ae8d285e33a9dc123411519f5df`

## Owner constraints

- Implement directly on `main`.
- No staging or deployment.
- No tests, lint, typecheck, build, browser/API/worker runtime verification or provider calls.

These constraints were observed. Source review and successful Supabase migration application are not represented as runtime acceptance.

## Implemented

### 1. Owner-scoped Agent Configuration

- Added `moreai_customer_agent_configs` with owner identity, runtime key, name, description, optional custom instructions, tool allowlist, enabled state and configuration version.
- Added owner-name uniqueness and owner/update indexes.
- RLS is enabled; browser roles have no table privileges. FastAPI uses the server-side repository with explicit owner filters.
- Added Customer APIs:
  - `GET /api/v1/customer/agents/configurations`
  - `POST /api/v1/customer/agents/configurations`
  - `PATCH /api/v1/customer/agents/configurations/{id}`
  - `DELETE /api/v1/customer/agents/configurations/{id}`
- Customer Agent Studio now supports create, edit, delete and use saved configurations, including runtime selection, custom description/instructions and selected tools.
- Configuration is restricted to the registered Manus and ToolCall runtimes. Planning remains a platform runtime because its plan/execution contract is not yet a custom-agent configuration contract.
- The API validates selected tools against the code-registered OpenManus catalog and the runtime's declared availability. The worker then narrows the actual tool definitions to the selected allowlist; it cannot add tools that are not registered.
- User-authored instructions are included as a user-role preference message, never promoted into the trusted system prompt. Runtime/system policy and approval enforcement remain authoritative.
- Configuration snapshots are embedded atomically in the durable Agent Run input, so later edits/deletion do not silently mutate a task already queued.
- Chat handoff carries the selected configuration ID into the typed Customer enqueue request. Attachment-aware enqueue and safe retry preserve the same saved configuration snapshot.

### 2. Dynamic Worker Capability Registry

- Added `moreai_worker_capability_snapshots` with server-only access and a service-role-only heartbeat RPC.
- Worker derives capability data from actual registered runtime adapters and their policy-filtered tool definitions, rather than copying static catalogue claims.
- Worker publishes at startup and every 30 seconds. API treats a snapshot as live only when it is healthy and no older than 90 seconds.
- `GET /api/v1/agents` now reports runtime availability, active worker count, live tool keys and last heartbeat.
- Customer Agent Run enqueue and retry fail closed with HTTP 503 when no healthy worker advertises the requested runtime; no queued task is created in that case.
- Added `GET /api/v1/media/capabilities`, derived from live worker-advertised adapters:
  - `file_generation` is available only when a healthy worker registers `file_saver`.
  - `image_generation` requires a registered `image_generate` adapter.
  - `video_generation` requires a registered `video_generate` adapter.
- No static “online” status or fake media availability is returned.

### 3. Create Studio — Image / Video / File

- Added a File category and real file-artifact handoff through Manus and the existing `file_saver` tool.
- File generation is gated by the live worker capability endpoint. The prompt explicitly requires an actual artifact write confirmation before the Agent may claim completion.
- Image generation is now capability-gated. It can only hand off to Chat when the worker advertises an actual `image_generate` adapter; otherwise it explains that no image was generated and no credit was charged.
- Video generation is capability-gated. When no `video_generate` adapter exists, Create Studio only creates a script/storyboard task and explicitly states that no rendered video is produced.
- The current worker does not register image or video generation adapters. No OpenAI media provider was activated because provider credentials, entitlement/credit reservation, media usage metering, and durable media artifact persistence are not yet connected. Future OpenAI capability must be added as a server-side worker adapter and exposed through the same live registry; no OpenAI key belongs in the browser.
- The existing UI structure and MoreAI PRD v1.2 tokens remain unchanged; the new configuration panel follows the adjacent white/light surface, red primary action, navy text and subtle cool-gray border patterns.

## Supabase changes

Applied to the bound MoreAIdb project:

1. `moreai_customer_agent_configuration_capability_registry`
   - owner-scoped Agent configuration table;
   - worker capability snapshot table;
   - worker heartbeat RPC;
   - atomic configured Chat enqueue RPC.
2. `moreai_agent_config_chat_attachments`
   - attachment-aware overload of configured Chat enqueue;
   - validates owner, conversation, artifact purpose, MIME type and size before linking attachments;
   - preserves idempotency and stores the configuration snapshot on the durable run.

Both migration applications returned `success: true`. Source migration files are committed under `supabase/migrations/`.

## Important limitations

- This is not completion of all Phase 09 Customer API actions.
- Payment/checkout/settlement, official EduTech catalog and protected video, OTP/gateway activation, support ticket provider and real provider activation remain unavailable without their actual contracts and credentials.
- OpenAI image/video generation is not live. The current worker advertises no image/video adapters; the UI therefore fails closed for rendered media.
- File generation depends on the existing worker storage adapter and private artifact bucket being correctly configured. It has not been exercised in this increment.
- Worker heartbeat, API readiness, RLS, Agent config dispatch, attachment linkage, artifact writes and media actions have not been runtime-verified.

## Verification and release boundary

- No tests, lint, typecheck, build, browser checks, API/worker runtime checks, provider calls, staging or deployment were run.
- Supabase migration application is the only live system mutation in this increment.
- Source changes are committed to `main`; no claim is made that these flows have passed runtime verification.

## Remaining Phase 09 sequence

1. Finish the Customer API action inventory and close every remaining actionable UI gap without seeded/demo fallback behavior.
2. Complete workflow/task lifecycle integration, including dynamic tool availability, retry/approval/cancel/recovery and artifact result presentation.
3. Integrate actual OpenAI image generation and a supported video provider only through server-side worker adapters, provider-secret references, entitlement/quota checks, idempotent reservations, usage metering and durable artifact storage.
4. Complete payment, EduTech, OTP/gateway and support APIs against real provider contracts.
5. Close the remaining Customer Dashboard gaps and reconcile every screen against Master PRD v1.2.
6. Runtime/E2E verification remains deferred until the owner changes the no-testing instruction.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED** by the controlling release gate.


## Follow-up hardening after initial report

- Added `moreai_agent_config_retry_snapshot` migration and `moreai_enqueue_chat_run_with_config_snapshot` RPC. A safe manual retry now validates the original owner-scoped run and reuses its exact immutable Agent configuration snapshot, even if the saved configuration was later edited or deleted.
- The retry RPC independently checks the source run state, original prompt/runtime/config/attachments, attachment ownership and the durable tool-event allowlist before creating a new run.
- Runtime now enforces saved tool allowlists both when advertising tool definitions and immediately before tool execution; unselected registered tools cannot be invoked through a hallucinated function call.
- Agent Studio only offers tool choices reported by a live healthy worker and disables saved Agent launch while its runtime is offline.
- Follow-up migration `moreai_agent_config_retry_snapshot` was applied successfully; no runtime verification was performed.
- Follow-up source commits include `c2ab2538`, `4bc4dc2e`, `502089b9`, `e4df5a37`, `1069b152`, `57978256`, `deb8d374`, and `e8c9bc36`.
