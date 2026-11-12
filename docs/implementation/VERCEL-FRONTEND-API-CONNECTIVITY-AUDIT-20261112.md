# Vercel Frontend/API Connectivity Audit — 2026-11-12

## Scope and safety boundary

Read-only inspection of the More AI Vercel team, both production projects, deployment metadata, domain assignments, frontend/API environment variable names and non-secret values, Git linkage, and the repository's FastAPI CORS configuration. One corrective environment-variable update was made to the API project. No deployment, build, test, migration, database write, provider call, or worker activation was performed.

## Vercel projects and deployment state

| Service | Project | Framework | Latest production deployment |
|---|---|---|---|
| Customer/Partner/Super Admin web | `more-ai-portal-indihome` | Next.js | READY — `dpl_J1nsNjFZHdqQ7uzsWVPR5tFrwGb6` |
| API | `more-ai-api` | FastAPI | READY — `dpl_DshYnqYjojE4r26VTXoQBw7ebWiz` |

Both projects are in Vercel team `More AI` and link to GitHub `fadliansyah36/More-AI-Portal-Indihome`, branch `main`. The production deployments both use commit `cbcbda694206a0c2904b6a5626dc04feff292d07`. Web deployment region is `iad1`; API deployment region is `sin1`.

## Domain and API origin

- `moreai.web.id` is verified and redirects to `www.moreai.web.id` with HTTP 308.
- `www.moreai.web.id` is verified and assigned to the Next.js project.
- API project has verified Vercel aliases including `more-ai-api-more-ai.vercel.app`.
- Frontend Production/Preview/Development has `NEXT_PUBLIC_MOREAI_API_URL=https://more-ai-api-more-ai.vercel.app`.
- Frontend API client uses this base URL for shared FastAPI calls; optional Customer and Partner origins fall back to the same API origin. Customer/Partner separation remains enforced through server-side route namespaces.
- FastAPI CORS middleware uses the exact `MOREAI_CORS_ALLOWED_ORIGINS` allowlist and permits Authorization, Content-Type, Accept, Idempotency-Key and X-Correlation-ID.

## Corrective configuration change

The API CORS allowlist originally omitted the production custom web origin. Updated Vercel project `more-ai-api`, variable `MOREAI_CORS_ALLOWED_ORIGINS` (ID `DXhmORrCOxF1TDBa`) for Production, Preview and Development to include:
- `https://moreai.web.id`
- `https://www.moreai.web.id`

Existing Vercel preview origins were preserved. The Vercel API confirmed the updated value. This environment change is **not retroactive**: the currently active API deployment must be redeployed before this updated CORS value is loaded by a running function.

## Remaining connection blockers

1. API project environment inventory does not contain `SUPABASE_SERVICE_ROLE_KEY`. The API `/ready` implementation requires server-side data credentials and will report degraded readiness when they are absent. Do not place this key in the web project or any `NEXT_PUBLIC_*` variable. Configure it only as an encrypted/sensitive server-side environment variable in the API project.
2. `MOREAI_AGENT_EXECUTION_ENABLED=false` in the API project's configured environments. Agent execution is intentionally disabled.
3. There is no separate Vercel project/deployment for `apps/worker`. The repository packages the durable worker separately as a long-running container profile; a READY FastAPI deployment does not prove the worker is deployed or consuming runs.
4. The active production deployments are behind GitHub `main`: deployed commit `cbcbda694206a0c2904b6a5626dc04feff292d07` was 18 commits behind main `36b936a39ee6506b4dc05e77f45f5360c67527a1` at comparison time. Two documentation commits subsequently advanced main to `13a51a8517304cbea90f007ac4811b923b1c314c`.
5. Git integration automatically queued/build-started Production deployments after the documentation commits. To honor the Phase 11 release gate, both were canceled before becoming READY: web `dpl_3oRoPtoeJ3x75whAphUvjzx4gctK`; API `dpl_9cpapMM357744Dy3oKEVkMRDBofB`. Existing production aliases were not promoted to these canceled builds.
6. No live HTTP, authenticated API, CORS preflight, /health, /ready, browser, worker, or end-to-end test was run. Deployment state READY is a Vercel build/deployment status, not proof of application-level service connectivity.

## Conclusion

**Frontend-to-API configuration exists, but the production service chain is not yet fully operationally connected/accepted.** The frontend has a FastAPI base URL and both projects are Git-linked and READY. The custom-domain CORS omission has been corrected in Vercel configuration for the next deployment. However, current production code has not consumed that new setting, API server-side Supabase credentials are missing, agent execution is disabled, the worker has no deployed runtime evidence, and production is behind current main.

## Next authorized sequence

1. Add `SUPABASE_SERVICE_ROLE_KEY` directly in Vercel API project's encrypted Production/Preview/Development settings; never share it in chat or add it to the frontend.
2. Provision the durable worker as a protected long-running service using the repository's worker container profile and its server-only secrets; keep sandbox/browser tools disabled until their isolation gates pass.
3. After testing authorization, deploy the current reviewed main SHA to Preview first; verify CORS preflight, `/health`, `/ready`, Supabase Auth/data access, authenticated API routes, worker claim/heartbeat/recovery and browser-to-API integration.
4. Only after Phase 10 evidence passes, perform the Phase 11 release gate and production promotion.
