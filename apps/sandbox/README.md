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
