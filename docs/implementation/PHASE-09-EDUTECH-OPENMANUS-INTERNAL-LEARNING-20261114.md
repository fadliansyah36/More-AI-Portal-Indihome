# Phase 09 — Internal EduTech through OpenManus Agent Runtime

Date: 2026-11-14  
Branch: `main`  
Scope: Customer EduTech UI → typed Customer Chat API → durable OpenManus Planning runtime → FastAPI/Supabase run persistence.

## Product decision

EduTech is a first-party MoreAI capability. It does not require an external EduTech vendor. The Customer feature is designed for school students, university students, postgraduate learners and self-directed learners. OpenManus supplies the agent execution engine; MoreAI owns the learning experience, learner identity, access policy, conversation history, task lifecycle and persistence.

## Source implementation in this increment

- Replaced the previous provider-waiting EduTech empty state with a small, additive learning-session composer in the existing `components/views/edutech-view.tsx`.
- Added four learning modes:
  - Structured learning path / curriculum planning.
  - Interactive AI tutor.
  - Adaptive practice and quiz.
  - Project-based learning and case study.
- Added learner topic, education level and learning-goal inputs. The prompt is bounded in the UI and explicitly asks the agent to distinguish sourced facts from assumptions/examples, avoid fabricated citations, use knowledge retrieval only when user knowledge is available, and avoid claiming official grades or certificates.
- The composer selects the existing Planning agent runtime and hands off through the existing `handleStartPrompt` → `ChatView` flow. ChatView creates the normal customer conversation and enqueues the durable Agent Run using the existing authenticated FastAPI contract and idempotency behavior.
- Agent Run progress, steps, activity, cancellation/recovery, conversation transcript and task visibility remain owned by the existing Chat/Tasks/Workflow system. No second learning execution engine was added.
- Existing learning progress read remains connected to the Customer learning API. The existing progress mutation endpoint deliberately rejects arbitrary module/lesson IDs until a trusted learning record exists; this increment does not falsely mark generated lesson content as a canonical course or award completion.
- Existing page design language and layout primitives are retained; changes are scoped to the existing EduTech view and its mount point in `app/page.tsx`.

## Learner workflow

1. Learner selects a subject, level and target outcome.
2. Learner chooses learning path, tutor, quiz/practice or project mode.
3. MoreAI sends a structured learning request into a durable Planning Agent Run.
4. OpenManus Planning decomposes the request into steps; the registered tool policy, LLM gateway, worker, checkpoint and event lifecycle remain authoritative.
5. Learner follows the generated curriculum/material in the conversation, answers tutor/quiz prompts and iterates with the agent.
6. The run appears in the existing Tasks and Workflow surfaces; the conversation is retained in the learner's account.

## Explicit limitations / follow-on work

- This is an AI-guided learning workspace, not yet a full institutional LMS. Structured course enrollment, canonical lesson records, lesson-level progress mutation, grading records, rubric/version management, certificate issuance, instructor/course administration and cohort/classroom management require first-party MoreAI domain schemas and APIs.
- AI-generated curriculum is personalized learning output, not an accredited syllabus or verified institutional course. No external content catalog, protected video vendor or EduTech provider is required for the core workflow.
- The current progress write API remains fail-closed for unverified lesson identifiers. A later additive migration should introduce owner-scoped learning paths, modules, lessons, attempts, quiz responses and rubric-backed assessment records, then connect generated/curated learning assets to those canonical records.
- No provider secrets were configured or called. No tests, lint, typecheck, build, browser/API/worker runtime checks, staging or deployment were performed, per product-owner instruction. Source changes are not runtime acceptance evidence.

## OpenManus agent and tool capability inventory

### Upstream agent abstractions / paradigms

- `BaseAgent`: stateful execution foundation.
- `ReActAgent`: think/act loop.
- `ToolCallAgent`: structured model tool/function calling.
- `PlanningAgent`: plan creation, step tracking and plan-aware execution.
- `Manus`: general-purpose agent combining planning and tools.
- `SWEAgent`: software-engineering agent using shell and file editing.

### Upstream tools in OpenManusWeb

| Tool | Capability |
|---|---|
| `bash` | Shell/process execution |
| `browser_use` | Browser navigation and page interaction |
| `create_chat_completion` | LLM chat completion |
| `file_saver` | Save generated files |
| `google_search` | Public web search |
| `planning` | Create/read/update execution plans |
| `python_execute` | Python computation |
| `run` | Dispatch a tool through the tool collection |
| `str_replace_editor` | Create/edit files through structured operations |
| `terminate` | End an agent run |

### MoreAI registered tool catalog (16 definitions)

| Tool key | Capability | Availability policy |
|---|---|---|
| `bash` | Isolated shell | Critical-risk; explicit approval and sandbox |
| `browser_use` | Approved-domain browser automation | High-risk; action approval and browser sandbox |
| `create_chat_completion` | Routed, metered LLM call | Entitlement / quota |
| `file_saver` | Private artifact creation | Owner-scoped storage and overwrite/share approval |
| `image_generate` | OpenAI image generation | Worker adapter + secret + entitlement + billing configuration |
| `video_generate` | Runway video generation | Worker adapter + secret + entitlement + billing configuration |
| `knowledge_ingest` | Tenant knowledge ingestion / embeddings | Owner-scoped knowledge write |
| `knowledge_search` | Semantic RAG retrieval | Owner-scoped knowledge read |
| `google_search` | Public web search | Approved search provider policy |
| `planning` | Durable plan and step updates | Run-scoped orchestration |
| `python_execute` | Isolated Python execution | Critical-risk; explicit approval and sandbox |
| `run` | Policy-controlled nested tool dispatch | Tool policy / quota / timeout |
| `workspace_restore_version` | Restore immutable workspace version | Approval + version fence |
| `workspace_read_file` | Read owner/member-scoped workspace file | Workspace authorization |
| `str_replace_editor` | Version-fenced workspace file edits | Approval for destructive/overwrite actions |
| `terminate` | Explicit run completion/failure | Current-run lifecycle |

Catalog presence is not execution permission. Actual Customer availability is determined by healthy worker capability snapshots, agent configuration, authorization, tool policy, approval, sandbox and provider/billing configuration. In the current Customer Agent Studio, registered runtime choices are Manus, Planning and ToolCall. SWE exists in the upstream source and is not represented as an enabled Customer runtime merely because the upstream class exists. Critical/high-risk tools remain gated.

## Next implementation slice within Phase 09

1. Add first-party EduTech persistence: learning paths, modules, lesson content versions, enrollments, study attempts, quiz items/responses, rubrics and assessment results.
2. Add Agent tool contracts for structured learning artifact creation, lesson retrieval, quiz generation and assessment recording, with user ownership and safe schemas.
3. Bind the generated learning artifacts to the existing durable Agent Run and workspace/artifact lifecycle.
4. Complete Customer API action inventory and remaining Customer dashboard contract gaps.
5. Keep payment, OTP/gateway, and other genuinely external provider adapters deferred as requested. They must not block internal EduTech learning.

Phase 09 remains IN PROGRESS. Phase 10 and Phase 11 are not accepted.
