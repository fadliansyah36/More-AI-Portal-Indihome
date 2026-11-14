# Skill Source Ingestion & OpenManus Resolver — Implementation Increment

Date: 2026-11-14  
Branch: `main`  
Status: **SOURCE IMPLEMENTATION COMMITTED — NOT RUNTIME ACCEPTED**

## Implemented

### Pinned source ingestion
- Added `POST /api/v1/customer/skills/{skill_id}/ingest`.
- Only the pinned Visual Skills and Scenario Skills repository/commit pairs are accepted:
  - `smixs/visual-skills` @ `61a60d317f0fa0c3dc98902e58a7cb178838ae3f`
  - `scenario-labs/skills` @ `94cab3f1da47841f52d4c7b3ea8583aa13dd0eb9`
- Fetches through GitHub Contents API over HTTPS, does not follow redirects, rejects non-file objects, traversal and symlink entries.
- Enforces 40-file, 512 KiB/file and 5 MiB/package limits.
- Recomputes Git blob SHA-1 and SHA-256, compares the entrypoint against the package provenance hashes, and stores nested local Markdown references and bounded file bytes in server-only Supabase tables.
- Ingestion is immutable per skill package; duplicate ingestion is rejected.
- Customer UI exposes source ingestion and integrity outcome.

### OpenManus Skill Resolver
- Added a worker-side Supabase resolver. It is shared by the registered OpenManus runtimes.
- Resolves only owner-scoped, installed, validated, license-approved, published skills whose install permission is approved and execution flag is true.
- Loads immutable text instruction files and records skill version/hash/permission snapshot against the Agent Run in `moreai_skill_execution_audit`.
- Injects skill material as explicitly untrusted context, not system policy.
- Applies a per-run allowlist mapping granted capability keys to registered OpenManus tools, and independently checks tool calls before execution. A skill cannot grant itself a tool.
- No second agent runtime was added; OpenManus remains the sole Agent Runtime.

### Permission release gates
- Admin permission review is scoped to a single installation (fixes cross-user grant propagation).
- Runtime activation requires both server flags `MOREAI_SKILL_RUNTIME_ENABLED=true` and `MOREAI_SKILL_RELEASE_GATE_PASSED=true`, plus validated source files, approved license and published package.
- Default behavior remains disabled. No flag was enabled as part of this source-only change.

### Database
- Added `moreai_skill_source_files` and `moreai_skill_execution_audit`, server-only with RLS and browser access revoked.
- Existing Skill Registry/Install tables remain the canonical persistence layer.

## Files touched in this increment

- `apps/api/app/routers/skills.py`
- `apps/api/app/routers/admin.py`
- `apps/worker/app/skill_resolver.py`
- `apps/worker/app/registry_factory.py`
- `engine/agents/durable_tool_runtime.py`
- `lib/api/client.ts`
- `components/views/skills-library-view.tsx`
- `supabase/migrations/20261114102000_moreai_skill_source_files_and_audit.sql`

## Remaining work before this vertical slice is complete

1. Complete robust recursive parsing of all Scenario Skills manifest formats, references, scripts, dependency manifests, NOTICE/license inheritance and asset types; current ingestion follows local Markdown links with strict caps, not a complete repository crawler.
2. Exact-version SBOM reconciliation and script/dependency security review.
3. Reviewer UI for license/publication/permission decisions.
4. Add skill selection to Agent Studio/chat enqueue contracts so users can attach installed skill IDs to new Agent Runs; resolver currently accepts run input `skill_ids`, but customer enqueue/UI does not yet populate that field.
5. Add durable permission-review audit events and idempotent/transactional ingestion to prevent partial file writes if persistence fails.
6. Integrate Gmail/Calendar OAuth and the remaining OpenFuse Connections Center capabilities.
7. Finish dashboard route-by-route API integration and remove remaining simulated actions.

## Operational restrictions

No test, lint, typecheck, build, browser/API/worker runtime probe, external provider operation beyond source fetch implementation, staging, deployment or Supabase mutation was performed. SQL migrations are committed but not applied. Runtime activation flags remain off; no live execution acceptance is claimed.
