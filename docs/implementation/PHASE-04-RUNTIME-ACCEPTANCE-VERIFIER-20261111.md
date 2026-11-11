# Phase 04 — Runtime acceptance verifier added
Date: 2026-11-11
Branch: main

## New operator verifier
Added `apps/sandbox/scripts/verify-browser-network-isolation.sh` (commits `8b1093cdc29765385883e79598137340ea66f52a`, `4eebf0984a5362e39f34b98865cd02844edc6f14`).

Run on the Docker deployment host after bringing up the isolated topology:
```bash
docker compose -f apps/sandbox/docker-compose.browser.yml up -d --build
bash apps/sandbox/scripts/verify-browser-network-isolation.sh
```

The script checks browser-only private network attachment, proxy bridge topology, Docker internal network, blocked direct public IPv4/IPv6 TCP egress, successful allowlisted HTTPS through the authenticated proxy, rejected loopback/metadata/unlisted targets, and non-privileged/non-host-network mode.

The verifier returns nonzero if controls cannot be demonstrated and does not print tokens. It has NOT been executed.

## Runtime status
No authorized Docker host/runtime execution tool for the MoreAI sandbox deployment is available in this session. Source and Compose declarations are not runtime proof. DNS-rebinding and redirect/subresource bypass tests still require deployment-host execution and controlled DNS fixtures before browser activation.

## Remaining Phase 04 blockers
SWE list/read/delete/version-history/restore/Git API surface and complete OpenManus Flow/session/server/WebSocket/backend capability parity remain incomplete. No Phase 07 work has begun.

## Verification boundary
No Docker build/up, test suite, network probes, provider call, staging or deployment was performed. The previously stated restriction against tests/build/lint/typecheck/deployment remains respected.
