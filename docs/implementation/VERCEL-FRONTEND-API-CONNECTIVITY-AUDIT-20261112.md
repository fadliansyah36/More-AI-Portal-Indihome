# Vercel Frontend/API Connectivity Audit — 2026-11-12

## Scope and safety boundary

Read-only inspection of the More AI Vercel team, both production projects, deployment metadata, domain assignments, frontend/API environment variable names and non-secret values, Git linkage, and the repository's FastAPI CORS configuration. One corrective environment-variable update was made to the API project. Git integration subsequently deployed the source commit containing the SSE reconnect implementation to both Production projects. No tests, migration, database write, provider call, or worker activation was performed.

## Vercel projects and deployment state

| Service | Project | Framework | Latest production deployment |
|---|---|---|---|
| Customer/Partner/Super Admin web | `more-ai-portal-indihome` | Next.js | READY — `dpl_DbSaKgdd8UJbhKPxERMkL1VmcwaR` |
| API | `more-ai-api` | FastAPI | READY — `dpl_Hn8LSHR5Q6zxgEmy8u5Dn8NKT9Nw` |

Both projects are in Vercel team `More AI` and link to GitHub `fadliansyah36/More-AI-Portal-Indihome`, branch `main`. Both current production deployments use commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6` (`feat: reconnect durable SSE streams from last event cursor`). Web deployment region is `iad1`; API deployment region is `sin1`. The frontend production deployment explicitly lists aliases `moreai.web.id` and `www.moreai.web.id`; the API deployment lists `more-ai-api-more-ai.vercel.app`.

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

Existing Vercel preview origins were preserved. The Vercel API confirmed the updated value. This environment change was subsequently consumed by the API Production deployment at commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6` (deployment `dpl_Hn8LSHR5Q6zxgEmy8u5Dn8NKT9Nw`, READY). No live CORS preflight was executed, so browser acceptance is still unverified.

## Remaining connection blockers

1. API project environment inventory does not contain `SUPABASE_SERVICE_ROLE_KEY`. The API `/ready` implementation requires server-side data credentials and will report degraded readiness when they are absent. Do not place this key in the web project or any `NEXT_PUBLIC_*` variable. Configure it only as an encrypted/sensitive server-side environment variable in the API project.
2. `MOREAI_AGENT_EXECUTION_ENABLED=false` in the API project's configured environments. Agent execution is intentionally disabled.
3. There is no separate Vercel project/deployment for `apps/worker`. The repository packages the durable worker separately as a long-running container profile; a READY FastAPI deployment does not prove the worker is deployed or consuming runs.
4. Production now runs the source commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6`. `main` subsequently advanced with documentation-only commits to `b980f413a1bc138b8dab466b81c32bbf38697baa`; those commits do not contain further application code changes.
5. Git integration automatically queued Production deployments for the later documentation-only commits. To avoid releasing documentation-only revisions outside the gate, the six queued/building deployments for SHAs `9c7dd5792082044d8502129a2fb09b116c625b3a`, `b788e4286d42f0d677dd5a54b2ba9f5a68f8a391`, and `b980f413a1bc138b8dab466b81c32bbf38697baa` were canceled across web/API. The two READY deployments at SHA `500510bbb041dc235d3b7a832d3dc314a6d86fc6` remain the active code deployments.
6. No live HTTP, authenticated API, CORS preflight, /health, /ready, browser, worker, or end-to-end test was run. Deployment state READY is a Vercel build/deployment status, not proof of application-level service connectivity.

## Conclusion

**Frontend-to-API configuration exists, but the production service chain is not yet fully operationally connected/accepted.** The frontend has a FastAPI base URL and both projects are Git-linked and READY. The custom-domain CORS omission has been corrected in Vercel configuration and the API deployment at commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6` is READY. However, no live preflight/readiness/authenticated request was executed; API server-side Supabase credentials are missing, agent execution is disabled, and the worker has no deployed runtime evidence. Current production application code includes the latest source change, while `main` has since advanced only with documentation updates.

## Next authorized sequence

1. Add `SUPABASE_SERVICE_ROLE_KEY` directly in Vercel API project's encrypted Production/Preview/Development settings; never share it in chat or add it to the frontend.
2. Provision the durable worker as a protected long-running service using the repository's worker container profile and its server-only secrets; keep sandbox/browser tools disabled until their isolation gates pass.
3. After testing authorization, deploy the current reviewed main SHA to Preview first; verify CORS preflight, `/health`, `/ready`, Supabase Auth/data access, authenticated API routes, worker claim/heartbeat/recovery and browser-to-API integration.
4. Only after Phase 10 evidence passes, perform the Phase 11 release gate and production promotion.
