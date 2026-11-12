# Phase 09 — Customer EduTech Content Truthfulness (2026-11-13)

## Scope
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main`
- Keep the existing EduTech screens and persisted learning-progress API.
- Remove unverified ratings, partner affiliation claims and non-functional video action.

## Implemented
- Removed static star ratings and review counts from the EduTech module list and lesson detail. No review/rating API exists in the current learning router.
- Replaced the unverified "EduTech Global Partner" / "Modul EduTech Partner Network" labels with neutral MoreAI learning-material wording.
- Replaced the clickable "Mulai Belajar Sekarang" action (which only displayed an unavailable toast) with an explicit inline statement that video delivery is unavailable.
- Retained the existing curated text syllabus and the authenticated `learningApi.progress()` / `learningApi.setProgress()` persistence behavior.
- No layout redesign or new backend contract was introduced.

## Files changed
- `components/views/edutech-view.tsx`
- `components/views/edutech-lesson-view.tsx`

## Commits
- `b3e629badec6f2a98589283c65b01e8620cccf89` — remove unverified EduTech partner and review claims.
- `aa3b8ac0088b1d4f50c8616ecfe8b78d880089ef` — remove unverified EduTech ratings and video action.

## Restrictions and verification
- Source changes only; no tests, lint, typecheck, build, browser/API probes, screenshots, staging, deployment, provider calls or Supabase live mutations were performed.
- The local syllabus remains curated static text, not a remotely managed course catalog. Video/content delivery and verified course metadata require a real backend content/catalog contract.
- This increment does not mark Phase 09 complete.
