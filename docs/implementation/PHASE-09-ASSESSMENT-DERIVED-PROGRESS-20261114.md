# Phase 09 — Assessment-derived progress and enrollment

Date: 2026-11-14  
Branch: main  
Baseline: 767d01f824c63d60d9b8d1238d96cb8e2eac7ca7

- Agent progress tool now accepts only in_progress; completion cannot be supplied by an Agent/model.
- Progress RPC rejects completed status and preserves already-completed progress against later in-progress updates.
- A lesson is completed only when every quiz attached to it has a persisted passing attempt.
- Enrollment is completed only when every lesson in the path has completed progress.
- Completion writes a progress artifact linked to the assessment Agent Run.
- EduTech session prompts now ask the Agent to record only actual session start and never claim completion.
- Fixed short-answer whitespace normalization in worker grading.

Policy limitation: lessons without quizzes remain incomplete; no unsupported completion shortcut was introduced. Project/essay rubric assessment and genuine content-activity completion need a separate first-party contract. No tests, build, lint, typecheck, SQL execution, migration application, browser/API/worker runtime, staging or deployment were run. Migration is committed but NOT applied or runtime-verified.
Next: EduTech → Agent Run → Tasks → Artifacts traceability, then reconcile no-quiz lesson activity. Phase 09 remains IN PROGRESS.
