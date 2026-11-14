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


## OpenAI Image Generation adapter — source integration follow-up

- Added `engine/tools/media.py` with a server-side OpenAI Images API adapter using the current `gpt-image-2` model and `POST /v1/images/generations`.
- Added private binary artifact persistence to `SupabaseArtifactTool.binary_saver`. The adapter stores the generated image in the configured private artifact bucket and returns only the owner-scoped artifact reference/metadata; it does not return a public Storage URL.
- Added `image_generate` to the canonical OpenManus tool catalog and registered it in Manus/ToolCall only when all server-side secret, wallet, entitlement, quota and price configuration is present.
- Image generation reserves wallet credits and media quota before provider invocation through the existing idempotent request/reservation lifecycle. It settles against an explicit per-image USD price map; provider timeouts/ambiguous outcomes retain the reservation and block duplicate execution instead of silently releasing credits.
- The adapter does not assume Image API token usage fields. Image output cost is configured per size/quality; the usage ledger records the configured USD cost and leaves LLM token counters at zero for this media operation.
- Required Worker environment:
  - `OPENAI_API_KEY` (server-only secret)
  - `MOREAI_MEDIA_BILLING_ENABLED=true`
  - `MOREAI_MEDIA_ENTITLEMENT_KEY`
  - `MOREAI_MEDIA_QUOTA_METRIC_KEY`
  - `MOREAI_CREDIT_WALLET_CURRENCY`
  - `MOREAI_CREDITS_PER_USD`
  - `MOREAI_OPENAI_IMAGE_COSTS_JSON` (explicit map such as `{"1024x1024:low":0.006,"1024x1024:medium":0.053,"1024x1024:high":0.211}`; confirm current OpenAI pricing before configuration)
  - optional `MOREAI_OPENAI_IMAGE_MODEL=gpt-image-2` and `MOREAI_IMAGE_PROVIDER_TIMEOUT_SECONDS=600`
- The worker does not register the adapter unless every required variable is present and valid. No key was created or read, no provider request was made, and the adapter is not claimed active in the current deployment.
- GPT Image organization verification may be required by OpenAI. See [Image generation docs](https://developers.openai.com/api/docs/guides/image-generation) and [pricing details](https://developers.openai.com/api/docs/guides/image-generation#cost-and-latency).
- Source changes are recorded in the repository history on `main`; this report intentionally avoids a partial or unverified commit-hash list.


## Runway Dev video adapter — source integration follow-up

- Added `engine/tools/video.py` with a Runway Dev text-to-video adapter using `POST /v1/text_to_video`, the required `X-Runway-Version: 2024-11-06` header, and `GET /v1/tasks/{id}` polling.
- The provider task ID is persisted to the existing durable Agent Run checkpoint before polling. Recovery resumes the same provider task; an ambiguous submit outcome is marked unknown and never resubmitted automatically.
- The adapter reserves MoreAI wallet credits and media quota before provider submission, uses an explicit maximum USD price map per model/duration/ratio, then settles from Runway's returned `estimatedCost.credits` and configured USD-per-Runway-credit conversion.
- Generated MP4 output is downloaded only from configured HTTPS host suffixes and stored as a deterministic, private Supabase artifact. Task ID, artifact and completion result are checkpointed for recovery.
- Registered canonical `video_generate` tool in Manus/ToolCall only when all required provider, pricing, billing, wallet, quota, entitlement and output-host allowlist settings are present. Dynamic capability snapshots now report provider identity; Tool Catalog and Create Studio show actual live provider availability.
- Required Worker environment:
  - `RUNWAYML_API_SECRET` (server-only secret)
  - `MOREAI_MEDIA_BILLING_ENABLED=true`
  - `MOREAI_MEDIA_ENTITLEMENT_KEY`, `MOREAI_MEDIA_QUOTA_METRIC_KEY`
  - `MOREAI_CREDIT_WALLET_CURRENCY`, `MOREAI_CREDITS_PER_USD`
  - `MOREAI_RUNWAY_VIDEO_MODEL=gen4.5` (the source adapter currently enables Gen-4.5 only)
  - `MOREAI_RUNWAY_VIDEO_COSTS_JSON` with a maximum USD reservation for each allowed `model:duration:ratio` combination; default registration requires `gen4.5:5:1280:720`
  - `MOREAI_RUNWAY_CREDIT_USD` (USD conversion for one provider credit, based on the provider account's current pricing)
  - `MOREAI_RUNWAY_OUTPUT_HOST_SUFFIXES` (comma-separated HTTPS output host suffix allowlist)
  - optional `MOREAI_VIDEO_PROVIDER_TIMEOUT_SECONDS=420`, `MOREAI_RUNWAY_POLL_INTERVAL_SECONDS=5`, `MOREAI_MEDIA_MAX_ARTIFACT_BYTES=100000000`
- No Runway key was created/read, no price/host configuration was supplied, and no provider request was made. The adapter is source-integrated but not registered/active in the current deployment.
- Runway Dev official reference: [API Reference — Text to video and Task management](https://docs.dev.runwayml.com/api/). Its task detail API advises against polling more frequently than every five seconds; this adapter uses a five-second minimum interval.
- Source changes are recorded in the repository history on `main`; this report intentionally avoids a partial or unverified commit-hash list.

- Provider-specific tool execution bounds were added: image generation defaults to 360 seconds (HTTP timeout 300 seconds); video generation defaults to 600 seconds with a maximum 420-second provider poll window to leave time for download, private artifact storage and usage settlement. These bounds are independent from the general 120-second tool timeout.

- The current Runway adapter is intentionally limited to model `gen4.5` and durations `5` or `10` seconds; other model/duration combinations remain unavailable until their API parameters and price map are explicitly added.
