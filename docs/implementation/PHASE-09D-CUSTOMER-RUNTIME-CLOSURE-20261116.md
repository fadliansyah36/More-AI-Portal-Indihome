# Phase 09D — Customer Runtime Closure and Supabase reconciliation

Date: 2026-11-16  
Target: `main`  
Baseline: `77931b17248095237b6590fbeea805cb35cee0e4`  
Execution policy: no tests, builds, lint, typecheck, browser/API/worker/provider runtime calls, staging, or deployment.

## Supabase migration reconciliation completed

Project: `uunfgimtokhucegqbpce` (MoreAIdb, PostgreSQL 17).

The repository contained ten forward-only Phase 09D migrations absent from live migration history. Four additional forward-only security/capacity migrations were added and applied during this continuation. Their SQL was reviewed against the live schema, current migration history, and existing MoreAI data/API boundaries. All fourteen were applied sequentially using Supabase migration operations; no historical version was rewritten and no destructive table/data operation was used.

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
| `20261116083600_moreai_server_only_deny_rls_policies` | `20261116083654` | Applied |
| `20261116090000_moreai_browser_capacity_leases` | `20261116083856` | Applied |
| `20261116091000_moreai_browser_capacity_lease_owner_fencing` | `20261116083934` | Applied |
| `20261116092000_moreai_browser_capacity_single_worker_limit` | `20261116084745` | Applied |

Read-only metadata reconciliation after migration application confirmed:
- Browser profile retention columns exist on `moreai_browser_sessions`.
- Retention claim/ack, browser close request/completion, and atomic Memory clear/create/disable functions exist with the expected signatures.
- Memory atomic functions are SECURITY INVOKER; browser lifecycle RPCs are SECURITY DEFINER and have restricted execution grants to `service_role`.
- `moreai-artifacts` now has an explicit `anon, authenticated` deny policy while FastAPI continues to use the server-only service-role boundary.
- Live migration history contains all ten applied operations.

No business records were inserted, deleted, or modified by the read-only reconciliation queries.

## Security advisor finding and source migration

The Supabase security advisor initially reported 16 RLS-enabled application tables without explicit policies. They were default-deny, but the MoreAI architecture requires an explicit browser-deny policy for all business data. Migration `20261116083600_moreai_server_only_deny_rls_policies.sql` was applied as live version `20261116083654`; read-only metadata confirmed all 16 `USING (false)` / `WITH CHECK (false)` policies. The new `moreai_browser_capacity_leases` table also has its own explicit deny policy. The policy migration does not grant client access or change the FastAPI service-role access boundary.

The migration is committed in source and applied to production as live version `20261116083654`. Read-only metadata confirms 16 explicit deny policies now exist. The security advisor no longer reports the 16 `rls_enabled_no_policy` findings.

After the deny-policy migrations, the security advisor no longer reports `rls_enabled_no_policy`. One warning remains: leaked-password protection is disabled in Supabase Auth. This is an Auth dashboard configuration and is not changed by SQL migration.

## OpenFuse runtime parity

- The pinned OpenFuse worker restores session metadata from its configured `WORKER_DATA_DIR` and reopens the same persistent profile ID; MoreAI's worker adapter already reuses the canonical session UUID.
- The profile deletion extension remains a committed patch against the pinned upstream worker, not deployed to the live OpenFuse service.
- Added a pinned OpenFuse worker image build that clones commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`, applies the profile-delete patch and a MoreAI private-egress proxy override. The Node worker is isolated on an internal Docker network and can reach public sites only through the separate allowlist/pinned-IP egress proxy.
- Compose now defines a persistent `openfuse_browser_profiles` volume, a 10-minute idle context timeout, a private `moreai_browser_isolated` network, and a ClamAV service. Same UUID/profile is reopened after context close or worker restart when the same persistent volume is mounted.
- The MoreAI worker adapter now uses a stable browser-service worker identity, obtains a shared Supabase capacity lease (global limit 3, per-user limit 2, 660-second lease) and is fenced against another browser service instance taking an unexpired session lease. The cap matches the pinned OpenFuse worker's `maxSessions=3`; do not scale browser-worker replicas until profile storage is shared and routing is sticky.
- Browser download bytes are fetched only from the private OpenFuse worker, scanned with ClamAV INSTREAM, then posted to the owner/run/session-checked FastAPI internal artifact endpoint with signature, size and SHA-256 checks. Scanner failure blocks import.
- These are source/Compose integrations only. The production host has not supplied the immutable ClamAV image digest, secrets, allowlist, external network attachment or encrypted persistent-volume attestation. No OpenFuse/ClamAV containers were started and no runtime browser/download scan was executed.
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

1. Provision the OpenFuse Compose stack on an authorized host with immutable ClamAV image digest, secrets, allowlist, external worker network attachment and encrypted persistent profile volume; keep it to one browser-worker replica until shared profile storage is available.
2. Run the Customer Skills Library batch action to recursively ingest the 56 Motion entrypoints; resolve dependency edge closure, SBOM, nested licenses and asset provenance, then reviewer approval. The batch action is source code only and has not been run in this assistant session.
3. Finish Visual/Scenario recursive package ingestion and exact-version dependency/asset provenance.
4. Connect real media providers and persistent workers; only then enable image/video generation and wire provider routing, wallet reservation/settlement, ledger and private artifact projection.
5. Complete Customer dashboard action-to-API acceptance and security review without bypassing FastAPI or Supabase.
6. Resolve the remaining Supabase Auth leaked-password protection warning through the Auth configuration surface.


## Supabase explicit deny policy applied

- Live migration version: `20261116083654` for `moreai_server_only_deny_rls_policies`.
- Read-only metadata query confirmed 16 explicit deny policies on the 16 server-only tables.
- Updated Supabase security advisor output now contains only the Auth leaked-password-protection warning; the previous 16 RLS-without-policy INFO findings are no longer present.


## 2026-11-16 OpenFuse persistent profile, egress, download scanning and capacity continuation

### Source integration
- Added `apps/sandbox/Dockerfile.openfuse`, which builds the pinned upstream worker commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`, applies the profile-delete patch and overlays a MoreAI egress proxy implementation.
- The OpenFuse worker's loopback proxy accepts HTTPS CONNECT only and forwards to the separate MoreAI egress proxy. The browser worker container is attached only to the Docker internal network; the egress proxy validates the allowlist and public DNS/IP before connecting.
- Compose now mounts persistent `openfuse_browser_profiles`, retains profile metadata/cookies across restart, closes idle contexts after 10 minutes, and reopens the same session UUID on the next action.
- The MoreAI worker uses a stable browser-service worker ID (service hostname by default), not its own container hostname. This keeps leases stable across worker process restarts when the browser service/volume remains the same.
- Shared Supabase capacity lease is serialized by a transaction advisory lock and owner-fenced. Current single OpenFuse service cap: 3 active sessions globally, 2 per customer, 660-second lease; the 10-minute OpenFuse idle close gives a one-minute lease grace. Close completion deletes the lease atomically.
- ClamAV INSTREAM scanning is now in the MoreAI BrowserSupervisor download path. Only a clean PDF with matching SHA-256, expected signature, active owner session and running/completed owner Agent Run is accepted by the internal FastAPI artifact endpoint. The resulting artifact is stored in the private artifact bucket and appears through the existing Customer artifact list.

### Applied Supabase capacity migrations
| Migration | Live version | Result |
|---|---:|---|
| `moreai_browser_capacity_leases` | `20261116083856` | Applied |
| `moreai_browser_capacity_lease_owner_fencing` | `20261116083934` | Applied |
| `moreai_browser_capacity_single_worker_limit` | `20261116084745` | Applied |

Read-only metadata confirms the capacity lease table is RLS-enabled with an explicit anon/authenticated deny policy, the admission function is SECURITY DEFINER with an empty search_path, and the live function now uses the 3-session global limit. No active capacity lease rows existed at the time of metadata inspection.

### Operational boundary
The Compose stack and worker network attachment are committed but not deployed. The actual host still needs a digest-pinned ClamAV image, secrets, exact domain allowlist, external private network attachment for the MoreAI worker, and encrypted persistent volume/backup policy. The browser worker must remain a single replica until profile storage is shared across replicas. No container was built or started; no browser runtime, session recovery, malware scan or download import was executed.


## Canonical provider and worker registry snapshot

Read-only Supabase counts at the latest reconciliation: `llm_providers=0`, `llm_models=0`, `moreai_worker_capability_snapshots=0` fresh within 90 seconds, `moreai_browser_sessions=0` active, and `moreai_browser_capacity_leases=0` unexpired. The provider/worker adapters remain source-level only. No fake provider, model, heartbeat or credit ledger record was seeded. Actual OpenManus execution and media generation remain unavailable until the real provider secrets, model prices, quota/entitlement policy and always-on worker are provisioned.
