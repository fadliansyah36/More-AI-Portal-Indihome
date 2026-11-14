# Phase 09 — First-party EduTech persistence and OpenManus tools

Date: 2026-11-14  
Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Baseline HEAD: `f5306792c41c2e12e89c0a300ec5244b280c5fd8`  
Scope: implement the first canonical MoreAI EduTech data domain and expose its lifecycle to the existing Customer dashboard and OpenManus Agent Runtime. This is a source implementation report, not runtime acceptance.

## Product and architecture decision

Implementation follows Master PRD v1.2 (11 November 2026), particularly the Phase 09 existing-frontend integration gate and Design System section 16: existing screens are the visual source of truth; white/light surfaces, MoreAI red, deep navy, cool-gray borders and subtle elevation remain authoritative. The UI changes below are additive and limited to missing persisted-data visibility; no global token or component-library migration was introduced.

EduTech is a first-party MoreAI capability for students and university students. It does not depend on an external EduTech catalogue provider. Existing Next.js Customer screens remain the product UI. The browser uses the existing typed FastAPI client; FastAPI and the worker access Supabase through the existing server-only repository/RPC boundaries.

## Implemented Supabase domain

Added migration `supabase/migrations/20261114080000_moreai_edutech_learning_domain.sql` and forward-only hardening migration `20261114081000_moreai_edutech_tool_idempotency.sql`; both were applied to canonical Supabase project `uunfgimtokhucegqbpce` (MoreAIdb). Supabase migration tool returned `success: true`.

New tables:
- `learning_paths`: owner, originating Agent Run, learning goal, level and lifecycle status.
- `learning_modules`: ordered curriculum modules.
- `learning_lessons`: ordered canonical lessons with Markdown content, objectives and content version.
- `learning_lesson_versions`: immutable prior lesson content versions.
- `learning_enrollments`: learner enrollment and lifecycle state.
- `learning_quizzes`: canonical quiz question sets and pass threshold.
- `learning_quiz_attempts`: submitted learner answers, score and feedback.
- `learning_assessments`: formative/rubric assessment records.
- `learning_progress`: canonical per-lesson progress with run linkage.
- `learning_run_artifacts`: Agent Run → learning resource references and safe summary payloads.

All ten tables have RLS enabled. Direct `anon` and `authenticated` table privileges are revoked; `service_role` receives the server-only table privileges. Tool RPCs are invoker functions, revoked from public/anon/authenticated and executable only by `service_role`. Each tool mutation checks that the supplied Agent Run belongs to the supplied user and that referenced learning resources are owner-scoped. No sample courses or learner activity were seeded.

## OpenManus tools

Added `apps/worker/app/learning_tools.py` and registered five tools in the canonical tool catalog and durable OpenManus tool runtime:
1. `learning_path_create` — create a path with ordered modules/lesson outlines and auto-enroll the owner.
2. `lesson_generate` — write/revise lesson content and preserve prior content versions.
3. `quiz_generate` — persist a quiz for a canonical lesson.
4. `answer_assess` — persist a quiz attempt, score, feedback and assessment.
5. `learning_progress_update` — update canonical lesson progress against the current owner-scoped Agent Run.

The tools are registered for Manus, Planning step execution (through the Manus step executor), and ToolCall. They use the existing worker Supabase RPC client and durable Agent Run identity; no separate learning engine or client-side database path was introduced.

## FastAPI and Customer UI integration

- Added owner-scoped FastAPI reads for learning paths, path/module/lesson detail, canonical progress and learning artifacts created by a given Agent Run. Learner-facing quiz projections omit answer keys, explanations and grading notes.
- Added typed Customer API contracts for the new routes.
- Updated the existing EduTech view to display saved learning paths, enrollment/progress summaries, modules and canonical lessons.
- Selecting a saved lesson hands its stored content and canonical IDs into the existing Chat → Planning Agent Run flow. Task detail also loads the learning artifacts associated with its Agent Run; EduTech progress counts use canonical lesson progress. Learner-facing quiz projections remove answer/answer_key/correct_answer/explanation/rationale/grading_notes/rubric fields before returning questions. The prompt explicitly instructs the agent to use the five persisted learning tools and never invent IDs or claim a write without a tool result.
- Existing Customer visual hierarchy, palette and component patterns were preserved; the UI change is additive and limited to displaying persisted curricula.

## Source changes

- `9be8d6b2b20b3bae3ee0038c0909139f31cac794` — add first-party EduTech migration file.
- `1184a8da508175fba5185abf26208c6745ef2882` — correct migration declaration block.
- `d6d57be71749341e0c55271b7139a4f6387dd4fa` — add worker learning tool adapters.
- `67a1ca69cc7af6a0e5eb6ed92eb2d1567006185a` — add catalog contracts.
- `14b806d911cf9600fa4494878dd95c7c774efd21` — expose tools through durable OpenManus runtime.
- `81947602ed0c4a37bdd085ef8bae858867bd4882` — register tools in worker agent factory.
- `e9f7bacc4f0753b378356b9a5281ec5fb325c10f` — add owner-scoped FastAPI learning reads and Agent Run artifact lookup.
- `eac7d3a73e786066e3ee73a9e8ed80d7ee7064e1` — add typed Customer API contracts.
- `4cdad90e947c11a18d183984da597c177de8d3a4` — surface saved curricula and resumable lessons.
- `d387581b664e7e634b6f746b84adf30847d09e13` — route EduTech prompts through persisted learning tools.
- `2e5bc04bfd26d3a4d5623190aae83e03ac470afd` — render saved curricula and lesson continuation in EduTech.
- `95b344000d770e6a677004e13da9685921044e78` — count canonical lesson progress.
- `4b8a89cdcccbd0e3ab348bd0c815a28c954672d2` / `2eff65742c5f998e8f22c8e12cc83a82b2a194c6` — display learning artifacts in Task detail and refresh them from Agent Run events.
- `b3300d82b8e16674022b17b7dc5adce6f147a5ad` — prevent learner curriculum reads from exposing quiz answer keys.

## UI change gate and visual preservation

- Protected baseline routes touched: Customer Dashboard → AI Content & EduTech; Customer Dashboard → Tasks & Workflow → Agent Run detail.
- Exact missing behaviors: the EduTech screen could start a learning session but could not display canonical saved learning paths/modules/lessons or resume a lesson; Task detail could display generic artifacts but not the learning artifacts created by its own Agent Run.
- Minimal changes: additive saved-curriculum and lesson-list section in the existing EduTech screen; additive learning-artifact section in the existing Task detail; no navigation shell, global CSS, Tailwind token, typography or component-library redesign. Existing MoreAI red/light-surface component styling was retained.
- Before/after browser screenshots and visual regression comparison were not captured because the owner explicitly prohibited real testing/browser checks. Therefore visual regression evidence is NOT VERIFIED.

## Security and integrity boundaries

- Customer-facing data reads filter by authenticated `user_id` / `owner_user_id`; path detail also scopes nested modules, lessons, quizzes and progress.
- Worker RPCs validate run ownership and learning-resource ownership before mutation.
- No direct browser Supabase PostgREST, Storage, RPC or Realtime access was added.
- Generated lesson/quiz/assessment content is AI-assisted learning material, not an accredited syllabus, official grade or certificate.
- Assessment scores and progress should only be persisted when supported by the actual learner response/session evidence; the model must not invent a completion event.
- Existing media/payment/OTP/gateway provider configuration remains deferred per product-owner instruction.

## Verification and deployment

- Supabase schema migration application: connector returned `success: true`.
- No SQL verification query, test query, unit/integration/E2E test, lint, typecheck, build, browser/API/worker runtime check, provider call, staging or deployment was run, per explicit product-owner instruction.
- Runtime behavior, worker deployment pickup, frontend rendering and data-flow acceptance remain **NOT VERIFIED**. The implementation is not represented as end-to-end tested or production-validated.
- No deployment was performed.

## Phase status and next work

Phase 09 remains **IN PROGRESS**. This increment closes the first-party EduTech schema/tool foundation and makes saved curriculum visible/resumable from the Customer UI. It does not close the entire Phase 09 Customer integration scope.

Next, in dependency order:
1. Extend EduTech with teacher/classroom/assignment and institutional governance only where the PRD requires them; keep minor/guardian consent and age-appropriate safety as a separate policy gate.
2. Complete the full Customer API action audit, reconcile every navigation action against typed FastAPI contracts and durable lifecycle, and close remaining workflow/task gaps.
3. Reconcile any remaining dashboard domains already backed by a real schema/API contract; leave payment, OTP/Gateway and external media configuration deferred.
4. Keep Phase 10 and Phase 11 blocked until the product owner authorizes the required verification/release gates. No phase advancement is claimed.
