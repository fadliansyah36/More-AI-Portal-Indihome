# Phase 09 — Server-authoritative EduTech quiz assessment

Date: 2026-11-14  
Branch: `main`  
Baseline: `ea252a9c73488915a3a4940e765cc3b3bf729b7b`

## Gap

The `answer_assess` OpenManus tool accepted a model/client supplied `score`, then persisted it as the learner's authoritative result. This allowed a caller to submit arbitrary scores unrelated to the persisted quiz answer key.

## Implemented

- The tool contract no longer accepts `score`, `feedback` or `rubric` from callers.
- Worker loads the quiz's persisted questions using an owner-scoped `learning_quizzes` query.
- Worker computes score from submitted `question_id` / `answer` values and stored `correct_answer` keys; unknown/duplicate question IDs, malformed values, unsupported subjective types and invalid scoring weights fail closed.
- Supported deterministic grading types: `single_choice`, `multiple_choice`, `true_false`, `short_answer`. Short answer is normalized for case and whitespace; multiple-choice arrays are normalized and compared as sets.
- Worker generates feedback and per-question rubric server-side, then calls the existing owner/run-checked Postgres RPC to persist attempt, assessment and run artifact.
- Quiz generation validates the machine-gradeable question contract before persistence. Existing API strips answer keys from learner-facing quiz payloads.

## Contract for generated questions

Each question must contain unique string `id`, `type`, and `correct_answer`; optional `points` defaults to 1 and must be positive. Question type is one of the four deterministic types above. Submission shape is `[{"question_id":"...","answer":...}]`. Subjective/free-form essay grading is intentionally rejected rather than assigning an unverified AI score.

## Constraints and security

The quiz read is scoped by both quiz ID and authenticated run owner ID. The client/model cannot provide the authoritative score or feedback. No schema change was needed; existing RPC persists the computed score and server-generated rubric. No tests, lint, typecheck, build, browser/API/worker execution, staging or deployment were run. Runtime behavior is NOT VERIFIED. UI screenshots were not captured because browser work was prohibited; no UI files changed.

## Next

Continue with activity-derived lesson progress/enrollment and then EduTech run/artifact/task traceability. Phase 09 remains IN PROGRESS.
