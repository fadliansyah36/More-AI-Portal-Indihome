# Phase 09D — Customer Runtime Closure and Supabase reconciliation

Date: 2026-11-16  
Target: `main`  
Baseline: `77931b17248095237b6590fbeea805cb35cee0e4`  
Execution policy: no tests, builds, lint, typecheck, browser/API/worker/provider runtime calls, staging, or deployment.

## Supabase migration reconciliation completed

Project: `uunfgimtokhucegqbpce` (MoreAIdb, PostgreSQL 17).

The repository contained ten forward-only Phase 09D migrations absent from live migration history. Their SQL was reviewed against the live schema, current migration history, and existing MoreAI data/API boundaries. They were applied sequentially using Supabase migration operations; no historical version was rewritten and no destructive table/data operation was used.

| Repository migration | Live migration version | Result |
|---|---:|---|
| `20261116100000_moreai_browser_session_close_event_constraint` | `20261116083451` | Applied |
| `20261116150000_moreai_skill_publication_evidence_gate` | `20261116083455` | Applied |
| `20261116153000_moreai_browser_profile_retention` | `20261116083458` | Applied |
| `20261116160000_moreai_browser_profile_retention_rpcs` | `20261116083502` | Applied |
| `20261116170000_moreai_artifacts_storage_server_only` | `20261116083506` | Applied |
| `20261116180000_moreai_browser_profile_retention_retry_lease` | `20261116083510` | Applied |
| `20261116190000_moreai_browser_session_close_atomic` | `20261116083514` | Applied |
| `20261116200000_moreai_browser_session_close_request_atomic` | `20261116083517` | Applied |
| `20261116210000_moreai_browser_session_worker_close_atomic` | `20261116083521` | Applied |
| `20261116220000_moreai_customer_memory_clear_atomic` | `20261116083527` | Applied |

Read-only metadata reconciliation after migration application confirmed:
- Browser profile retention columns exist on `moreai_browser_sessions`.
- Retention claim/ack, browser close request/completion, and atomic Memory clear/create/disable functions exist with the expected signatures.
- Memory atomic functions are SECURITY INVOKER; browser lifecycle RPCs are SECURITY DEFINER and have restricted execution grants to `service_role`.
- `moreai-artifacts` now has an explicit `anon, authenticated` deny policy while FastAPI continues to use the server-only service-role boundary.
- Live migration history contains all ten applied operations.

No business records were inserted, deleted, or modified by the read-only reconciliation queries.

## Security advisor finding and source migration

The Supabase security advisor initially reported 16 RLS-enabled application tables without explicit policies. They were default-deny, but the MoreAI architecture requires an explicit browser-deny policy for all business data. Migration `20261116083600_moreai_server_only_deny_rls_policies.sql` was applied as live version `20261116083654`; read-only metadata confirmed all 16 `USING (false)` / `WITH CHECK (false)` policies. The policy migration does not grant client access or change the FastAPI service-role access boundary.

The migration is committed in source and applied to production as live version `20261116083654`. Read-only metadata confirms 16 explicit deny policies now exist. The security advisor no longer reports the 16 `rls_enabled_no_policy` findings.

After the deny-policy migration, the security advisor no longer reports `rls_enabled_no_policy`. One warning remains: leaked-password protection is disabled in Supabase Auth. This is an Auth dashboard configuration and is not changed by SQL migration.

## OpenFuse runtime parity

- The pinned OpenFuse worker restores session metadata from its configured `WORKER_DATA_DIR` and reopens the same persistent profile ID; MoreAI's worker adapter already reuses the canonical session UUID.
- The profile deletion extension remains a committed patch against the pinned upstream worker, not deployed to the live OpenFuse service.
- Durable private `WORKER_DATA_DIR` volume, backup/restore and encryption-at-rest are not configured from this repository workflow.
- Browser download import remains fail-closed because no malware scanning service is provisioned.
- Per-process OpenFuse `maxSessions` is not a cross-replica tenant admission coordinator. Multi-replica capacity coordination remains open.
- No OpenFuse deployment, Docker/browser execution or worker runtime operation was performed.

## Skills and media

- Motion source catalog pins 19 pack repositories and identifies 56 Motion `SKILL.md` entrypoints.
- The existing customer import/ingest flow recursively fetches each skill directory and referenced local files with path, Git blob and SHA-256 integrity checks and bounded size/file limits.
- Full recursive ingestion of all 56 Motion packages has not been executed. The customer registry currently supports one-by-one private import and ingestion; publication and execution remain blocked until SBOM/dependency/license/asset evidence and reviewer approval pass.
- `generative-illustration-skills` has no root LICENSE and remains `NOASSERTION`.
- Media adapters retain provider, entitlement, quota, wallet/ledger and artifact gates. No provider secrets, persistent worker, video rendering provider, or runtime call was provisioned. Image/video generation must remain unavailable when readiness gates are not satisfied.

## Customer dashboard status

Existing Chat, Research, Create, Analyse, Tasks, Files, Memory, Skills, Agent Studio and Browser Sessions surfaces use the typed FastAPI customer API boundary in source. The Create Studio Motion skill selector passes approved installed Motion skill IDs through the existing chat enqueue contract. This is source integration, not proof of live end-to-end execution.

## Verification and release

- No tests, build, lint, typecheck, browser/API/worker/provider calls, staging or deployment were run, as instructed.
- Read-only Supabase metadata and advisor queries were used only for migration/schema/security reconciliation; they are not runtime acceptance tests.
- Phase 09 remains IN PROGRESS.
- Phase 10 remains NOT ACCEPTED and Phase 11 remains BLOCKED.
- No production application deployment was attempted.

## Next work

1. Close the remaining Auth leaked-password protection warning through the Supabase Auth configuration surface when an authorized configuration window is available.
2. Add shared tenant/global browser capacity leases or a database-backed admission coordinator before multi-replica OpenFuse operation.
3. Apply the pinned OpenFuse profile-delete patch to the deployed service and provision persistent private profile storage through authorized infrastructure access.
4. Provision a malware scanner and keep download import blocked until a clean verdict is recorded.
5. Add a resumable bulk ingestion workflow for the 56 Motion entrypoints; complete dependency edge closure, SBOM, nested license and asset provenance, then reviewer approval.
6. Connect real provider/worker media generation and durable artifact projection only after secrets, pricing, entitlements and quota/credit settlement are configured.


## Supabase explicit deny policy applied

- Live migration version: `20261116083654` for `moreai_server_only_deny_rls_policies`.
- Read-only metadata query confirmed 16 explicit deny policies on the 16 server-only tables.
- Updated Supabase security advisor output now contains only the Auth leaked-password-protection warning; the previous 16 RLS-without-policy INFO findings are no longer present.
