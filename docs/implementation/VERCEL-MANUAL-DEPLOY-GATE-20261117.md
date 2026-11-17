# Vercel Manual Deployment Gate — 2026-11-17

## Product-owner instruction
Production and preview deployments must not be published automatically from routine pushes. A Vercel deployment may be initiated only after an explicit product-owner instruction to deploy.

## Projects updated
Team: `more-ai` (`team_wHMjZ5NapyaF8aYYVs4UUY36`)

- Frontend: `more-ai-portal-indihome` (`prj_2ge37Xd5uBSUGhn3wPsaHfFcW1UV`)
- FastAPI: `more-ai-api` (`prj_L6i6j0ERPcdpZNM1c53hcdPaP9Nn`)

## Configuration
Both projects' Vercel Ignored Build Step (`commandForIgnoringBuildStep`) was set to:

```sh
case "$VERCEL_GIT_COMMIT_MESSAGE" in *"[MOREAI-DEPLOY-APPROVED]"*) exit 1 ;; *) exit 0 ;; esac
```

Vercel semantics: exit code 0 ignores/skips the deployment build; exit code 1 continues the build. Routine commit messages therefore skip Git-triggered deployments. A deployment trigger commit must include the exact marker `[MOREAI-DEPLOY-APPROVED]`, and the marker is to be added only after the product owner explicitly asks to deploy.

## Operational procedure
1. Continue implementation on `main`; routine commits do not include the approval marker.
2. Do not run staging or real-world tests unless separately authorized.
3. When the product owner explicitly says to deploy, first confirm the target project(s), then create a deliberate release-trigger commit containing the marker and track the resulting Vercel deployment.
4. Never add the marker to ordinary implementation commits or automated documentation commits.

## Evidence and limitations
- Vercel `update_project` returned success for both project IDs and updated their project timestamps.
- A subsequent `get_project` readback confirmed both project identities, domains and existing latest Production deployment IDs remained present. The readback endpoint does not expose `commandForIgnoringBuildStep`, so the exact setting value is not independently echoed by that endpoint.
- The attempted Vercel Deployment Policy route was unavailable on the current Hobby plan (`403 pro_plan_required`); this Ignored Build Step mechanism was used instead.
- No deployment was manually created or promoted by this change.
- No build, lint, typecheck, tests, browser/API/worker checks, staging, migration, or provider calls were run.

## Current status
Manual-deployment guard configuration submitted successfully for both projects; exact setting readback is not exposed by the available project-detail response. Treat this as configured based on successful update response, but not as an independently verified end-to-end deployment gate until Vercel exposes the setting or an authorized future deployment confirms it.
