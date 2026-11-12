# Phase 04 — Remote Sandbox Supervisor Integration (2026-11-13)

## Scope and source range
- Phase: 04 — Full Backend Integration & Security Hardening.
- Branch: `main`.
- Baseline HEAD: `9ea16f90bccd406d4ea799ba091817c46168c8e2`.
- Latest implementation commit in this increment: `068553a012b95412fd39a3e83d38b96684a74262`.
- User constraints: no real testing, staging, deployment, or production database changes.

## Implemented
- Added `apps/sandbox/app/execution_supervisor.py`, a separate authenticated FastAPI service for Python/Bash execution.
- Added `apps/sandbox/Dockerfile.execution` as the execution-supervisor image entrypoint.
- Replaced the worker's in-process Docker CLI adapter with an authenticated HTTP client in `apps/worker/app/sandbox_tools.py`. The worker no longer needs a Docker socket or direct Docker CLI access.
- Added authenticated readiness checks requiring the supervisor, isolated runner, network-disabled mode, digest-pinned image, and a reachable Docker daemon/socket proxy (`docker info`) before the supervisor reports ready.
- Wired supervisor construction and readiness preflight into `apps/worker/app/main.py`; the worker refuses to start claiming work when sandbox flags are enabled but the supervisor is unavailable.
- Wired the same adapter into `build_agent_registry` and `RegisteredAgentDispatcher`. SWE dispatch explicitly fails closed without a supervisor; each sandbox invocation rechecks readiness.
- Added run-scoped execution request identifiers and cancellation endpoint. Worker cancellation is propagated to the supervisor; the runner's cancellation cleanup terminates its Docker CLI process group. The readiness endpoint now checks the actual daemon/socket-proxy connection instead of only validating image configuration.
- Updated `apps/sandbox/README.md` with private topology, worker configuration, token handling and deployment gates.

## Security and compatibility decisions
- Python/Bash remain disabled unless both `MOREAI_SANDBOX_ENABLED=true` and `MOREAI_SANDBOX_RELEASE_GATE_PASSED=true` are explicitly configured.
- The supervisor only accepts HTTPS or the exact private Compose endpoint `http://execution-supervisor:8080` when the private-network flag is enabled.
- The runner continues to use a digest-pinned image, non-root execution identity, no network, read-only root, dropped Linux capabilities, bounded resources/output and a hard timeout.
- No browser UI or Customer UI files were changed.
- No Docker socket is introduced into the worker. The separate supervisor deployment still requires a restricted Docker socket proxy and private networking; unrestricted Docker socket exposure is not acceptable.

## Not performed / limitations
- No tests, lint, typecheck, build, browser/API probes, Docker build, migration, Supabase write, staging or deployment were run, per instruction.
- The execution supervisor has source code and a Dockerfile but is not deployed or runtime-accepted.
- A restricted Docker socket proxy, private service network and runtime deployment configuration remain infrastructure prerequisites.
- This increment does not complete all Phase 04 parity: upstream server/session lifecycle, full workspace execution mount semantics, browser download scanning and complete exception taxonomy remain open.
- Tool activation remains fail-closed. Do not set either sandbox activation flag until infrastructure security acceptance is separately authorized and complete.

## Next implementation
Continue Phase 04: finish OpenManus server/session and agent lifecycle parity, workspace lifecycle/runner binding, exception taxonomy and browser supervisor controls. Then proceed to Phase 06 route-wide schemas/auth/idempotency/OpenAPI, Phase 07 durable lifecycle, Phase 08 full AI runtime and Phase 09 existing Customer Dashboard integration.
