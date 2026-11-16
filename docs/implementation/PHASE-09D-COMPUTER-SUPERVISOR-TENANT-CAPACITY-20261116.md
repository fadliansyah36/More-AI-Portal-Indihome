# Phase 09D — Computer Supervisor Tenant Capacity Hardening

Date: 2026-11-16  
Branch: `main`  
Repository: `fadliansyah36/More-AI-Portal-Indihome`

## Scope and baseline

Source-only continuation of the isolated Python/Bash execution supervisor. Baseline was the `main` branch after the Phase 09A provider-secret routing increment. `AGENTS.md` was read before implementation. No customer UI files were changed; this increment addresses a missing per-customer resource boundary in the existing disposable execution service.

## Implemented

File: `apps/sandbox/app/execution_supervisor.py`

- Active execution handles are keyed by `(user_id, run_id, request_id)` rather than request ID alone.
- Cancellation resolves the complete tenant/run/request identity, preventing a colliding request ID from cancelling another customer's active execution.
- Added atomic admission limits guarded by an async lock: `MOREAI_SANDBOX_MAX_ACTIVE_PER_CUSTOMER` defaults to 2 (range 1–8); `MOREAI_SANDBOX_MAX_ACTIVE_GLOBAL` defaults to 16 (range per-customer limit–64).
- Capacity is checked before container execution and rechecked under the lock before registering the task. Over-capacity requests receive HTTP 429; invalid configuration fails closed with HTTP 503.
- Existing digest-pinned, network-disabled, disposable Docker runner and durable FastAPI/Supabase receipt/workspace pipeline are unchanged.

File: `apps/sandbox/README.md`

- Documented capacity settings, tenant-scoped cancellation semantics, process-local scope and the requirement for consistent routing or a shared admission coordinator in multi-replica deployments.

## Security and architecture notes

This is a tenant-aware concurrency boundary, not a complete persistent Computer/Desktop supervisor. The active-handle map is process-local and is not a durable queue. Durable receipts remain owned by FastAPI/Supabase. Multi-replica global/customer quotas are not guaranteed until sticky per-customer routing or a shared coordinator is deployed. No persistent desktop/VNC session, per-customer filesystem volume, desktop lifecycle API, or production host is provisioned by this change.

## Supabase / FastAPI / UI

- No schema or migration changes.
- No FastAPI endpoint changes.
- No frontend route/component changes; existing customer UI and design system remain untouched.
- Existing worker action receipt and canonical workspace snapshot/write-back contracts remain the source of truth.

## Verification and deployment

Per owner instruction, no tests, build, lint, typecheck, browser/API/worker execution, Docker execution, provider calls, staging or deployment were performed. Screenshots were not captured because no UI files changed. The source implementation is not runtime-verified. Sandbox runtime flags remain disabled until the isolated supervisor deployment/security gate is accepted.

## Commit

- `b87752af392de541bd65dd0237bda0d632b91d91` — `fix(sandbox): enforce per-customer execution capacity`
- `f5b42a2cb0021f0d7963e46446aafbceb9d6a58d` — `docs(sandbox): document tenant-scoped execution capacity`

## Remaining blockers / next work

1. Complete a dedicated persistent per-customer Computer/Desktop supervisor with isolated lifecycle, resource budgets, storage, access policy and audit; do not mount OpenFuse shared-key/E2B service directly.
2. Add shared admission coordination or per-customer supervisor sharding before multi-replica operation.
3. Connect persistent worker and supervisor hosts, immutable image digests, restricted Docker socket proxy, private networking and secret manager.
4. Continue Phase 09C action-to-screen reconciliation and AI Skills governance inventory/license/SBOM/reviewer workflow.
5. Phase 10 verification remains NOT ACCEPTED; Phase 11 remains BLOCKED.
