# P1 Continuation Evidence — OpenFuse Runtime, Browser and OAuth Review — 2026-11-14

## Scope

- Main repository: `fadliansyah36/More-AI-Portal-Indihome`, branch `main`.
- OpenFuse pinned source: `CopilotKit/openfuse@7771e2db03a4b25d8bc8ee32f7a5c0dddafe3bfc`.
- Review type: static source review only. Full contents were fetched for the files listed as full review below. No source code was executed and no tests/builds/installations/staging/deployments or Supabase writes were performed.
- Upstream tree at the pin: 219 blob paths, recursive tree response not truncated. This is a source inventory count, not a count of files reviewed.

## Files fully reviewed in this increment

| Path | Blob SHA | Key disposition |
|---|---|---|
| `apps/server/src/computer-backend.ts` | `62933aaec6c2b0445b0a7ee0acc972f005ac3504` | Docker backend inspects container configuration, labels, owner/deployment identity, volume, mounts, network mode, capabilities, memory/CPU/PID limits, read-only rootfs and user. E2B backend delegates by metadata labels and uses a separate provider. Adapt only behind FastAPI tenant-bound owner identity. |
| `apps/server/src/computer-e2b-desktop.ts` | `fddbf72823c05638504fc5f59d4fa2dbad6d52ce` | E2B sandbox lifecycle, metadata ownership, template checks, paused/running lifecycle, idle timeouts, serialized cached handles, bounded command output/stdin, desktop actions and screenshots. Treat E2B as network-enabled; it does not inherit Docker's network-none posture. Require explicit policy, network egress restrictions, per-tenant quotas, secrets isolation and approval before production enablement. |
| `apps/server/src/computer.ts` | `e0e787ebb6d379d8d4a80e5159d1cc0a8672dd72` | Docker runner uses argv with `shell:false`, allowlisted inherited environment, timeout/abort and bounded output. Owner/deployment hashes scope container/volume labels. Workspace path validation rejects traversal. Service has leases/receipts and persistent state. Preserve the no-host-shell invariant; review lease persistence/atomicity against MoreAI's durable Supabase worker before porting. |
| `apps/server/src/browser.ts` | `0be1cd1c4ac30fc964f5eb874bb003b356fc8d6e` | Browser session ownership is stored per owner, IDs validated as UUID, operations serialized by session, worker calls use private bearer token, signed preview/console URLs and downloads are imported to owner-scoped Files. MoreAI must replace OpenFuse Store/auth with Supabase/FastAPI, bind session to tenant/principal, enforce idempotent import and short-lived signed URLs. |
| `apps/server/src/google-auth.ts` | `ae56eb481b6cab1a52b3994d59090156ba97e193` | OAuth state has expiry, PKCE verifier/challenge, one-time state take, generation/CAS protection, encrypted credentials, refresh-token handling and revoke flow. Port only with tenant-scoped Supabase records, KMS/secret encryption, callback allowlist, strict OAuth state ownership and consent-scoped permissions. |
| `apps/worker/src/downloads.ts` | `f290a072c1c1c17f975e2b6da23ae659d9da6cd9` | PDF-only import, 10 MiB cap, 20-download session limit, bounded metadata/failure journal, temporary/pending outcome and recovery. Preserve content sniffing, limits and failure receipts; add malware/content scanning and tenant storage policy at MoreAI boundary. |
| `apps/worker/src/network.ts` | `b824809a9404e752206eb15620731f1bf20c23e7` | URL validator permits HTTP(S) on 80/443, rejects credentials/local hostnames and non-public IP ranges, resolves all DNS answers and rejects mixed public/private results. Residual risk: DNS validation and subsequent browser navigation are not an atomic pin to the resolved address; browser-side rebinding/redirect behavior must be revalidated and egress enforced outside application code. |
| `apps/worker/src/proxy.ts` | `d4297573c2a277b0f413c590dde692b404af1171` | Egress proxy connects HTTP/CONNECT upstream sockets to validated IP addresses rather than doing a second DNS lookup, strips proxy auth headers and tracks sockets for shutdown. This is defense-in-depth, not a replacement for network namespace/firewall egress policy. |
| `packages/integrations/src/vault.ts` | `d36efce472df11916f23cd325084918c38439c78` | AES-256-GCM envelope, 32-byte base64 key validation, nonce/tag validation, version marker and AAD; legacy AAD is retained for compatibility. MoreAI should use managed key rotation/KMS envelope encryption and tenant-scoped access; never reuse a shared static key or expose it to clients. |
| `apps/worker/src/browser.ts` | `2f53e731f7c086a7799f767cdb036ece343a8235` | Browser contexts/profiles and session state are persistent; per-session serialized operations, URL validation on navigation/redirect, fixed page evaluation, constrained input, popup/dialog handling, bounded PDF download capture, idle sweeper and cleanup. Persisted browser state/cookies are sensitive credentials: tenant isolation, encryption, retention/deletion, egress control and human approval must be designed before activation. |

## Additional integration findings

1. **Docker vs E2B network posture:** Docker backend explicitly sets `--network none`, non-root user, read-only root filesystem, dropped capabilities, no-new-privileges, bounded memory/CPU/PIDs, no devices/host binds and one labeled workspace volume. E2B desktop reports `network: enabled`; do not treat the two providers as equivalent. E2B requires a separate egress/security policy and user consent.
2. **Shell boundary:** Docker host launches only the Docker executable with argv and `shell:false`. Commands execute inside the container. The E2B desktop command wrapper uses an in-sandbox shell intentionally; its command is still untrusted agent/user input and must remain in an isolated VM. Never expose host shell execution.
3. **Durability mismatch:** OpenFuse's owner-keyed Store and service leases are not MoreAI's canonical database or durable queue. Port command receipts, session ownership and lease semantics to Supabase-backed durable run/step/event records, with transaction-safe claims and cancellation. Do not import process-local Maps as the source of truth.
4. **Browser SSRF:** worker resolves DNS and the proxy pins upstream IP for proxy requests; direct browser navigation still requires enforced proxy-only egress and validation after redirects. Block cloud metadata, private IPv4/IPv6, loopback, link-local, reserved, internal DNS and non-HTTP protocols at network layer.
5. **OAuth write actions:** OpenFuse's Google integration can send mail and create/update/delete calendar events. These are high-impact side effects. MoreAI must require explicit user confirmation with a review snapshot, scoped OAuth permissions, immutable action receipt, idempotency/unknown-outcome handling and a fresh version/ETag check before mutation.
6. **Credential encryption:** AES-GCM envelope is a useful pattern, but a static environment key is not a full enterprise key lifecycle. Use KMS/HSM-backed envelope encryption, rotation, access audit and tenant authorization.
7. **Downloads:** imported PDFs are untrusted content. Keep size/type limits and add malware scanning, safe text extraction, quarantine and storage ACL before exposing them to RAG or model context.

## Review status boundary

- This increment adds 10 full-file reviews.
- Prior addendum `P1-OPENFUSE-SECURITY-REVIEW-ADDENDUM-20261114.md` records 5 full-file reviews and 2 partial reviews from its prior increment.
- Some paths overlap across increments; do not sum these counts as unique files without deduplication.
- The OpenFuse tree has 219 blobs. This work does not claim all 219 paths are reviewed. Remaining server routes, integrations, packages, worker support files, nested notices, build/config and assets still require path-by-path disposition.
- Exact-version package license coordinates remain unresolved; this report changes no SPDX `NOASSERTION` coordinate.
- Visual Skills and Scenario Skills are inventoried separately and are not closed by this report.

## P1 gate

**P1 remains OPEN.** Do not close the manifest or mark all content reviewed based on this increment. This review does not satisfy the exact-version dependency license gate, full OpenFuse path coverage, Visual Skills asset provenance, Scenario nested-file review, or zero-pending manifest gate.

## Next work

1. Continue remaining OpenFuse routes, integrations, packages, worker support files, Docker/E2B tests and configuration, then reconcile every one of the 219 upstream blob paths to the canonical manifest.
2. Resolve all 1,793 package@version `NOASSERTION` coordinates using immutable registry metadata/artifacts and retain evidence per exact version.
3. Complete Visual Skills provenance/rights for all 60 blob paths, especially provider logos/marks and third-party references; root license alone is not proof of third-party trademark permission.
4. Recursively inspect Scenario Skills' 2,114 blob paths, including linked scripts/assets/tests/metadata/nested licenses. The pinned recursive tree contains 2,114 blobs and is not truncated; this is not equivalent to a completed content review of all 179 skill entrypoints and their dependencies.
5. Update the final manifest only when each row has evidence-backed disposition; then publish a P1 closure report.

## Validation statement

No dependency install, script execution, build, lint, typecheck, tests, staging, deployment, or Supabase mutation was performed. This is static source review only.
