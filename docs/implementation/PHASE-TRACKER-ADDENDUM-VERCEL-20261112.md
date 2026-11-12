# Phase Tracker Addendum — Vercel Connectivity — 2026-11-12

This is an append-only operational addendum to `PHASE-TRACKER.md`; it does not change phase acceptance status.

- Vercel projects `more-ai-portal-indihome` (Next.js) and `more-ai-api` (FastAPI) both exist in the More AI team and both have a latest Production deployment in READY state.
- Both projects are Git-linked to `fadliansyah36/More-AI-Portal-Indihome` on `main`. The deployed commit is `cbcbda694206a0c2904b6a5626dc04feff292d07`; current main was `36b936a39ee6506b4dc05e77f45f5360c67527a1` before the two audit-doc commits. Main is now `13a51a8517304cbea90f007ac4811b923b1c314c`; production remains behind.
- `moreai.web.id` is verified and redirects to verified `www.moreai.web.id`. The frontend `NEXT_PUBLIC_MOREAI_API_URL` points to `https://more-ai-api-more-ai.vercel.app`.
- Corrected API project's `MOREAI_CORS_ALLOWED_ORIGINS` in Production/Preview/Development to include both custom web origins while preserving existing Vercel origins. This takes effect only on a subsequent deployment.
- Git integration automatically queued/started production deployments for the docs-only commits. In accordance with the Phase 11 release gate, both deployments were canceled before READY: web `dpl_3oRoPtoeJ3x75whAphUvjzx4gctK`, API `dpl_9cpapMM357744Dy3oKEVkMRDBofB`.
- API environment inventory has no `SUPABASE_SERVICE_ROLE_KEY`; `MOREAI_AGENT_EXECUTION_ENABLED=false`; no Vercel worker project/deployment was found. Do not activate worker or high-risk tools until the required secret and runtime/security gates are satisfied.
- No live HTTP, CORS preflight, /health, /ready, authenticated API, worker, browser, E2E, build, test, migration or deployment verification was run. READY means Vercel deployment status only, not end-to-end service acceptance.
- Phase 04, 06, 07, 08 and 09 remain IN PROGRESS; Phase 10 BLOCKED; Phase 11 NOT STARTED.
- Full evidence: [VERCEL-FRONTEND-API-CONNECTIVITY-AUDIT-20261112.md](./VERCEL-FRONTEND-API-CONNECTIVITY-AUDIT-20261112.md).
- Next dependency: configure the API-only service-role secret in Vercel; provision the durable worker runtime; then, when testing is authorized, verify the current main commit in Preview before production release.
