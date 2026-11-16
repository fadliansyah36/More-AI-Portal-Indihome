# Phase 09 — Skill ingestion contract alignment and resumability (2026-11-16)

## Scope and baseline

Target branch: `main`  
Baseline before this increment: `c7c4c0174a88d43f62a0c0e8748b86119ec319e4`

Commits:
- `fddb8e7b418de44bec13bbddda1a36758b3567cc` — add forward-only Supabase migration to align the atomic source-ingestion RPC file count with FastAPI.
- `2b9c6b442c9c160046f1a1004ec1087912a58b4f` — add forward-only migration to keep source-ingested packages pending until explicit SBOM validation.
- `1f612973efa4797399556e19237c48ee935fe017` — make the FastAPI source-ingestion endpoint idempotently reconcile previously persisted immutable source files.

No UI, navigation, visual token, API route path, customer record, provider, worker or OpenFuse runtime was added or activated.

## Findings corrected

### FastAPI ↔ Supabase file-count contract

FastAPI had a bounded package limit of 64 source files, while the live atomic Supabase RPC still rejected arrays above 40. Pinned Scenario skill folders may contain 41–56 files. This meant that the Customer batch could successfully fetch a package and then fail at the canonical persistence boundary.

Migration `20261116230000_moreai_skill_source_file_count_alignment.sql` changes only that maximum to 64. It retains:
- owner ID and owner-scoped package lookup;
- immutable single-ingestion protection;
- 128-node FastAPI traversal cap;
- 512 KiB per-file limit and 5 MiB expanded package limit;
- Git blob SHA-1 and content SHA-256 validation;
- relative-path traversal rejection and duplicate-path rejection;
- text/binary payload exclusivity;
- service-role-only RPC execution and anon/authenticated revocation.

### Correct pending state until explicit validation

The previous RPC marked a successfully ingested package `review_required` before the validation endpoint had evaluated its SBOM, dependency graph and license evidence. The existing Customer batch treats `validated` and `review_required` as terminal outcomes on reruns, so a browser interruption between ingestion and validation could leave a package permanently skipped.

Migration `20261116240000_moreai_skill_ingestion_pending_until_validation.sql` changes the post-ingestion state to `pending`. The existing Customer batch will therefore continue to the validate step after a resumed source ingest. The explicit FastAPI validation action remains responsible for setting `validated` or `review_required`.

### Idempotent source reconciliation

The FastAPI `POST /api/v1/customer/skills/{skill_id}/ingest` path now checks for existing source rows before fetching upstream files again. If rows exist, it reconciles every stored path and SHA against the immutable initial ingestion report or validated SPDX file inventory and verifies the root entrypoint against the package's pinned Git blob SHA and SHA-256.

- Exact match: returns an idempotent integrity-verified response with `already_ingested=true`; it does not overwrite source rows.
- Missing/mismatched evidence: returns HTTP 409 and fails closed.
- No existing source rows: the original bounded pinned recursive ingestion proceeds unchanged.

This closes the interruption window between a successful database commit and the browser receiving the response, without requiring a customer UI redesign.

## Supabase application and postcondition

Canonical project: `uunfgimtokhucegqbpce`.

Both forward-only migrations were successfully applied:
- `moreai_skill_source_file_count_alignment` — Supabase migration version `20261116113124`.
- `moreai_skill_ingestion_pending_until_validation` — Supabase migration version `20261116113852`.

Read-only function-definition and privilege inspection confirms:
- the live RPC contains the 64-file guard;
- the previous 40-file guard is absent;
- successful ingestion sets `validation_status='pending'`;
- `service_role` can execute the RPC;
- `anon` and `authenticated` cannot execute the RPC.

No package rows or source-file rows were inserted, updated or deleted by these migrations.

## Frontend and UI preservation

No frontend component was changed. Existing Customer Skills Library batch controls, sequential progress display and styles remain unchanged. The correction is implemented at the FastAPI/Supabase seam so the current UI can resume correctly after an interrupted ingest.

No before/after screenshot was required for this increment because no UI file or visual output changed.

## Verification boundary

No tests, lint, type-check, parser execution, build, browser/customer session, API endpoint runtime, worker/provider call, real skill batch, staging or deployment was run manually. Postcondition verification was limited to read-only SQL function-definition/privilege inspection and Supabase migration history.

The repository's existing Git-to-Vercel integration may automatically create deployments for source commits; any such deployment is pipeline evidence only, not a customer-runtime or E2E acceptance.

The 230 pinned entrypoints have not been ingested. Provider/model configuration and live worker remain unconfigured. Legal approval and asset redistribution rights remain human-review gates; this change does not approve any skill.

## Phase decision and next work

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED**.

Next operational order remains:
1. Authorized LUKS-backed host provisioning for OpenFuse/ClamAV and private persistent worker network.
2. Add the GitHub source token to Vercel `more-ai-api` as an encrypted secret.
3. Run the three authenticated Customer batches: Motion 56; Visual 2 + Scenario 172.
4. Complete remaining SBOM/dependency/license/NOTICE/provenance/asset human review.
5. Configure approved provider/model secrets, pricing, billing, credits, quota and entitlements.
6. Start the persistent worker and obtain heartbeat/readiness.
7. Complete Customer action-by-action API/security review and obtain the authorized integration acceptance evidence.

## Post-commit deployment reconciliation (read-only)

After the source and migration commits:
- Latest observed frontend production deployment: READY, deployment `dpl_FJU1QCdDefhwBSSTXh8KzwYopJFZ`, source commit `fddb8e7b418de44bec13bbddda1a36758b3567cc`.
- Latest observed FastAPI production deployment: READY, deployment `dpl_3osyzfU6os8UMV1zpmRRZ1zYowxo`, source commit `7628d110b1e7ce0b262ab38262ad2cd887a369a2`.
- The FastAPI idempotent-ingestion source commit `1f612973efa4797399556e19237c48ee935fe017` has no corresponding Vercel API deployment in the read-only deployment history. It is source-committed but is not confirmed in the current deployed API.
- The latest read-only API environment inventory still has no `MOREAI_GITHUB_TOKEN`; `MOREAI_AGENT_EXECUTION_ENABLED` remains `false`.
- No manual Vercel deployment or promotion was initiated. The existing Vercel Git integration produced the frontend deployment automatically; READY state is not runtime/E2E acceptance.
- Consequently, do not start the 230-skill batch against production until the API source update is deployed through the approved release process and the GitHub token is configured.
