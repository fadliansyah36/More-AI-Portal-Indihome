# Phase 09 — EduTech Lesson Reader Dashboard Wiring

Date: 2026-11-14  
Branch: `main`

## Baseline and gap

Baseline HEAD: `9297ba2ddee478305aca919b3ab212ebfa249732`. The canonical lesson reader existed but had no active caller from the Customer EduTech view. The saved curriculum list exposed a "Lanjutkan" action that started an Agent Run, but did not provide a direct read-only route to the persisted lesson content.

## Implemented

- Connected the existing `EdutechView` saved path/module/lesson selection to `EdutechLessonView`.
- Added a compact "Baca materi" action beside the existing "Lanjutkan" action. The original AI tutor/Planning Agent Run path remains unchanged.
- Passes only canonical `path.id` and `lesson.id` selected from the owner-scoped FastAPI path detail response.
- Embeds the canonical reader inside the selected curriculum panel; closing the path also clears the selected lesson.
- Removed an unused navigation callback from the lesson reader component contract.
- Lesson reader fetches canonical detail through typed `learningApi.path`; it renders stored content/objectives/progress/quiz summaries and explicit loading/error/missing/empty states. Opening the reader does not mutate progress.

## UI change gate

Protected baseline: Customer Dashboard → AI Content & EduTech → Kurikulum tersimpan. Exact missing behavior: the persisted lesson reader was not reachable from the selected curriculum. Minimal UI change: one compact "Baca materi" action and an embedded reader within the existing curriculum card. Existing "Lanjutkan" AI Agent behavior and history controls remain unchanged. Existing MoreAI light surfaces, red action color, navy text, spacing and component hierarchy are retained. No screenshots or browser comparison were captured because the owner prohibited real testing/browser work.

## Constraints

No tests, lint, typecheck, build, browser/API/worker runtime verification, staging or deployment. Source linkage and committed files were inspected in GitHub only. Runtime behavior remains NOT VERIFIED.
