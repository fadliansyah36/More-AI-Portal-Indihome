# MoreAI — Browser Supervisor & Persistent SWE Workspace Implementation Increment
Date: 2026-11-11
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`

## Implemented and committed

### 1. Persistent SWE workspace
- Added `engine/tools/workspace.py` with `SupabaseWorkspaceTool`.
- Workspace objects are stored in the private `moreai-artifacts` bucket under `{user_id}/workspaces/{workspace_id}/{path}`.
- The editor requires a non-empty workspace ID from the durable run context; it does not fall back to a global/shared workspace.
- The adapter verifies the bucket exists and is private before each operation.
- Path traversal, absolute paths, backslashes, NUL bytes and unsupported path characters are rejected.
- File reads are capped at 2 MiB and UTF-8 only. Writes are capped at 2 MiB.
- Existing-file edits require exactly one old-text match; create operations cannot silently overwrite existing objects.
- Output includes byte size and SHA-256.

### 2. Worker/tool registry integration
- Added `str_replace_editor` handler registration to `DurableOpenManusRuntime` when the workspace adapter is configured.
- Passed the run's `workspace_id` through the tool registry to the workspace adapter.
- The upstream tool catalog already defined `str_replace_editor`; its existing JSON contract and policy enforcement remain authoritative.
- Missing workspace ID fails closed. No local ephemeral directory is represented as persistent workspace.

### 3. Browser egress proxy
- Added `PinnedConnectProxy` with authenticated HTTP CONNECT only.
- Proxy validates CONNECT authority against the configured domain allowlist, resolves DNS through `BrowserRequestGuard`, rejects non-public IPs and DNS rebinding, connects to the pinned IP directly, and checks the actual peer address.
- HTTPS remains end-to-end between Chromium and destination; redirects/subresources/WebSockets create their own CONNECT request and must pass the proxy policy again.
- Proxy supports a dedicated entrypoint `apps/sandbox/app/proxy_main.py`, configured by a strict domain allowlist and a 32+ character secret.

### 4. Isolated browser supervisor service
- Added `apps/sandbox/app/browser_service.py` as a separate FastAPI service.
- Service accepts only authenticated browser action requests; only HTTPS URLs and navigate/extract actions are accepted.
- Chromium runs with an authenticated proxy, QUIC disabled, service workers blocked, downloads disabled, certificate verification enabled and a request scheme guard.
- Added worker-side HTTP adapter `BrowserSupervisor`; browser execution no longer runs inside the general-purpose worker process.
- Registered `browser_use` in the durable tool registry only when explicit browser enablement, isolated service URL/token and the egress-enforcement flag are present.
- Browser dependency set is optional and isolated in the sandbox workspace.

## Security gates / what remains blocked
- `MOREAI_BROWSER_EGRESS_ENFORCED=true` is a deployment assertion, not proof. The actual browser container/network namespace must have outbound access denied except to the authenticated proxy. That network policy has not been provisioned or verified in this increment.
- The browser service readiness endpoint reports configuration, not an end-to-end network firewall attestation. Browser stays disabled unless deployment supplies the required flags; production must not set the egress flag until firewall/network policy is applied and verified.
- The proxy CONNECT tunnel does not inspect decrypted HTTP response bodies. It enforces destination IP/domain at each tunnel, but content-type/size malware scanning for downloads is not implemented; downloads are therefore disabled.
- Browser action surface is deliberately limited to navigate/extract; click/type and browser download APIs remain unavailable until a selector/action contract and safety controls are implemented.
- Proxy host allowlist must include all required top-level and subresource domains. Do not use wildcard public domains.
- SWE workspace writes are persistent in Storage but are not yet guarded by a database-backed per-file lease/CAS transaction. Concurrent edits to the same path can race; serialize edits per workspace/path before enabling concurrent SWE agents.
- Workspace read/list/delete/version history, project Git operations, and full upstream SWE runtime parity remain open.
- No browser tool is enabled by default. No browser or SWE runtime test, network test, build, lint, typecheck, E2E or deployment was performed.

## Key commits
- `07064ae` persistent SWE workspace Storage adapter
- `8fae0bf` authenticated DNS-pinned CONNECT proxy
- `df42e6c` workspace editor tool-registry contract
- `dcb4731` workspace ID propagation and runtime registration
- `e3cec95` worker registry workspace integration
- `f105bf9` browser proxy Basic authentication compatibility
- `d5ca47f` browser supervisor adapter
- `771d685` browser tool contract narrowed to implemented actions
- `870aca2` browser tool registration in durable runtime
- `b4ea13f` worker gated browser integration
- `cfeb771` browser proxy service entrypoint
- `96b3c63` isolated browser supervisor service API
- `124ff3a` worker-to-isolated-browser-service adapter
- `c90adb5` worker browser service integration
- `78f7ce7` workspace path and overwrite hardening

## Next implementation
1. Add and verify deployment network policy so browser containers cannot egress except through the proxy; only then allow browser flag.
2. Add database-backed workspace path leases/CAS and workspace list/read/delete/version APIs.
3. Implement durable event outbox and monotonic per-run event sequence, including tool progress and cancellation publication/replay.
4. Reconcile full upstream Flow/server/session and remaining tool adapters against the pinned vendor snapshot.
5. Continue remaining Partner/Wi-Fi/Captive Portal/Voucher/Analytics APIs and transactional Super Admin governance.
6. Wire existing UI only after baseline/after screenshots satisfy AGENTS.md.
7. Run Phase 10–11 only after explicit test/release authorization.
