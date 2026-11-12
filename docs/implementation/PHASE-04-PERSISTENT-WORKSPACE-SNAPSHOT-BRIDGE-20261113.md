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
