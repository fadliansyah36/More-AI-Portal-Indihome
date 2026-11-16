# Phase 09 — Unified Memory Context Coordinator (2026-11-16)

## Scope and commits

Target branch: main  
Source commits:
- 50926ee1bd32846ba4b6c31cf11484e9293f0f6f — extend MemoryContextCoordinator to collect owner/workspace-scoped memory domains.
- 2affed0468d0cf6a5a1ee7f3dc12de6c5e0f32e3 — route DurableOpenManusRuntime context composition through the coordinator.
- fa361c04efb100164853b4cba6b202b65d18a3b0 — retain the coordinator's working-checkpoint snapshot as the current run recovery state.

Changed files:
- engine/agents/memory_context.py
- engine/agents/durable_tool_runtime.py

## Memory domain mapping

The Customer Agent Run now asks one MemoryContextCoordinator for a bounded AgentMemoryContext. The coordinator reuses existing canonical stores and does not create a second database or duplicate memory persistence.

| Memory domain | Canonical source | Coordinator behavior |
|---|---|---|
| Working | Agent Run recovery checkpoints and durable plan/checkpoint records | Carries the current run checkpoint snapshot used by the existing recovery/tool runtime |
| Conversation | conversation_messages scoped by conversation, owner, workspace and run | Restores run history, idempotently appends the user prompt if missing, then loads bounded conversation history |
| Long-term / Personal | moreai_customer_memories and memory consent preferences | Loads only user-authored personal records under the existing versioned consent and expiry checks |
| Episodic | consented episodic metadata on conversation_messages | Loads only non-expired episodes in the exact owner/workspace scope; expiration/cleanup remains in the existing memory store |
| Semantic | knowledge_documents/knowledge_chunks through the existing Knowledge Search and pgvector path | Uses bounded owner/workspace retrieval, minimum similarity, and validated citation markers |
| Procedural | approved and installed Skill Resolver snapshots | Accepts only snapshots already resolved through owner, validation, license, publication, install, permission and source-integrity gates |

The coordinator does not grant tools, infer permissions from memory or skill text, or treat retrieved content as trusted system instructions. Personal, semantic, episodic and procedural context remain explicitly labelled untrusted evidence/preferences. Tool policy and server-side authorization remain authoritative.

## Behavior preservation

- Conversation prompt append remains idempotent using the existing run-scoped message key.
- Personal Memory is still opt-in using the existing consent version; no default opt-in is introduced.
- Episodic retrieval remains consent-gated, workspace-scoped, bounded and time-limited.
- Semantic retrieval remains optional and emits the same durable failure event when the optional recall source is unavailable.
- Skill resolution occurs before memory composition and continues to be permission-gated; the coordinator only renders the approved resolver output.
- The current Customer screens and Personal Memory component are unchanged.

## Supabase

No Supabase migration, table, index, policy, RPC or data record was added or modified by this source increment. No new database was introduced. The previous applied ingestion migrations remain separate from this Memory refactor.

## Verification and limitations

- No tests, lint, type-check, build, browser/API runtime, worker/provider execution, staging or deployment was run, in accordance with the product-owner instruction.
- The changes are source commits only; the persistent worker deployment is not available, so runtime activation is not claimed.
- The six domains now share one retrieval/composition coordinator, but their durable persistence intentionally remains in the existing canonical services/tables. This is not a claim that all data is stored in one physical memory table or that unconsented content is retained.
- No new procedural-memory table was added: approved immutable Skill snapshots remain the procedural knowledge source. Workspace/plan/checkpoint records remain the working/run source.

## Phase decision

Phase 09 remains IN PROGRESS. Phase 10 is NOT ACCEPTED and Phase 11 remains BLOCKED.

Next work follows the required operational order: provision encrypted OpenFuse host; configure the encrypted GitHub source token; deploy the approved FastAPI source through its existing release path; run the authenticated 230-entry Customer Skill batch; complete residual SBOM, licence, NOTICE, provenance and asset review; configure approved providers/pricing/credit policy; start persistent worker and obtain heartbeat/readiness; finish the Customer action/security audit.
