# Phase Tracker Addendum — Vercel Connectivity — 2026-11-12

This is an append-only operational addendum to `PHASE-TRACKER.md`; it does not change phase acceptance status.

- Vercel projects `more-ai-portal-indihome` (Next.js) and `more-ai-api` (FastAPI) both exist in the More AI team and both have a latest Production deployment in READY state.
- Both projects are Git-linked to `fadliansyah36/More-AI-Portal-Indihome` on `main`. Both active Production deployments now use commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6`. Web deployment `dpl_DbSaKgdd8UJbhKPxERMkL1VmcwaR` and API deployment `dpl_Hn8LSHR5Q6zxgEmy8u5Dn8NKT9Nw` are READY. `moreai.web.id` and `www.moreai.web.id` are listed as aliases on the active frontend deployment. `main` later advanced to `b980f413a1bc138b8dab466b81c32bbf38697baa` with documentation-only commits.
- `moreai.web.id` is verified and redirects to verified `www.moreai.web.id`. The frontend `NEXT_PUBLIC_MOREAI_API_URL` points to `https://more-ai-api-more-ai.vercel.app`.
- Corrected API project's `MOREAI_CORS_ALLOWED_ORIGINS` in Production/Preview/Development to include both custom web origins while preserving existing Vercel origins. The API deployment at SHA `500510bbb041dc235d3b7a832d3dc314a6d86fc6` was created after the environment update and is READY; live CORS preflight remains unverified.
- Git integration automatically queued/started production deployments for subsequent documentation-only commits. Six deployments across web/API for SHAs `9c7dd5792082044d8502129a2fb09b116c625b3a`, `b788e4286d42f0d677dd5a54b2ba9f5a68f8a391`, and `b980f413a1bc138b8dab466b81c32bbf38697baa` were canceled. The active READY deployments remain on the source-code commit `500510bbb041dc235d3b7a832d3dc314a6d86fc6`.
- API environment inventory has no `SUPABASE_SERVICE_ROLE_KEY`; `MOREAI_AGENT_EXECUTION_ENABLED=false`; no Vercel worker project/deployment was found. Do not activate worker or high-risk tools until the required secret and runtime/security gates are satisfied.
- No live HTTP, CORS preflight, /health, /ready, authenticated API, worker, browser, E2E, test or migration verification was run. Vercel did perform the production builds/deployments described above. READY means deployment status only, not end-to-end service acceptance.
- Phase 04, 06, 07, 08 and 09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.
- Full evidence: [VERCEL-FRONTEND-API-CONNECTIVITY-AUDIT-20261112.md](./VERCEL-FRONTEND-API-CONNECTIVITY-AUDIT-20261112.md).
- Next dependency: configure the API-only service-role secret in Vercel; provision the durable worker runtime; then, when testing is authorized, verify the current main commit in Preview before production release.
