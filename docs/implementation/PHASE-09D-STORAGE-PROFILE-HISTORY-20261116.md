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
