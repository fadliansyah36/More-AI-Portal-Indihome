# Phase 04 — Persistent Workspace Snapshot Bridge (2026-11-13)

## Scope and repository target

- Repository: fadliansyah36/More-AI-Portal-Indihome
- Branch: main
- Baseline before this increment: d0808c3de676122a0664269641a5cc36d5220bec
- Target: connect durable Supabase workspace files to the isolated Python/Bash runner and commit successful changes back as immutable, versioned workspace objects.
- Existing Customer UI was not changed.

## Implementation

### Worker and workspace access

- Added bounded workspace snapshot export in engine/tools/workspace.py.
- Snapshot listing is constrained by workspace_id, active (not deleted) files, and a maximum of 200 files / 2 MiB.
- Every listed file is re-authorized through moreai_workspace_get_file using the run's authenticated user and workspace context.
- Storage object paths are constrained to the authenticated user/workspace/version prefix.
- Downloaded bytes are checked against stored size_bytes and SHA-256 before entering the snapshot.
- Python/Bash tool handlers now receive workspace_id from the durable AgentRunContext through the policy-enforced registry. The identity is not accepted from model-generated tool arguments.
- Sandbox activation fails closed when the persistent workspace adapter is unavailable.

### Isolated runner and supervisor

- apps/sandbox/app/runner.py now accepts a bounded snapshot, materializes it only inside the disposable runner's /tmp/workspace tmpfs, and runs Python/Bash with that directory as the working directory.
- Runner returns a bounded snapshot of regular files after execution. Symlinks are rejected; no host path or host mount is exposed.
- apps/sandbox/app/execution_supervisor.py validates the base64 snapshot envelope, limits file count and decoded bytes, passes the snapshot into the runner, and returns the resulting snapshot to the authenticated worker.
- Worker adapter decodes the result and only attempts write-back after exit_code=0 and timed_out=false. Failed or timed-out execution changes are discarded.

### Versioned write-back

- Changed/new files are uploaded to fresh immutable Storage object paths and committed through existing worker-lease-fenced workspace CAS RPCs.
- New file creation expects version 0, preventing concurrent insert overwrite.
- Existing file updates must match the baseline version. Conflicts stop subsequent writes.
- Removed files are persisted through the existing soft-delete RPC.
- Deleted paths cannot be silently recreated; the explicit restore workflow remains required.
- The implementation commits each file independently, not as one atomic multi-file transaction. Earlier file commits remain valid if a later file conflicts. This limitation is explicit in apps/sandbox/README.md.

## Files changed

- apps/sandbox/app/runner.py
- apps/sandbox/app/execution_supervisor.py
- apps/worker/app/sandbox_tools.py
- apps/worker/app/registry_factory.py
- engine/tools/workspace.py
- engine/tools/registry.py
- apps/sandbox/README.md
- docs/implementation/PHASE-TRACKER.md
- docs/implementation/openmanus-backend-capability-map.json

## Data flow

Supabase Storage immutable workspace objects → worker membership/metadata RPC → SHA-256/size verification → authenticated supervisor request → disposable network-disabled runner snapshot → changed-file result → worker version/lease CAS → new immutable Storage objects and soft-delete records.

No schema migration or live Supabase mutation was required for this source increment. Existing workspace CAS/delete RPC contracts are reused.

## Security boundaries and limitations

- Service-role credentials remain server-side in the worker; they are not passed to the sandbox.
- The runner receives only the selected workspace snapshot, source code and no network capability.
- Workspace paths are validated at worker and runner boundaries; symlinks are rejected.
- Snapshot caps: 200 files and 2 MiB total, with per-file Storage limits inherited from the existing workspace contract.
- Write-back is lease-fenced and version-fenced per file but is not an atomic multi-file transaction.
- This bridge is source-level only. Sandbox remains disabled unless MOREAI_SANDBOX_ENABLED=true and MOREAI_SANDBOX_RELEASE_GATE_PASSED=true.
- Runner/supervisor deployment, immutable image publication, private worker network attachment, Docker socket proxy policy and runtime acceptance remain outstanding.
- Full upstream server/session parity and other Phase 04 capabilities remain incomplete.

## Verification and deployment

- Per instruction: no tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment, Supabase migration or live Supabase write were performed.
- No runtime success is claimed. The implementation is committed source code only.
- No frontend/UI files were touched.

## Next work

1. Phase 04: complete OpenManus server/session lifecycle parity, exception/logging parity, controlled browser download scanning/quarantine, and supervisor deployment contract; then review workspace multi-file atomicity and orphan-object cleanup.
2. Phase 06: complete Customer/Partner/Admin endpoint response models, authz, idempotency and OpenAPI coverage.
3. Phase 07: complete worker recovery, retry, heartbeat, cancellation, checkpoints, lease fencing and outbox.
4. Phase 08: complete all agent types, provider/model routing, tool adapters, planning/orchestration, memory and RAG.
5. Phase 09: connect all existing Customer Dashboard screens/actions through the typed FastAPI client without redesign.


## Commit evidence

- Source commits: 7849e00fa23ef259c7349aad75d43278fafde194, a7022638fba6b6944e00e0aea2c54c16ee130460, 96081b36e78d08ba92d3f74157d77c880343ed23, e6f2a3303698d6665bedab9bdf95423522cafb68, 76f46b91626581a3d7f66d86152650df0293260e, 3457aeeda21469385ce4d534589580cf5f7c8298, c841c708a098d0349fd5b066ece2cc69cb226599, 7890e8a21972e01511566dcc50997bf8565236e6, 33cc0e105f423e981e66c3a11eebeff0517ee179, 7ae5ad0389660278e713587e34fedd7f7efe5edd, 1fe50efa6302c0ca77fa25c8144bdce69416a98e, 5162fe2b470b5f8db34d60c6736a4e5ab6e5d18f, 817aa2011f713e17571714ca0ae63c02c40e24fd, 53ad5f50455d21add45b11df3792468660fbbf73, b7db9fcec321457edcd50232d4645c493cbd5f63.
- Documentation commits follow in the tracker, capability map and README. Target source HEAD before the documentation-only updates: b7db9fcec321457edcd50232d4645c493cbd5f63.
- The runner buffers child stdout/stderr to temporary files on its bounded 16 MiB tmpfs and returns only the first 64 KiB per stream; this avoids unbounded in-memory capture. The workspace result remains capped at 200 files / 2 MiB.


## Follow-up increment — atomic multi-file commit and session lifecycle (2026-11-13)

- Added conversation-scoped `POST /api/v1/conversations/{conversation_id}/sessions/{run_id}/cancel`. It checks both conversation ownership and run ownership, then delegates cancellation to the existing durable worker RPC. No in-memory cancellation state is introduced.
- WebSocket and SSE replay cursors now reject malformed, negative, boolean-like or out-of-range values and are bounded to PostgreSQL `bigint`; run/session event query parameters have the same upper bound.
- Added forward-only migration `supabase/migrations/20261113120000_moreai_workspace_atomic_execution_commit.sql`. It creates a server-only idempotency ledger for workspace execution commits and an RPC that validates worker lease, run/user/workspace binding, active membership, private bucket, unique safe paths, expected versions, immutable Storage object existence and file limits. All file metadata updates and soft deletes execute in one PostgreSQL transaction. Existing version-history trigger archives overwritten versions; delete history is inserted in the same transaction.
- Worker RPC client now calls the atomic commit function. Workspace bridge uploads deterministic immutable object paths first, then submits the full changed/deleted set under a SHA-256 operation key. Retries return the previously committed result. Conflicts roll back the entire metadata batch rather than leaving a partially committed workspace.
- Storage objects uploaded before a failed metadata transaction may remain orphaned; a storage-object garbage collector is still required. The migration is committed but was not applied to Supabase.
- Source commits: `59c70b792f458fa07e06d0ef2c4fc55a3e954f4b`, `3678ff6d39c2a7890e84242e747de3d02924719a`, `cb0181fe1cb7032caf52250c8d7a8aba273978d5`, `eaae18f24fc0ccd0db5481e96d7f6bdd309050b8`, `7a49e3eaa8e1ee6fb58e9bb2adf3be838a993dba`, `b8a4b68e326a2f8e3da6462b1faf9bbc1955ee66`, `62721184ae397280a060a6ebaa45e6015b0b55b5`, `4b7983d2a73829be9893f62b09ad710263f658ee`.
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment or live Supabase migration/write were run. These are source changes only.
