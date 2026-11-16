# Phase 09D — Storage state, profile lifecycle and customer history

Date: 2026-11-16  
Target branch: `main`  
Baseline commit: `8b00ba16f46aaf81f29b7d68551f86fcc56a8870` (start of this continuation)  
Target code commit: `7c52eca3fad29fdfee5bbd2eee8ebb4dbae2d798`.

## Pinned OpenFuse contract inspected

Pinned upstream: `CopilotKit/openfuse@7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`.

The upstream worker source confirms its browser manager:
- Uses `WORKER_DATA_DIR` (default `.openfuse/browser-profiles`).
- Stores each profile at `<WORKER_DATA_DIR>/<session UUID>/profile` via Chromium persistent context.
- Persists session metadata atomically in `session.json`.
- Saves Playwright cookie state to `storage.json` on close.
- Restores session metadata as closed on worker startup and reopens the same persistent profile directory.
- Reads saved cookies on reopen and retains the Chromium profile directory.

MoreAI therefore uses the canonical MoreAI session UUID as the OpenFuse profile ID. Durable browser storage depends on the OpenFuse worker's `WORKER_DATA_DIR` being mounted to a persistent private volume. The MoreAI database `encrypted_state` field is not the active persistence mechanism in this integration and is not represented as proof of restored browser state.

## Source changes

- `apps/api/app/routers/browser_sessions.py`
  - Added customer session history projection with event timeline.
  - Added worker-only canonical owned-profile ID projection.
  - Existing acquire and close flow keeps durable cleanup requests and tenant ownership filters.
- `lib/api/client.ts`
  - Added typed `browserSessionHistory` method using FastAPI.
- `components/views/code-view.tsx`
  - Added historical sessions, closed/expired statuses, timestamps and up to five lifecycle events per session to Browser Sessions & Activity.
- `apps/sandbox/app/browser_supervisor.py`
  - Added authenticated OpenFuse profile listing and a delete-profile adapter.
- `apps/worker/app/main.py`
  - Added independent orphan-profile reconciliation with a complete ownership snapshot; partial snapshots abort deletion.
  - Added 30-day retention cleanup. The worker deletes only profiles returned by the FastAPI retention endpoint and acknowledges deletion only after the OpenFuse endpoint confirms success.
- `apps/sandbox/openfuse-patches/0001-openfuse-delete-profile.patch`
  - Added a unified source patch for the pinned OpenFuse worker's authenticated `DELETE /sessions/{id}/delete-profile` route and safe profile deletion implementation.
- `apps/sandbox/openfuse-patches/0001-durable-profile-delete-and-storage-contract.md`
  - Documents the persistent profile volume and deletion safety contract.
- `supabase/migrations/20261116153000_moreai_browser_profile_retention.sql`
  - Adds 30-day profile retention deadlines, deletion acknowledgement timestamps, retention notification timestamps and lifecycle event vocabulary.
- `supabase/migrations/20261116160000_moreai_browser_profile_retention_rpcs.sql`
  - Makes retention-eligibility claims and profile-deletion acknowledgement/event writes atomic using service-role-only database functions.
- `apps/api/app/routers/skills.py`
  - Tightened dependency evidence: direct package manifests no longer count as exact pins; npm, Poetry, uv, Pipfile, Cargo and Composer lockfiles are inventoried; unsupported lockfile formats and unresolved direct declarations fail validation closed.
  - Direct declarations are matched to lockfile-resolved versions; npm package integrity hashes are required.
  - Validation requires registry metadata resolution and SPDX license assertions before a package can become validated.
- `supabase/migrations/20261116150000_moreai_skill_publication_evidence_gate.sql`
  - Hardens the publication RPC: reviewer approval requires empty validation findings, source license evidence, a complete dependency inventory, and resolved registry metadata.
- `apps/api/app/routers/admin.py`
  - Exposes validation findings, SPDX SBOM, dependency resolution and source evidence to the Super Admin reviewer. The existing Super Admin Skills Review UI already renders these validation and SBOM details; no new reviewer screen was required.

## Orphan cleanup and retention compatibility gate

The pinned upstream OpenFuse worker currently exposes list/create/close/navigate/read/input/screenshot/download routes, but no profile deletion endpoint. A unified patch is now committed at `apps/sandbox/openfuse-patches/0001-openfuse-delete-profile.patch`. It adds an authenticated deletion route and refuses deletion while a Chromium context is active.

MoreAI's supervisor adapter and worker reconciliation now target that route. Until the patch is applied to the deployed OpenFuse worker, the endpoint returns an error and cleanup remains unavailable; no profile is falsely marked deleted.

Closed profiles receive a 30-day retention deadline. FastAPI records a single `profile_retention_eligible` event when the deadline is first reached. The worker then requests deletion from OpenFuse and FastAPI records `profile_deleted` only after a successful deletion acknowledgement. Retention eligibility and deletion acknowledgement plus their event rows are committed atomically through service-role-only RPCs. The API ownership inventory excludes acknowledged deleted profiles. Orphan cleanup uses exact count plus pagination and refuses deletion if the inventory is partial or exceeds the 10,000-row safety bound.

## Persistent volume requirement

The OpenFuse service deployment must mount `WORKER_DATA_DIR` to durable, private storage. An ephemeral container filesystem loses profile persistence across replacement. No volume was added to the Python browser supervisor compose file because that compose service is not the pinned OpenFuse TypeScript worker and does not own its `WORKER_DATA_DIR`.

## Customer history

The customer Browser Sessions panel now loads:
- current active/close-requested sessions;
- closed/expired session history;
- lifecycle event names and timestamps;
- browser action receipts.

All data is served through FastAPI and filtered by authenticated customer identity. No direct browser Supabase access was introduced.

## Remaining limits

- OpenFuse profile-delete extension is source-documented but not yet applied to the separately deployed OpenFuse service.
- Durable volume mount, backup/restore and encryption-at-rest still require infrastructure configuration. The 30-day retention policy is now implemented in source and migration, but it cannot execute until the OpenFuse deletion patch is applied and deployed.
- OpenFuse's upstream cookie persistence is best-effort on close; persistent Chromium profile storage is the primary state mechanism. A process crash can interrupt cookie snapshot writing.
- Malware scanning and browser download import remain blocked.
- Skills dependency lockfile inventory and publication evidence gates are stronger, but parser coverage remains intentionally incomplete for pnpm/yarn, Go module graph, Ruby and other unsupported ecosystems; those sources remain blocked from validation. License compatibility, malware scanning and legal rights clearance still require human review.

## Verification policy

No tests, lint, type checks, builds, browser/API/worker/Docker runtime calls, provider calls, staging or deployment were performed, per product-owner instruction. The OpenFuse source contract was inspected at the pinned commit; production runtime behavior is not claimed.

## Next implementation

1. Apply the committed profile-delete patch to the pinned OpenFuse deployment and mount its `WORKER_DATA_DIR` persistently; deployment credentials and runtime verification remain unavailable under the current instruction.
2. Complete remaining skill lockfile parsers and package provenance mapping, including unsupported ecosystems.
3. Add reviewer UI presentation for the expanded SBOM/dependency evidence where required; the existing reviewer screen already displays validation report and SPDX data.
4. Continue customer dashboard route-to-screen closure across Chat, Research, Create, Analyse, Tasks, Files, Memory and Skills.


## Phase 09D continuation — dependency parser coverage and dashboard boundary review

Continuation date: 2026-11-16. Changes committed directly to `main`.

### Dependency parser increment

- Added bounded, dependency-free parsers for pnpm lock snapshots and Yarn lock descriptors. Exact package versions are inventoried from lock entries; missing package integrity remains a validation finding rather than being silently accepted.
- Added Ruby `Gemfile.lock` Specs inventory for direct and transitive gems.
- Added Go `go.mod` direct declarations and `go.sum` checksum inventory; direct declarations are reconciled against exact lock entries using the common package/version matcher.
- Poetry lock entries with explicit non-registry source metadata (git/path/custom source) are now marked `non_registry_source_requires_provenance` and are not treated as ordinary PyPI registry packages.
- Parser provenance continues to identify the exact source lockfile path; Go checksum records and npm integrity values are retained as package evidence.
- Unsupported or ambiguous lock syntax, unresolved direct declarations, missing integrity, unpinned dependencies, and unsupported registry metadata remain fail-closed. Parser coverage does not itself prove a reproducible build, license compatibility, or full dependency graph closure.

### Customer dashboard integration inventory

The current repository already contains dedicated customer views for Chat, Research, Create, Analyse, Tasks, Files and Skills, plus Memory settings. The relevant integration seams are the typed FastAPI client in `lib/api/client.ts` and customer-scoped FastAPI routers under `apps/api/app/routers/`. Files and Tasks already use durable artifact/workspace and agent-run APIs; Skills uses customer-scoped import/ingest/validate/install/permission endpoints. Browser session history is served by FastAPI. No direct browser PostgREST, Storage, RPC or Realtime access was added.

This continuation did not redesign any screen. A complete per-control route-to-endpoint audit and any missing UI additions remain open; no screenshot comparison was performed because browser execution is explicitly prohibited for this phase.

### Current deployment and verification status

- OpenFuse patch remains committed as a deployment patch only. It has **not** been applied to the pinned deployed OpenFuse service; no OpenFuse deployment credential or authorized deployment action is available in this workflow.
- Persistent `WORKER_DATA_DIR` volume mount, backup/restore and encryption-at-rest remain infrastructure blockers.
- Supabase migrations are source-committed but were not applied to the live project.
- No tests, builds, lint, type checks, runtime calls, staging or deployments were run, per instruction. The new parsers are therefore source changes only and are not represented as verified.
- The exact target commit for this continuation is recorded in the GitHub branch history; current `main` HEAD must be confirmed after all sequential commits.

### Next implementation sequence

1. Close external OpenFuse deployment and persistent-volume configuration when authorized deployment access is available.
2. Complete package graph/provenance reconciliation for pnpm/Yarn/Go/Ruby, including source URLs, checksums and dependency-edge evidence; add registry metadata resolvers only where authoritative versioned metadata exists.
3. Finish route-to-endpoint and persistence audit for Chat, Research, Create, Analyse, Tasks, Files, Memory and Skills; implement only demonstrably missing integration seams and preserve existing UI.
4. Continue AGENTS.md Phase 09 integration gate evidence. Phase 10/11 remain blocked until the product owner authorizes verification.


## Phase 09D continuation — research entrypoint, dependency graph and live Supabase reconciliation

### Additional source changes

- `components/views/research-view.tsx`: added a visible “Mulai Riset dengan AI” action and Enter-key submission. It hands the user query to the existing parent Chat navigation callback with an explicit research instruction; execution therefore remains on the authenticated Chat → FastAPI → durable Agent Run path. No public/trending topic samples were fabricated. This is a minimal UI addition using the existing red action button, border, typography and spacing conventions.
- `apps/api/app/routers/skills.py`: dependency inventory now retains transitive dependency edges where the lockfile explicitly exposes them (npm package-lock v2/v3 and v1, Cargo, Composer). The graph is persisted inside the existing validation report/SBOM evidence; no new table or database was introduced.
- `components/views/super-admin-view.tsx`: reviewer evidence now presents the transitive dependency graph edges and count alongside the existing dependency inventory and SPDX SBOM.

### Live Supabase read-only inventory

The connected project was identified as `MoreAIdb`, ref `uunfgimtokhucegqbpce`, PostgreSQL 17, region `ap-southeast-2`, status `ACTIVE_HEALTHY`. Read-only schema, migration-history and `pg_policies` metadata were inspected; no migration or data mutation was performed.

Observed relevant tables and RLS state:
- Chat/workflow: `conversations`, `conversation_messages`, `agent_runs`, `agent_run_steps`, `workspaces` — RLS enabled.
- Files/knowledge: `artifacts`, `agent_workspace_files`, `knowledge_documents`, `knowledge_chunks` — RLS enabled.
- Memory: `moreai_customer_memory_preferences`, `moreai_customer_memories` — RLS enabled.
- Skills: `moreai_skill_packages`, `moreai_skill_source_files`, `moreai_skill_installs` — RLS enabled.
- Browser: `moreai_browser_sessions`, `moreai_browser_session_events`, `moreai_browser_action_receipts` — RLS enabled.

Observed policy posture:
- Chat tables, agent runs/steps, artifacts, knowledge tables, workspace files and skill tables have explicit deny-client policies (false predicates) for anon/authenticated roles, consistent with the FastAPI-only business-data boundary.
- Workspaces expose an authenticated SELECT policy constrained to active membership or ownership.
- Personal memory preference and memory tables expose owner-scoped authenticated policies using `auth.uid()`. Frontend code must nevertheless continue using FastAPI only; these policies are defense in depth, not permission for direct browser PostgREST access.
- The browser-session tables were RLS-enabled but no policy rows for those tables appeared in the inspected `pg_policies` result; this is default-deny behavior for roles without a policy, but service-role access and API repository behavior still require separate verification.

Migration reconciliation finding:
- Live migration history currently ends at `20261115101318` (`moreai_computer_action_receipts`).
- Repository migrations dated `20261116100000`, `20261116150000`, `20261116153000`, and `20261116160000` are not recorded in the live migration history at inspection time.
- Correspondingly, live `moreai_browser_sessions` did not expose `profile_retention_after`, `profile_deleted_at`, or `profile_retention_notified_at`; live event constraint metadata also did not show the new retention event vocabulary. These migrations remain unapplied.
- Do not run the worker's profile-retention loop against this live schema until the pending migrations have been applied through an authorized change window. The source already has fail-closed API/RPC error handling, but deployment/runtime behavior remains unverified.
- Migration history contains multiple similarly named historical versions for workspace, knowledge and learning objects. Reconciliation must use exact version IDs and SQL definitions, not filename-only assumptions.

### Dashboard integration evidence and remaining gaps

- Chat: conversation restore, message enqueue, SSE run streaming, cancellation, retry, attachments and workspace selection use typed FastAPI API client methods.
- Research: run and artifact history are loaded through FastAPI; the new research query action hands off to Chat so a durable Agent Run is created only after user submission.
- Create: provider capabilities are read from FastAPI; selected creation prompts hand off to Chat. Media generation remains blocked unless the worker capability endpoint reports an available provider.
- Analyse: upload/ingestion and document retrieval use FastAPI Knowledge APIs; analysis hands off with an explicit selected document ID.
- Tasks: Agent Run list/detail/progress/activity, cancellation/retry and artifact/learning outputs use FastAPI.
- Files: artifacts and workspace files/versions/upload/download lifecycle use FastAPI.
- Memory: consent, personal notes, episodic summaries and deletion use FastAPI customer memory routes.
- Skills: catalog/import/ingest/validate/install/permissions use FastAPI customer skill routes; admin reviewer evidence uses server-side admin routes.
- These are source-level integration paths, not end-to-end proof. Full per-control coverage, error-state review and auth/tenant verification remain open.

### UI preservation

Only `components/views/research-view.tsx` and `components/views/super-admin-view.tsx` were changed in this increment. Research gained one explicit run-start action; Super Admin gained a compact dependency-graph evidence block. Existing navigation, layout, colors, typography, responsive structure and component patterns were retained. Before/after browser screenshots were not captured because browser testing is prohibited by the current instruction.

### Verification and blockers

- Supabase schema and policy inspection was read-only; no DDL, data writes, migration apply, test, build, lint, typecheck, browser, runtime, staging or deployment was performed.
- OpenFuse deployment patch and persistent `WORKER_DATA_DIR` volume remain unapplied/unconfigured.
- The live Supabase schema is behind the latest repository migrations for browser retention. The new retention path must not be considered operational until those migrations and OpenFuse deployment are completed.
- pnpm/Yarn/Go/Ruby parsers and dependency-edge extraction are source-only, not validated. Registry metadata/license coverage remains incomplete for Go/Ruby and non-registry sources. Full transitive closure and integrity are not proven.


## Follow-up source reconciliation — 2026-11-16

### Customer Memory route de-duplication

- Source inspection found two FastAPI handlers registered for the same `DELETE /api/v1/customer/memory` route in `apps/api/app/routers/customer.py`.
- The later handler invoked `moreai_customer_clear_personal_memory` but did not run the owner-scoped episodic metadata cleanup used by the earlier handler. Since FastAPI route registration order can cause the first matching handler to be selected, the duplicate created ambiguous behavior and risked leaving episodic summaries behind.
- Removed the later duplicate handler. The remaining handler explicitly disables consent, purges owner-scoped episodic metadata and deletes user-authored memory; errors return 503 rather than claiming success.
- The existing database RPC remains available for other callers; no schema changes were made. The endpoint's multi-step cleanup is not a single cross-table transaction, so partial cleanup remains a recoverable failure path rather than atomic completion.

### Python dependency graph expansion

- `apps/api/app/routers/skills.py` now extracts dependency edges from Poetry and uv lockfile package records when the lockfile encodes dependency declarations as a map or structured list.
- Edge records retain ecosystem, source package, target package, dependency kind and requested specifier. Non-registry source packages continue to be flagged for provenance review instead of being silently treated as registry packages.
- Existing npm/Cargo/Composer edge extraction remains. The graph is evidence, not a guarantee of complete dependency closure; optional groups, platform markers, extras, workspace aliases, package-source identities and lockfile dialect variants still require broader coverage.
- No parser execution, test, lint, typecheck or build was run.

### UI scope

No additional UI files changed in this increment. The Memory component already uses the typed FastAPI customer memory methods for consent, create, edit, delete and clear actions. The API duplicate-route correction improves the clear action's server-side lifecycle without changing the visible design.

### Live Supabase reconciliation remains unchanged

- Canonical live project: `uunfgimtokhucegqbpce`.
- Live migration history last observed: `20261115101318`.
- Pending repository migration files observed: `20261116100000_moreai_browser_session_close_event_constraint.sql`, `20261116150000_moreai_skill_publication_evidence_gate.sql`, `20261116153000_moreai_browser_profile_retention.sql`, `20261116160000_moreai_browser_profile_retention_rpcs.sql`.
- The browser profile retention columns and new event vocabulary are absent from the inspected live table metadata. No migration was applied.
- Browser session, browser event and browser receipt tables have RLS enabled. The inspected `pg_policies` result returned no explicit policies for these three tables, which means no ordinary authenticated/anon policy path was observed; verify service-role-only grants and all table/function privileges before any change to policy.
- Chat, Agent Run, artifact, knowledge, skill and workspace-file tables show explicit deny-client policies. Memory tables show owner-scoped policies. The browser must still use FastAPI for all application data, consistent with AGENTS.md.
- No storage policy changes were made; no storage bucket policy inventory was retrieved in this increment. Storage authorization mapping remains open.

### Exact source commits in this continuation

- `6549a809d7bde82151c1af9b942ba3f9968a8ce3` — remove duplicate Memory clear endpoint.
- `64affc7b82cae1eb8922f75bee627b539dee8adf` — Poetry/uv dependency graph edges.
- This report is updated in the final documentation commit for this increment.

### Acceptance status

Phase 09D remains IN PROGRESS. This increment improves source correctness and evidence but does not close all customer action mappings, dependency ecosystem coverage, live Supabase migration reconciliation, OpenFuse deployment, or AGENTS.md Phase 09 acceptance. Phase 10 and Phase 11 remain blocked by the owner instruction prohibiting real tests and by unavailable deployment prerequisites.


## Follow-up — dependency file provenance and authorization inventory (2026-11-16)

### Source implementation committed

- `apps/api/app/routers/skills.py` now emits a per-manifest/lockfile evidence record containing repository-relative path, ingested SHA-256, Git blob SHA, byte size and file role. The report includes a completeness flag that is false if any inventoried dependency file lacks a valid SHA-256.
- Cargo dependency edges now preserve both endpoint versions and the lockfile source identity instead of collapsing packages to name-only edges. This avoids merging distinct versions or git/registry source variants in the evidence graph.
- Corrected a parser control-flow defect: an earlier generic `go.mod` branch shadowed the later structured parser, preventing Go direct requirements from being inventoried. The structured declaration parser is now reachable and direct declarations are still required to reconcile to `go.sum` evidence.
- Commit: `4536c784c0be16942483a8492f0c1ed5adfca963`.
- pnpm/Yarn currently retain exact package inventory and integrity status where parsed, but complete dependency edges, peer/optional resolution semantics, workspace aliases, platform conditions and full package-source identity remain open. This increment does not claim ecosystem-complete transitive closure.

### Supabase authorization/storage read-only reconciliation

Canonical project `uunfgimtokhucegqbpce` was queried again using `pg_policies`, bucket metadata and migration history. No DDL, policy, grant, bucket or data mutation was performed.

- Explicit `anon, authenticated` deny policies (`USING false` / `WITH CHECK false`) were observed for core business tables including conversations/messages, agent runs/steps/events, artifacts, credit ledger/reservations, knowledge documents/chunks, skill packages/source files/installs, connection credentials/actions, OAuth states and workspace file/version records.
- Memory preferences and memory records have owner-scoped authenticated policies using `auth.uid()`. Workspaces and membership tables have membership/owner constrained read policies. Profile, entitlement, partner membership/location and selected network-session tables have narrow owner/member read policies. These policies do not relax the browser-to-FastAPI-only business data boundary in AGENTS.md.
- Browser session, browser event and browser receipt tables remain RLS-enabled with no explicit policy rows observed for those tables; ordinary anon/authenticated access is therefore not evidenced. Service-role table grants and API repository access still require a separate privilege inventory before acceptance.
- Storage buckets observed: `moreai-artifacts` (private; 150,000,000-byte limit; text/markdown/json/csv/pdf/png/jpeg/webp) and `moreai-knowledge-private` (private; 26,214,400-byte limit; pdf/jpeg/png/webp). A server-only deny policy was observed for `moreai-knowledge-private`. No matching `storage.objects` policy was returned for `moreai-artifacts`; its effective grant/policy path remains unverified and must be confirmed server-only before release.
- Live migration history still ends at `20261115101318`. Four repository migrations remain absent from live history: `20261116100000`, `20261116150000`, `20261116153000`, `20261116160000`. Browser retention columns/event constraint remain unapplied. No migrations were applied.

### Acceptance impact

Phase 09 remains IN PROGRESS. Source provenance is stronger, but lockfile dialect/edge completeness, complete dashboard control-to-endpoint authorization mapping, browser service-role grants, artifact-bucket policy/grants, four pending migrations, and OpenFuse patch + persistent volume deployment are still open. No tests, builds, lint, type checks, runtime, staging or deployment were performed. Phase 10/11 remain blocked by the explicit no-test instruction and infrastructure prerequisites.
