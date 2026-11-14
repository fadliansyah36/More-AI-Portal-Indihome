# Phase 09 — Canonical EduTech Lesson Reader

Date: 2026-11-14  
Branch: `main`

## Baseline and missing behavior

The existing `components/views/edutech-lesson-view.tsx` rendered a static "Menunggu katalog resmi" placeholder and did not read the first-party learning domain, even though the EduTech dashboard already exposed owner-scoped saved path and lesson data through FastAPI.

## Implemented

Replaced the static placeholder with a read-only canonical lesson reader:
- requires the canonical `pathId` and `lessonId` from the caller (no fabricated identifiers);
- loads the owner-scoped path detail through the existing typed `learningApi.path` FastAPI client;
- resolves the lesson only within the returned path and displays stored title, module, version, objectives, Markdown source text, progress and saved quiz summaries;
- renders explicit loading, API failure, missing lesson and empty-content states;
- never writes learner progress merely by opening a lesson and never fabricates lesson content or quiz attempts.

## UI change gate

Protected baseline surface: existing EduTech Lesson screen. The exact missing behavior was that the screen had no connection to the canonical first-party lesson store and always displayed a static catalogue placeholder. The smallest required change replaces that placeholder with persisted lesson content and truthful loading/error/empty states, retaining the existing card hierarchy, MoreAI red/light palette, typography scale, spacing conventions and back action. No navigation shell or global design tokens were changed. No before/after screenshots were captured because the owner prohibited browser/testing work.

## Constraints

Direct source change on `main`. No tests, lint, typecheck, build, browser/API/worker execution, staging or deployment. The component now requires its caller to pass real canonical `pathId` and `lessonId`; the current repository has no active call site for this view, so navigation wiring remains a separate integration item. Runtime behavior is NOT VERIFIED.
