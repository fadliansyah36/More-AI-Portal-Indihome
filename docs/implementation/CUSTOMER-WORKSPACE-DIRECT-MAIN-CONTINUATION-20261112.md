# Customer Workspace Direct-main Continuation — 2026-11-12

## Scope
- Direct target: `main`
- Product surface: existing MoreAI Customer Workspace only.
- Backend path: Customer frontend → FastAPI → OpenManus Engine / durable Worker → Supabase.
- No staging environment was created.
- No real endpoint, browser, provider, worker, SQL, migration, lint, build, or E2E test was run in this continuation.

## Repository and deployment reconciliation
- Repository HEAD inspected: `e309fd093cde6e34b98a69d235098f6cebada833`.
- FastAPI project: Vercel `more-ai-api`, project `prj_L6i6j0ERPcdpZNM1c53hcdPaP9Nn`.
- Production deployment created directly from `main` HEAD above:
  - Deployment: `dpl_5fpYzDFuqcB9Xzt4nNnj2UhHHykk`
  - URL: `https://more-ai-nvagc4ikl-more-ai.vercel.app`
  - Alias: `https://more-ai-api.vercel.app`
  - State: `READY`
  - Framework/root: FastAPI / `apps/api`; source outside root enabled.
- The deployment state is build/deployment evidence only. No runtime endpoint was invoked and no API health or Customer flow is claimed as verified.
- Frontend Vercel project `more-ai-portal-indihome` is linked to the same repository. A direct production deployment request for current HEAD was rejected by Vercel with HTTP 402 `api-deployments-free-per-day` (retry after 86400 seconds). The frontend production deployment therefore remains on an earlier commit until Vercel permits another deployment.
- Existing frontend environment contains `NEXT_PUBLIC_MOREAI_API_URL=https://more-ai-api-more-ai.vercel.app`, covering Production/Preview/Development.
- API environment inventory includes canonical `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `MOREAI_CORS_ALLOWED_ORIGINS`, and `MOREAI_AGENT_EXECUTION_ENABLED=false`. The service-role variable is configured as a sensitive environment entry; its value was not retrieved or exposed.

## Runtime blockers and safe gates
1. `MOREAI_AGENT_EXECUTION_ENABLED=false` remains intentionally disabled. Do not enable it until a durable worker is deployed and healthy, provider routing/secrets are configured, and credit/entitlement/quota/wallet policy is approved.
2. The repository has a Docker worker image and `docker-compose.runtime.yml` profile, but this inspection found no connected deployed worker service in the current Vercel project inventory. Vercel's FastAPI deployment is not a substitute for a continuously running durable worker.
3. Worker runtime requires server-only Supabase credentials, WORKER_ID, runtime enablement, credit conversion, wallet currency, entitlement/quota keys and enabled DB provider/model routing. No such worker runtime configuration was provisioned in this continuation.
4. Vercel frontend production deployment is blocked by the account's daily deployment quota. Do not change billing/security settings automatically.
5. API build state READY is not proof that `/health`, `/ready`, authenticated Supabase operations, SSE, or a worker run work. Those checks were deliberately not performed per owner instruction.

## Current source integration baseline
- Typed API client includes authenticated Customer conversations, durable run creation/list/detail/cancel, SSE stream, run steps, wallet/ledger/usage/entitlement/quota, artifacts, workspaces and Knowledge Library contracts.
- Customer Chat submits durable run requests and consumes persisted SSE events.
- Tasks / Workflow screens read persisted agent runs and approval decisions.
- Files / Knowledge screens have owner-scoped backend contracts and typed clients.
- The integration is still partial: screen-by-screen coverage, OpenManus upstream behavior parity, deployed worker execution, provider configuration, and the frontend production deployment lag remain open.
- Customer business data continues to flow through FastAPI; browser Supabase use remains Auth-only.

## Next implementation order
1. Restore frontend production deployment availability, then deploy the current main commit directly to production (no staging).
2. Provision and configure the durable Worker on an always-on container host using the repository's worker Dockerfile; configure required secrets and policy values in that host's secret manager.
3. Complete Phase 04: remaining OpenManus server/session/Flow and dispatcher parity; keep unsupported isolated tools fail-closed.
4. Complete Phase 07: durable event/outbox failure recovery, cancellation, timeout, lease fencing and worker restart behavior.
5. Complete Phase 08: provider/model routing, full supported tool/agent behavior, memory/RAG ingestion and citation provenance, accounting.
6. Complete Phase 06 and Phase 09 Customer API/client/screen coverage without changing protected UI/UX.
7. Only after owner authorization, run Phase 10 E2E and Phase 11 release gates.

## Acceptance status
- Phase 04: IN PROGRESS
- Phase 06: IN PROGRESS
- Phase 07: IN PROGRESS
- Phase 08: IN PROGRESS
- Phase 09: IN PROGRESS
- Phase 10: NOT ACCEPTED (no real E2E)
- Phase 11: BLOCKED

No claim of full integration or production runtime acceptance is made.
