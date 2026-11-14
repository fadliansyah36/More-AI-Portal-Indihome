# Skill Intelligence Platform — Source Implementation Report

Date: 2026-11-14  
Branch: `main`  
Status: **PARTIAL — registry/API/customer UI foundation committed; runtime execution integration and source ingestion are intentionally not enabled.**

## Implemented in this increment

- Added server-only Supabase tables for immutable skill provenance and per-user installation records:
  - `moreai_skill_packages`
  - `moreai_skill_installs`
- Enabled RLS and explicit deny policies for `anon` and `authenticated`; direct browser table access is revoked. Server-side service role is the only database path.
- Added FastAPI customer endpoints:
  - `GET /api/v1/customer/skills`
  - `POST /api/v1/customer/skills` — register provenance metadata only; does not fetch or execute source files.
  - `POST /api/v1/customer/skills/{id}/validate` — metadata-only validation.
  - `POST /api/v1/customer/skills/{id}/install` — only published and validated packages; execution remains false.
  - `POST /api/v1/customer/skills/{id}/permissions` — creates a pending permission request; never grants permission.
- Added privileged platform review endpoints:
  - `GET /api/v1/admin/skills/pending`
  - `PATCH /api/v1/admin/skills/{id}/review` — separate license and publication review.
  - `PATCH /api/v1/admin/skills/{id}/permissions` — allowlisted permission grant review; execution remains disabled.
- Added typed API client and customer AI Skills Library view, registered in existing customer navigation. Existing CSS/Tailwind conventions, typography, red action treatment and card patterns are retained.

## Security and lifecycle rules

- Source provenance requires repository/ref/40-char commit/path/40-char Git blob SHA/64-char SHA-256.
- Import is metadata-only. The API does not trust a caller-provided hash as proof that remote bytes match it.
- Skills remain untrusted. No code, scripts, dependencies or assets are executed by this feature.
- Validation does not claim malware scanning, nested-file review, dependency/SBOM verification, license clearance or sandbox compatibility.
- License approval and publication require a privileged reviewer permission: `skills.registry.review`.
- Execution permission requests are separate from install. Granted permissions must be a subset of the declared request and are constrained to an allowlist.
- Even approved permissions do not activate execution. The API explicitly returns `execution_enabled: false` until a worker-side OpenManus resolver and execution enforcement are implemented and reviewed.
- OpenManus remains the only Agent Runtime. No OpenFuse runtime or separate database is introduced.

## Files committed

- `supabase/migrations/20261114100000_moreai_skill_intelligence_registry.sql`
- `supabase/migrations/20261114101000_moreai_skill_permission_grants.sql`
- `apps/api/app/routers/skills.py`
- `apps/api/app/routers/admin.py`
- `apps/api/app/main.py`
- `lib/api/client.ts`
- `types/moreai.ts`
- `components/views/skills-library-view.tsx`
- `components/navigation/app-navbar.tsx`
- `app/page.tsx`

## Explicitly not complete

1. Secure pinned-source fetcher and nested-file/asset ingestion with redirect/DNS/size/path/symlink defenses.
2. Actual content hash verification against fetched bytes and Git blob object calculation.
3. Recursive Scenario Skills manifest/reference/license/NOTICE/asset/dependency scan and exact-version SBOM reconciliation.
4. Reviewer UI and permission catalogue administration.
5. Worker-side Skill Resolver that loads only published immutable skill versions and approved grants for a specific user/workspace/run.
6. OpenManus tool-context integration, run-level skill version/hash snapshots and durable audit events.
7. Skill sandbox policy enforcement for network, filesystem, data classes, timeouts and resource limits.
8. Connections Center (Google OAuth/Gmail/Calendar) and customer dashboard follow-on integrations.

## Operational restrictions honored

No tests, lint, typecheck, build, browser/API/worker runtime probes, external provider calls, staging, deployment or Supabase mutation were performed. Migration files are committed but **not applied**. No runtime acceptance is claimed.

## Next implementation phase

**Skill Intelligence Platform — Source Ingestion & OpenManus Runtime Resolver.** Complete the immutable source fetch/verification and nested-file manifest first; then implement worker-side per-run resolution and permission enforcement before enabling any skill execution. After that, implement Connections Center (OAuth/Gmail/Calendar) through the existing FastAPI and Supabase boundary, then continue customer dashboard gaps.
