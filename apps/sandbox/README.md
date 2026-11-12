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

For a Docker deployment where the worker and browser supervisor share the same private Docker network:

- `MOREAI_BROWSER_ENABLED=true`
- `MOREAI_BROWSER_SERVICE_URL=http://browser-supervisor:8080`
- `MOREAI_BROWSER_SERVICE_TOKEN=<same service token>`
- `MOREAI_BROWSER_EGRESS_ENFORCED=true`
- `MOREAI_BROWSER_PRIVATE_NETWORK_HTTP=true`

The HTTP exception is deliberately exact: only hostname `browser-supervisor`, port `8080`, without credentials, query, or fragment. Never set this flag for a public or shared network.

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
