# Phase 09 — Customer Auth Recovery & Vercel Build Recovery (2026-11-14)

## Scope
Continue Phase 09 on `main`: investigate the reported Supabase login failure, repair the source-level auth feedback path, correct the latest known frontend build blockers, and reconcile Vercel production deployment state. Existing UI layout and styling remain protected.

## Baseline and target
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main`
- Baseline HEAD before this increment: `eaa7ccb6b23544a6d42c6dc2208d750633828cca`
- Source commits:
  - `557c7ebe5c172b4a07dde14fc90b1bb59d363ebc` — align workspace version history with the existing API contract.
  - `fb4929ba75655ccf1ec0da2e819cbf6410e5b490` — make Supabase login errors actionable.
  - `c5eb19ab995617a6676a1e8142ca391030602d43` — remove a stale unsupported version-pagination action exposed by Vercel's next build.
- Current target HEAD at report time: `c5eb19ab995617a6676a1e8142ca391030602d43`.

## Auth investigation and changes
- Re-read `AGENTS.md`: browser Supabase access remains Auth-only; business data stays behind FastAPI; publishable key only in browser; no service-role key exposure.
- Vercel production environment metadata confirms the required variable names are configured: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, and `NEXT_PUBLIC_MOREAI_API_URL`. Values/secrets were not decrypted or printed.
- Read-only Supabase Auth logs show the Auth service is responding: successful password sign-up/login and refresh events exist, and a separate password-grant request returned `invalid_credentials` (HTTP 400). A recovery request was rate-limited once (HTTP 429, retry-after 56 seconds). This evidence does not support a general Supabase Auth outage or a frontend-to-wrong-project configuration issue.
- The login view previously collapsed nearly all Auth errors into “email/password salah”. It now distinguishes unconfirmed email, banned account, rate limits, invalid credentials and network/timeout errors, and surfaces the bounded Supabase error message for other failures.
- No password, user record, email confirmation flag, Auth user, or account metadata was changed. An `invalid_credentials` response means Supabase Auth did not accept the submitted email/password pair; a row in an application profile table alone cannot authenticate a user. The account owner must use the exact Auth email/password or complete a verified password recovery. No credential bypass was introduced.
- Existing recovery action remains rate-limited by Supabase's configured email-send policy when repeated too quickly; no rate limit or confirmation policy was weakened.

## Frontend build recovery
- Read the Vercel build logs for the latest prior frontend production deployment. First reported TypeScript error: `workspaceApi.versionsPage` did not exist; the client contract exposes `workspaceApi.versions`.
- Changed the workspace version-history screen to call the actual `versions` API contract and display its complete returned version collection.
- The next Vercel build surfaced a stale `loadMoreVersions` UI reference after pagination was removed; removed that obsolete control.
- No visual redesign, navigation change, token migration or unrelated UI edit was made.

## Vercel deployment state
- Frontend project: `more-ai-portal-indihome` (`prj_2ge37Xd5uBSUGhn3wPsaHfFcW1UV`).
  - Previous deployment at `0ba948c` failed on the `versionsPage` type error.
  - Deployment at `557c7ebe` failed on the stale `loadMoreVersions` reference.
  - Latest deployment for `c5eb19ab995617a6676a1e8142ca391030602d43` was observed as `QUEUED` at report time. It is not yet READY and has not been assigned as the verified live production build.
- API project: `more-ai-api` (`prj_L6i6j0ERPcdpZNM1c53hcdPaP9Nn`).
  - Deployment for `fb4929ba75655ccf1ec0da2e819cbf6410e5b490` reached `READY` in Vercel.
  - A newer deployment for `c5eb19ab995617a6676a1e8142ca391030602d43` was observed as `QUEUED`.
- These are Vercel Git-integration deployments triggered by pushes to `main`; no manual staging/preview deployment was requested or created in this increment.
- Production deployment cannot be declared complete while the frontend deployment is queued or failed. The controlling `AGENTS.md` also blocks production release until Phase 10 and Phase 11 gates are accepted. User's no-real-test/no-staging constraint means those release checks were not run.

## Supabase changes
- No schema migration, Auth configuration change, user mutation, password reset, email-confirmation change or RLS change was performed.
- Prior Phase 09 approval lifecycle migration remains applied as version `20261113182657`; no additional migration was needed here.

## Tests and verification
- Per user instruction: no tests, lint, typecheck, local build, browser checks, API calls, worker execution, staging or E2E tests were run.
- Read-only evidence used: GitHub source inspection, Vercel build logs/deployment metadata, Vercel environment-variable names only, and Supabase Auth log aggregation/details.
- The Vercel platform's own automatic build pipeline is part of its deployment lifecycle; its current frontend result remains queued at report time. This is not a substitute for Phase 10/11 acceptance.

## Phase status and blockers
- Phase 09 remains **IN PROGRESS**. Source changes improve auth diagnostics and remove known frontend type errors, but the customer-domain contracts still marked unavailable/gated in the acceptance matrix (real connector OAuth, Memory privacy lifecycle, payment settlement, partner OTP/gateway provider onboarding, manual retry/regenerate and other provider-backed contracts) cannot be fabricated without actual provider/API credentials/contracts. Runtime acceptance is intentionally unperformed.
- Phase 10 — End-to-End Integration Verification: **NOT STARTED / BLOCKED** by incomplete Phase 09 and the no-real-test constraint.
- Phase 11 — Integration Release Gate: **BLOCKED** until Phase 10 evidence and required CI/security/UI regression checks exist.
- Production deployment: frontend latest commit `c5eb19a` queued; API latest `c5eb19a` queued, prior API `fb4929b` READY. No verified complete frontend+API release at the current HEAD.

## Next phase
Continue Phase 09 source reconciliation and provider onboarding only where real contracts are available; then obtain explicit authorization for Phase 10 runtime verification. Phase 11 follows Phase 10 and is the mandatory production release gate.