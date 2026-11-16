# Phase 09 — Vercel and Customer frontend integration reconciliation

Date: 2026-11-16  
Branch: `main`  
Repository head after source correction: `446f479613ad5889d53276863a7cbf1ffe468fcc`

## Vercel project mapping (read-only)

The already-connected Vercel More AI account exposes two Git-linked production projects for `fadliansyah36/More-AI-Portal-Indihome`:

| Project | Vercel project ID | Framework | Latest deployment observed |
|---|---|---|---|
| `more-ai-api` | `prj_L6i6j0ERPcdpZNM1c53hcdPaP9Nn` | FastAPI | READY, commit `ed8a8b2305a6d5b3cb4be771361feb93c186b8ac` |
| `more-ai-portal-indihome` | `prj_2ge37Xd5uBSUGhn3wPsaHfFcW1UV` | Next.js | ERROR, commit `ed8a8b2305a6d5b3cb4be771361feb93c186b8ac` |

The frontend project's configured `NEXT_PUBLIC_MOREAI_API_URL` is `https://more-ai-api.vercel.app`, pointing to the canonical FastAPI service alias. The API environment includes the Supabase project URL and existing server variables. Only environment variable names/metadata were inspected; no secret values were decrypted or read.

## Exact frontend build failure and source correction

Vercel's existing production build log for deployment `dpl_6Rfyo76GNvtQ82CMdLuuVSu5Un5Z` reports:
- `next build` compiled application code successfully, then TypeScript validation failed.
- Error path: `apps/sandbox/openfuse-overrides/index.ts:2`.
- Error: `Cannot find module './server.ts' or its corresponding type declarations.`
- The repository root `tsconfig.json` previously included every `**/*.ts` file and excluded only `node_modules`. OpenFuse override source is copied into the pinned OpenFuse Docker build, where upstream `server.ts` exists, and is not part of the Next.js frontend TypeScript project.

Source correction:
- Commit `446f479613ad5889d53276863a7cbf1ffe468fcc` adds `apps/sandbox/openfuse-overrides/**/*.ts` to the root TypeScript `exclude` list.
- This keeps the infrastructure worker source in its existing location for Docker image assembly and prevents Next.js from treating the worker entrypoint as a product frontend module.
- No Customer page, CSS, component style or navigation was modified by this correction.
- No build/test was rerun after the correction, per the explicit no-testing instruction. The source correction is therefore not yet a verified deployment fix.

## FastAPI deployment and source lag

The latest API deployment observed is READY at commit `ed8a8b2305a6d5b3cb4be771361feb93c186b8ac`. It predates the latest main source head `446f479613ad5889d53276863a7cbf1ffe468fcc`; deployment readiness only confirms Vercel completed the API build/deploy for its own commit and does not confirm runtime integration, worker readiness or active Skills ingestion.

## Missing server-side source credential

The API project's read-only environment-variable inventory does not contain `MOREAI_GITHUB_TOKEN`. The application source supports it through FastAPI `Settings.from_env()`, and `docker-compose.runtime.yml` forwards it as a server-only variable. The actual GitHub read token was not supplied in this execution context and cannot be derived from the GitHub repository connector. Do not invent one or place it in source. An authorized operator must add it as an encrypted/sensitive production environment variable on the `more-ai-api` project and redeploy the API through the approved production process. Preview/development scope is not required for the production customer skill ingestion path.

The read-only Vercel API environment inventory also showed `MOREAI_AGENT_EXECUTION_ENABLED=false`. This remains intentionally disabled while real providers, model pricing, wallet conversion, quota/entitlement policy and the always-on worker are unprovisioned.

## Current canonical Supabase readiness (read-only)

At the latest verified snapshot:
- `moreai_skill_packages`: 0
- `moreai_skill_source_files`: 0
- `llm_providers`: 0
- `llm_models`: 0
- fresh worker capability snapshots within 90 seconds: 0
- active/unexpired browser sessions: 0
- unexpired browser capacity leases: 0

No Supabase data or schema changes were made in this continuation.

## Operations not performed

- No OpenFuse/ClamAV host provisioning, Docker execution, network creation, secret injection or encrypted volume creation.
- No `MOREAI_GITHUB_TOKEN` environment variable was created because no actual token value was provided.
- No Motion, Visual or Scenario package was imported or ingested; no Customer session/access token was available.
- No provider/model/secret/pricing/credit/quota/entitlement/wallet policy or always-on worker was created.
- No manual Vercel deployment, promotion, rollback, staging, test, build, lint, typecheck, browser/API/worker test or runtime request was performed in this continuation. The deployment log above is read-only evidence from the existing Git-linked Vercel deployment, not a test executed by this session.
- No screenshots were captured; no protected UI surface was changed.

## Phase and release status

Phase 09 remains **IN PROGRESS**. The Vercel frontend source-level TypeScript inclusion issue has a committed correction but no post-correction deployment evidence. The API deployment is behind the latest repository head. Phase 10 remains **NOT ACCEPTED** and Phase 11 remains **BLOCKED**.

## Next operational requirements

1. Add `MOREAI_GITHUB_TOKEN` to the `more-ai-api` production secret manager as an encrypted value, then deploy the API only through the owner's approved production release process.
2. Execute the OpenFuse/ClamAV provisioning script on an authorized LUKS-backed Docker host with immutable Playwright and ClamAV digests, exact domain allowlist and strong service/proxy tokens. Attach the persistent MoreAI worker through the private network overlay.
3. Run Motion, then Visual + Scenario batch ingestion from an authenticated Customer session; complete dependency/SBOM, license/NOTICE and asset-rights human review.
4. Provision real providers and model prices, wallet conversion, quota and entitlements, then deploy the always-on worker and establish fresh heartbeat.
5. Only after the operational gates are met, complete Customer end-to-end and security acceptance; do not declare Phase 09 complete based on source or Vercel build status alone.
