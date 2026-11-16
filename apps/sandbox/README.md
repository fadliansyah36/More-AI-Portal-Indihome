# MoreAI Browser Supervisor — Private Egress Runtime

The browser supervisor is deliberately disabled by default. Do not enable it until the deployment has a private worker-to-supervisor path and the Docker acceptance gate passes.

## Topology

- `browser-supervisor`: Chromium/Playwright, attached only to `browser_isolated` (Docker `internal: true`).
- `browser-egress-proxy`: authenticated HTTP CONNECT proxy, attached to `browser_isolated` and `browser_egress`.
- Worker: may join `browser_isolated` to call the supervisor and must retain its own separate egress path for Supabase/provider traffic. Do not attach the browser container to the worker's egress network.
- The browser container has no published host port. The proxy is the only container bridging isolated and egress networks.

## Local/CI acceptance

Set unique 32+ character tokens and an exact domain allowlist, then run:

```bash
export MOREAI_BROWSER_ALLOWED_DOMAINS=example.com
export MOREAI_BROWSER_SERVICE_TOKEN='<32+ chars>'
export MOREAI_BROWSER_PROXY_TOKEN='<32+ chars>'
export MOREAI_BROWSER_EGRESS_ENFORCED=true

docker compose -f apps/sandbox/compose.browser.yml build
docker compose -f apps/sandbox/compose.browser.yml up -d
bash apps/sandbox/scripts/verify-browser-network-isolation.sh
docker compose -f apps/sandbox/compose.browser.yml down --volumes --remove-orphans
```

The verifier checks container network membership, Docker internal-network enforcement, direct IPv4/IPv6 denial, authenticated supervisor readiness, actual Playwright navigation through the allowlisted proxy, redirect denial for a non-allowlisted host, download denial while scanner-backed downloads are disabled, and a DNS-rebinding public-to-loopback case against the proxy guard.

The GitHub Actions workflow additionally builds the worker image and runs its `BrowserSupervisor.check_ready()` client from a container attached to the private `browser_isolated` network. This proves the worker-side client contract and private DNS connectivity, not a production worker deployment.

## Worker connection settings

For the canonical Compose deployment, the pinned OpenFuse Node worker is exposed only on the private `browser_isolated` network:

- `MOREAI_BROWSER_ENABLED=true`
- `MOREAI_BROWSER_SERVICE_URL=http://browser-supervisor:8790`
- `MOREAI_BROWSER_SERVICE_TOKEN=<same 32+ character WORKER_TOKEN>`
- `MOREAI_CLAMAV_HOST=clamav`
- `MOREAI_CLAMAV_PORT=3310`
- `MOREAI_BROWSER_SERVICE_TOKEN=<same service token>`
- `MOREAI_BROWSER_EGRESS_ENFORCED=true`
- `MOREAI_BROWSER_PRIVATE_NETWORK_HTTP=true`

The HTTP exception is deliberately exact: only hostname `browser-supervisor`, port `8790`, without credentials, query, or fragment. Never set this flag for a public or shared network.

For a deployment platform with private HTTPS service discovery, use its HTTPS service URL and leave `MOREAI_BROWSER_PRIVATE_NETWORK_HTTP=false`. Do not publish the supervisor to the public internet.

The worker checks authenticated `/ready` on startup when browser tools are enabled. The check requires the egress proxy to be configured, enforced, and reachable. A missing/degraded proxy prevents worker startup rather than silently falling back to direct browser egress.

## Download policy

Downloads remain denied (`accept_downloads=false`) until a scanner-backed download flow exists and can prove size, type, malware verdict, tenant-scoped storage path, and immutable metadata. Do not enable downloads by changing Playwright's `accept_downloads` flag alone.

## Operational gate

- Browser supervisor is not production-enabled by this documentation.
- Do not enable `MOREAI_BROWSER_ENABLED` on a worker until the private network is attached and the Docker acceptance workflow is green.
- Keep the browser tool behind the release gate until redirect, subresource, DNS pinning, download, and tenant-isolation tests pass on the target deployment platform.


## Isolated Python/Bash execution supervisor

Python and Bash execution use a separate authenticated service; the worker must not receive a Docker socket or invoke the Docker CLI locally.

- Service entrypoint: `apps.sandbox.app.execution_supervisor:app`
- Image definition: `apps/sandbox/Dockerfile.execution`
- The supervisor accepts only authenticated worker requests, requires a digest-pinned runner image, and executes each request with network disabled, read-only root filesystem, non-root runner identity, dropped capabilities, bounded CPU/memory/PIDs/output and a hard timeout.
- The execution service must be reachable only from the private worker network. Do not publish port 8080 publicly.
- The Docker daemon endpoint must be exposed to this trusted service through a restricted Docker socket proxy with only the container lifecycle operations required by the runner. Do not mount an unrestricted host Docker socket into the worker or browser container.
- The supervisor service token must be unique, at least 32 characters, stored as a server-side secret, and never included in browser configuration.

Worker settings (only after the deployment security gate is accepted):

- `MOREAI_SANDBOX_ENABLED=true`
- `MOREAI_SANDBOX_RELEASE_GATE_PASSED=true`
- `MOREAI_SANDBOX_SERVICE_URL=https://<private-supervisor-host>` or exact private Compose URL `http://execution-supervisor:8080`
- `MOREAI_SANDBOX_SERVICE_TOKEN=<32+ character secret>`
- `MOREAI_SANDBOX_PRIVATE_NETWORK_HTTP=true` only for the exact private Compose hostname above
- `MOREAI_SANDBOX_IMAGE=<runner-image>@sha256:<64-hex-digest>` is configured on the supervisor, not in the browser bundle.

The worker checks authenticated `/ready` before it starts claiming work. The dispatcher also requires the supervisor for the SWE agent, and the adapter re-checks readiness before each execution. Any missing, invalid or degraded supervisor fails closed; there is no local Docker fallback.

This source integration does not deploy the supervisor, provision its private network/socket proxy, or authorize enabling either runtime flag. Those remain release-gated.

Supervisor service environment:

- `MOREAI_SANDBOX_SUPERVISOR_ENABLED=true`
- `MOREAI_SANDBOX_SERVICE_TOKEN=<same 32+ character worker token>`
- `MOREAI_SANDBOX_IMAGE=<runner-image>@sha256:<64-hex-digest>`
- `DOCKER_HOST=<restricted Docker socket proxy endpoint>`

The supervisor readiness endpoint runs `docker info` through the configured daemon/socket proxy and will not report ready when that boundary is unavailable. The socket proxy must deny privileged/container-host operations and expose only the container lifecycle API needed by the runner. A raw unrestricted Docker daemon socket is not an acceptable production configuration.


## Execution supervisor Compose topology

A private Compose topology is defined in `compose.execution.yml`:

- `execution-supervisor` is private-only and exposes no host port.
- `execution-docker-proxy` is the only service attached to the host Docker socket; the worker never receives the socket.
- The proxy is not published and is attached only to the internal `moreai_execution_private` network.
- Set `DOCKER_SOCKET_PROXY_IMAGE` to an immutable image reference ending in `@sha256:<64-hex-digest>`; do not use a floating tag.
- Build the minimal runner from `Dockerfile.runner`, publish it to the trusted image registry, resolve its immutable digest, and pass that digest as `MOREAI_SANDBOX_IMAGE`. The runner contains Python and Bash, runs as UID/GID 65534, and receives source only through stdin.
- Attach the worker to `moreai_execution_private` while preserving its independent outbound path for Supabase and configured model providers. Configure the exact private URL `http://execution-supervisor:8080` only on that isolated network.

The socket proxy exposes only the Docker API categories needed for container lifecycle, image inspection and daemon readiness. Because the Docker create API is powerful, the supervisor remains a trusted security boundary: only this service may possess the proxy token; it must validate every request and construct fixed runner arguments. Never expose the proxy or supervisor to the public internet, and never grant the worker direct Docker API access.

No runner image digest, socket-proxy digest, deployment, or readiness result is asserted by this source change. The runtime remains fail-closed until the immutable images and private infrastructure are provisioned and accepted.


## Ephemeral workspace snapshot bridge

When the independently gated Python/Bash tools are enabled, the worker now:

1. Resolves the run workspace_id and authenticated user from the durable run context (never from tool arguments).
2. Lists only active workspace files, then rechecks workspace membership and metadata through the owner/member-scoped workspace RPC.
3. Downloads each immutable Storage object and verifies its byte length and SHA-256 before creating a bounded snapshot (maximum 200 files / 2 MiB).
4. Sends the snapshot over the authenticated private supervisor request. The runner materializes it only under its disposable /tmp/workspace tmpfs, with no host mounts and no network.
5. Rejects symlink paths and returns a bounded file snapshot. Only a successful, non-timeout execution is eligible for write-back.
6. Compares the original workspace version/hash before writing. Changed/new files are uploaded to new immutable object paths and committed through the existing worker-lease-fenced CAS RPC; deleted files use the existing soft-delete RPC. A stale version or lost lease prevents that file's commit.

The current write-back uploads immutable Storage objects first, then commits all changed/new/deleted file metadata in one lease-fenced PostgreSQL RPC transaction. A version conflict or invalid path rolls back the complete metadata batch; no subset of the workspace metadata is committed. Storage objects uploaded before a failed metadata transaction can remain orphaned and require a later garbage-collection pass. The RPC is idempotent per run and deterministic operation key, so retry after a lost response returns the prior committed result. Failed/timed-out commands discard their ephemeral changes. Deleted workspace paths cannot be recreated implicitly; use the explicit restore flow. Snapshot limits are intentionally conservative and can be raised only with a coordinated API, supervisor, runner and Storage policy change.

This is a source-level implementation. Sandbox remains disabled unless both runtime and release-gate flags are enabled, and no deployment/runtime acceptance is implied.

## Per-customer execution capacity

The execution supervisor now keys live cancellation handles by the complete `(user_id, run_id, request_id)` tuple rather than request ID alone. This prevents one tenant's cancellation request from addressing another tenant's active execution even if request identifiers collide.

Admission control is enforced atomically under a process-local lock:
- `MOREAI_SANDBOX_MAX_ACTIVE_PER_CUSTOMER` defaults to `2` and accepts `1..8`.
- `MOREAI_SANDBOX_MAX_ACTIVE_GLOBAL` defaults to `16` and accepts a value from the per-customer limit through `64`.
- Requests exceeding either budget receive HTTP `429`; malformed capacity configuration fails closed with HTTP `503`.
- Limits are enforced before starting a container and rechecked under the lock to prevent concurrent admission races.

These limits are per supervisor process. A multi-replica deployment must route a customer's executions consistently to one supervisor shard or add a shared admission coordinator before claiming a global cross-replica quota. Durable action receipts remain in FastAPI/Supabase; the in-memory map is not a durable job queue. This is source hardening, not proof of a deployed per-customer desktop supervisor.

### Container-level tenant audit labels

Every disposable runner container now receives one-way SHA-256 labels for the authenticated customer ID, Agent Run ID and request ID. Raw identifiers are not copied into Docker metadata. These labels support restricted daemon-side inventory/audit and incident correlation while the container is alive; the runner still receives no tenant credential and no network access. Labels are passed as fixed Docker CLI arguments and do not alter the canonical durable receipt or workspace state.


## Canonical OpenFuse Compose topology

- `apps/sandbox/Dockerfile.openfuse` builds the pinned upstream OpenFuse worker commit `7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`, applies the MoreAI profile-delete patch and the MoreAI private-egress proxy override.
- The browser worker is attached only to `browser_isolated` (Docker `internal: true`) and stores profiles under the named `openfuse_browser_profiles` volume mounted at `/data/browser-profiles`. Worker restart preserves the profile metadata and Chromium profile directory; the same UUID is reopened by the MoreAI adapter. The worker closes idle Chromium contexts after 10 minutes but retains the profile; the shared database admission lease lasts 11 minutes, so another replica cannot take the same profile while the previous context is expected to be active.
- The worker's loopback proxy forwards HTTPS CONNECT only to `browser-egress-proxy:3128`. Plain HTTP is denied. The egress proxy is the only browser network component attached to the public bridge and validates allowlisted domains, resolves public addresses and pins the upstream socket.
- A ClamAV service is attached to the private network and public bridge only for signature updates. Set `MOREAI_CLAMAV_IMAGE` to an immutable digest-pinned image before Compose startup. The browser worker fails readiness when clamd is unavailable; download bytes are imported into private MoreAI artifacts only after a clean ClamAV verdict and signature/hash checks.
- `openfuse_browser_profiles` and `clamav_db` are persistent named volumes. Protect the Docker host/volume with encrypted storage and restrict operator access; deleting the profile volume deletes saved login state.
- No port is published to the host. The worker token and proxy token are server-side secrets only.

Start from the repository root:

```sh
docker compose -f apps/sandbox/compose.browser.yml up --build -d
```

The stack definition is source-only until an authorized deployment host supplies digest-pinned ClamAV image, tokens, exact domain allowlist and persistent encrypted volume. Do not set the worker release gate before those host controls are in place.


The OpenFuse worker adapter imports only PDFs that have passed the ClamAV `INSTREAM` scan. It then sends the bytes, SHA-256 digest, filename, session UUID and clean verdict to the authenticated FastAPI `/api/v1/artifacts/internal/browser-download` endpoint. FastAPI rechecks run ownership, session ownership/status, content signature, MIME, size, checksum and private bucket status before writing artifact metadata. Scanner or storage errors remain visible as per-file failures; no unscanned bytes are imported.
