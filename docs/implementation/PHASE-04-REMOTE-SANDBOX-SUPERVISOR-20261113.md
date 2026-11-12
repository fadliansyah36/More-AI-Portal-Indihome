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


## Follow-up hardening — browser policy and runnable topology

- Fixed the undefined `blocked_navigation_hosts` reference in `apps/sandbox/app/browser_service.py`.
- Browser supervisor now loads the configured exact domain allowlist, rejects an unapproved initial host before navigation, and applies HTTPS/port/credential/domain checks to every intercepted subresource and the final navigation URL. The CONNECT proxy remains responsible for DNS resolution, public-IP enforcement and pinned upstream sockets.
- Added `apps/sandbox/compose.execution.yml`: private-only supervisor + Docker socket proxy on an internal network; worker is expected to attach to that private network without receiving the Docker socket.
- Socket-proxy image must be supplied as a digest-pinned reference. No floating tag is selected.
- Added `apps/sandbox/Dockerfile.runner`: minimal Python/Bash runner, UID/GID 65534, source passed over stdin.
- Documented the immutable runner image publication/digest requirement and the private Compose topology in `apps/sandbox/README.md`.
- Commits: `2c62bc79f808420926a7dc79206c72c52781e7b1`, `91fa8128462a72f5826061df5316cdf61fdf4285`, `7a681f504935a7c7278300849f627c6dcdbc2d4d`, `c3de455c0da2c06955dde3b3aea4e938fc8c1220`, `c507d6930f41f25ef463b8e4691ab6d2b60e11c7`.
- Not run: tests, lint, typecheck, build, Docker build, browser/API probes, staging, deployment or Supabase mutation. The execution and browser supervisors remain release-gated and have not been runtime-accepted.


## Follow-up hardening — daemon-side cancellation cleanup

- `apps/sandbox/app/runner.py` now records the Docker container ID with a per-invocation CID file.
- Timeout, cancellation, output-limit termination and normal completion all run a final cleanup path that requests daemon-side forced removal of the container. This closes the gap where killing the local Docker CLI process alone could leave the daemon-managed container running.
- The cleanup uses the same restricted supervisor-only Docker API path; it does not grant Docker access to the worker.
- Commits: `b32cb13e97c855872f44b001b607b2b0d60452e7`, `2b45715f89f647d4194e1e76ecc5506b59a9db3b`.
- This is source-level hardening only. No Docker daemon, runtime or test was invoked.


## Follow-up — agent exception taxonomy and worker persistence

- Added `AgentExecutionError` with validated stable error codes and an explicit retryable flag in `engine/agents/errors.py`.
- Added a conservative classifier at the dispatcher boundary:
  - permission failures → `agent_action_not_permitted`;
  - unavailable capabilities → `agent_capability_unavailable`;
  - invalid request/tool contracts → `agent_request_invalid`;
  - timeouts → `agent_execution_timeout` (retryable);
  - unknown implementation faults → `agent_internal_error` (not automatically retryable).
- Worker runtime persists the safe classification code and retryability metadata in the durable `run.failed` event and terminal error payload; it never persists raw exception messages, prompts or provider payloads.
- Commits: `df7adb4e4635517e1d3d9e30be2e6643bc6c41bd`, `f389b12ad4a490b15588be0c5f044c6fd9c63569`, `a61c0eb130d69b3facdea0fc0bad2a0e258843ac`.

## Remaining Phase 04 gaps
- Workspace metadata and file tools are scoped through `AgentRunContext.workspace_id` and lease-fenced workspace RPCs. However, a persistent filesystem view is not mounted into the isolated Python/Bash runner; file operations remain mediated through workspace tools. Do not claim shell-level workspace parity until a safe, ephemeral workspace bridge is implemented.
- Complete upstream server/session parity and browser download scanning remain open.
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment or Supabase mutation were performed.


## Approval and provider failure classification correction

- Dispatcher explicitly preserves `RunPausedForApproval` as durable control flow. It must reach `WorkerRuntime` unchanged so the already-committed approval pause is not misreported as an execution failure.
- Added explicit upstream failure classes: HTTP timeout and transport errors are retryable; HTTP 429/5xx are retryable; non-transient HTTP status errors are classified as rejected requests. No response body, provider message or credential is copied into the durable error.
- Commits: `96388b5cbd9d898c35012240f307ba9fb976429d`, `bdaf4b2c3809acb2c22bc3d26e6ed63780e57b65`.


## Follow-up — browser download denial

- Browser contexts remain configured with `accept_downloads=False`; the page now also registers an explicit download event handler and calls `Download.cancel()` for every download event.
- Browser action responses expose a `blocked_downloads` count for navigation and extraction, so callers can distinguish a page that attempted a download from a normal page interaction.
- Downloaded files are not persisted to the supervisor filesystem or returned as artifacts. A future controlled-download feature must introduce malware/content scanning, MIME and size policy, quarantine storage, tenant-scoped artifact ownership and audit before enabling any download acceptance.
- Commit: `845b9e7d5ae5cff9676b06218324126fbaa6eca4`.
- Workspace limitation remains: workspace read/edit tools are backed by versioned Supabase Storage and metadata, but the Python/Bash runner still receives only source text and has no workspace filesystem snapshot or write-back bridge. Shell-level workspace parity remains blocked; this increment does not claim it.
- No tests, lint, typecheck, build, browser/API probes, Docker build, staging, deployment or Supabase mutation were performed.
