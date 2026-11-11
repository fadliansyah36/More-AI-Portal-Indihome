# Phase 04 — Browser network isolation deployment boundary
Date: 2026-11-11
Branch: main

## Implemented
Added a reproducible two-network Docker Compose topology:
- `browser-supervisor` attaches only to `browser_private`, an internal Docker network with no external routing.
- `egress-proxy` attaches to both `browser_private` and `browser_egress`; it is the only browser-network member with external routing.
- The proxy is a CONNECT-only server using `BrowserRequestGuard`, DNS pinning, public-address validation, per-host pin consistency, TLS hostname verification by browser, and explicit domain allowlisting.
- Browser supervisor points Chromium at the proxy, disables QUIC and downloads, blocks service workers and WebSockets, and caps intercepted requests.
- Added dedicated browser/proxy images and pinned Playwright version in `apps/sandbox/requirements-browser.txt`.

## Commits
- `16db80a9d9d7a5d1488de9cb2aece9afade0993a` proxy entrypoint
- `57f7428ca87445b0fab985952e21c2db19a2e1b6` browser image
- `ea26636acbc0d599db52873890c0e8f1ead77eb3` browser dependencies
- `5dc2f8753b32741458f6417472114703cd757045` isolated two-network Compose topology
- `13ca010e0fc08f17aaffd520003e9ef636126081` proxy image

## Important limitation
This creates a deployable isolation topology in source; it does NOT establish that it is running in the target environment. No Docker daemon, host firewall, deployment runtime, or browser container was available through this repository connector. The `MOREAI_BROWSER_EGRESS_ENFORCED` value in Compose is only a service startup gate, not independent proof. Do not activate the worker browser capability until deployment evidence demonstrates:
1. browser container has no default/external route;
2. proxy container can reach public allowlisted hosts;
3. browser can reach allowlisted public hosts through proxy;
4. browser direct TCP/UDP egress attempts fail (including IPv4 and IPv6);
5. private, loopback, link-local, metadata, reserved, unlisted, non-443, redirect and DNS-rebinding attempts fail;
6. browser-originated DNS and QUIC cannot bypass the proxy.

## Acceptance matrix (current)
| Capability | Source implementation | Runtime evidence | Status |
|---|---|---|---|
| Browser proxy CONNECT auth | Yes | Not run | Pending |
| Browser DNS pinning/public IP validation | Yes | Not run | Pending |
| Browser direct-egress isolation topology | Compose added | Not deployed/verified | Pending |
| Redirect/subresource egress via proxy | Browser proxy configured | Not run | Pending |
| Download safety | Downloads disabled | Not run | Pending |
| SWE CAS/version write | Existing worker + RPC | Not run | Partial |
| SWE list/read/delete/version history/restore | Not implemented end-to-end | None | Blocked |
| SWE Git/project workflows | Not implemented | None | Blocked |
| Durable Flow parity | Planning adapter only | Not run | Partial |
| Session/server/WebSocket parity | Not implemented as complete adapters | None | Blocked |
| All OpenManus backend tools/agents | Catalog + selective adapters | Not all adapters registered | Partial |

## Security evidence policy
Never infer a passing control from a feature flag, Docker Compose declaration, source-code presence, or a health endpoint. Required runtime evidence must include container network inspection, route table, iptables/nftables policy, packet-level negative egress attempts, proxy access logs and request correlation IDs. Retain test timestamp, image digest, config hash, and operator identity in the release evidence.

## Verification performed
Repository source and dependency wiring were inspected. No Docker build/up, tests, browser execution, network probes, staging, provider calls, or deployment were run. Therefore Phase 04 remains **IN PROGRESS — NOT ACCEPTED**.
