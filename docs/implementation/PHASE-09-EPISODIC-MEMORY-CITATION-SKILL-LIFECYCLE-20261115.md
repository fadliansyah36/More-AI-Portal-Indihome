# Phase 09 — Episodic Memory, Citation Provenance & Skill Lifecycle

Date: 2026-11-15  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Baseline HEAD: `c666d09d352adebc2811a4840ef79fa8f6627195`

## Owner execution constraints

- Work directly on `main`.
- Do not run real tests, build, lint, typecheck, browser/API/worker/provider verification, staging or deployment.
- Do not perform live Supabase schema/data mutations.
- Preserve the existing Customer Dashboard UI except for the missing Memory capability surface; additions follow the adjacent existing MoreAI white/light, red-action, navy-text and subtle-border styles.

These constraints were observed. This report records source changes only, not runtime acceptance.

## Implemented in this continuation

### 1. Episodic Memory write and retrieval

- Extended the existing `Message` data object with bounded metadata support; metadata is persisted in the existing `conversation_messages.metadata` JSONB column and is not forwarded into LLM message payloads.
- OpenManus now retrieves up to eight prior episodic records from the exact owner/workspace scope when the owner has enabled the current explicit consent version `2026-11-14.v1`.
- Prior task prompts and outcomes are injected as untrusted historical context, not system instructions.
- Successful Agent Runs persist an episodic summary containing prompt, outcome, model key, run ID, up to ten citation references, up to ten skill snapshots and up to twenty tool/outcome labels. Tool arguments and raw tool observations are not copied into episodic metadata.
- Existing chat history remains separate from episodic recall; disabling or deleting episodic memory does not delete conversation messages.

### 2. Consent, retention and deletion

- Episodic write and retrieval require both `enabled=true` and the current consent version.
- Retention is configurable with worker environment `MOREAI_EPISODIC_MEMORY_RETENTION_DAYS`, default 90 days, accepted range 7–3650. Invalid configuration falls back to 90 days.
- Each episode stores an explicit UTC expiry timestamp.
- Expired episodic metadata is removed opportunistically during retrieval while preserving the underlying chat transcript, message key and citation metadata.
- Customer API now returns owner-scoped episodic summaries with expiry timestamps only while current consent is active.
- Added per-episode deletion that removes only episodic metadata.
- Added `DELETE /api/v1/customer/memory` to disable consent, clear user-authored Personal Memory and remove episodic metadata. Conversation history and citations are retained.
- Disabling consent invokes the existing consent RPC, then removes episodic metadata. If cleanup cannot complete, the API returns an error rather than claiming deletion succeeded.

### 3. Citation provenance through Customer Chat

- Exact cited chunk/document identities remain in the durable Agent Run output.
- The final assistant message now also stores bounded citation metadata alongside the existing message record.
- Customer conversation APIs already resolve and validate citations from the owner-scoped Agent Run output; this path is retained.
- Existing Chat UI already supports displaying citation title, page and source marker, so no duplicate citation component or redesign was introduced.

### 4. Procedural Memory / Skill Resolver lifecycle

- Skill resolution remains based on immutable, hash-verified, validated and licensed-approved package versions.
- Execution still requires an owner-scoped installed package with execution enabled and approved granted permissions.
- Skill snapshots remain checkpointed with the durable run and are recorded in episodic provenance.
- Resolved and executed audit writes are now idempotent across worker recovery.
- Successful normal Agent completion now records skill execution, not only the explicit `terminate` tool path.
- Skill instructions remain untrusted context; permissions are enforced independently by the runtime tool allowlist and approval policy.

### 5. Customer Memory UI

- Extended the existing Personal Memory settings component with an Episodic Memory section.
- Users can inspect prior task summaries, outcomes and expiry dates, delete one episodic record, or clear all memory.
- The clear-all action is available when either Personal Memory records or episodic summaries exist.
- Existing style classes, typography, red action treatment, white/light surfaces and component structure are retained. No global tokens or CSS were changed.
- UI visual regression screenshots were not captured because no browser/runtime verification was performed under the owner constraint; visual regression remains NOT VERIFIED.

### 6. Agent Studio configuration snapshots

Existing source already contains owner-scoped Agent Configuration CRUD, atomic immutable configuration snapshots in Agent Run input, tool allowlists, and retry snapshot reuse. This continuation did not create a second configuration system. Runtime integration and deployment behavior remain unverified.

## Source files changed

- `engine/agents/types.py`
- `engine/agents/memory.py`
- `engine/agents/memory_context.py` (prior semantic recall increment)
- `engine/agents/durable_tool_runtime.py`
- `apps/worker/app/memory_store.py`
- `apps/worker/app/skill_resolver.py`
- `apps/api/app/routers/customer.py`
- `apps/api/app/routers/conversations.py`
- `lib/api/client.ts`
- `components/views/personal-memory-settings.tsx`

## Database and infrastructure boundary

- No migration was added in this increment.
- No Supabase schema, RLS, RPC, storage object or live data was mutated.
- Existing `conversation_messages.metadata`, `moreai_customer_memory_preferences`, `moreai_customer_memories`, `agent_runs`, existing Knowledge Library and Skill audit tables are reused.
- No new vector store, memory database, Agent Runtime or API boundary was introduced.

## Validation boundary

No tests, lint, typecheck, build, browser screenshots, API probes, worker execution, provider calls, staging, deployment or live Supabase mutation were performed. Source files and commits were retrieved from GitHub after writing, but this is source inspection only and does not prove runtime correctness.

## Commit sequence

- `bcd845aa` — bounded semantic Memory Context Coordinator
- `77ee55fa` — semantic recall in OpenManus runtime
- `ff503c27` — retain Knowledge adapter in runtime
- `ecb11d61` / `ea911621` — prior semantic recall report and tracker
- `95da575a` / `facb4f73` — episodic store and consent enforcement
- `5f830145` — episodic recall and run outcome persistence
- `d9557d0f` — conversation citation response contract
- `e8155f7c` / `4f6529cc` / `04811efc` / `b7830095` / `dc25e4f9` — retention, expiry and consent corrections
- `1afc45f4` / `4d9063c1` — clear-memory, consent deletion propagation and per-episode deletion/listing
- `56f95a7e` / `2abaddd5` / `af00baea` — idempotent skill audits and successful execution audit
- `4779d1d4` — Customer API client types/actions
- `9aba25b7` / `c666d09d` — existing Memory settings UI integration
- `8d1f4a4e` — episodic action outcome provenance

## Remaining Phase 09 work

1. Continue the complete Customer Dashboard action-to-FastAPI inventory and close remaining unsupported/demo/fallback behavior.
2. Finish full OpenFuse Browser and Computer capability integration through isolated supervisors, approvals, durable sessions and customer-facing controls.
3. Complete Knowledge deletion/reindex lifecycle, source cleanup and citation display for all customer conversation/message pagination paths.
4. Reconcile the complete Model Router, Agent Studio, tool registry and worker capability snapshot contracts, including runtime configuration and real provider/entitlement availability.
5. Complete every remaining customer screen integration: Chat, Agent Studio, Create, Research, Analyse, Code, Tasks, Workflow, Files/Results, Memory, Connections, Wallet and profile.
6. Update the full customer acceptance matrix and source-to-screen traceability.

## Next work package

**Phase 09 continuation — Customer Dashboard API Closure & OpenFuse Browser/Computer Parity.**

Dependencies: preserve the existing customer API and OpenFuse adapter boundaries; reconcile all remaining customer actions against real typed FastAPI contracts; do not activate browser/computer tools until the existing isolated supervisor and network/approval gates are satisfied.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED**.
