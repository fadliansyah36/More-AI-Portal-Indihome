# Phase 04 — Browser supervisor hardening continuation
Date: 2026-11-11
Branch: main

## Scope and changes
- `apps/sandbox/app/browser_proxy.py`: cancellation now propagates instead of being swallowed as a proxy error response; upstream/client writer cleanup tolerates close-time socket errors.
- `apps/sandbox/app/browser_service.py`: browser action is constrained to the typed `navigate | extract` contract; per-action request count is capped at 200; non-HTTPS, malformed-host, credential-bearing, and over-budget requests are aborted; WebSocket channels are explicitly denied because they are not part of the approved action contract.
- Existing DNS-pinned CONNECT enforcement, public-IP rejection, domain allowlist, service authentication, isolated supervisor, download disablement, and browser-off-by-default gate remain in place.
- Existing SWE workspace implementation already has workspace-scoped paths, immutable version object paths, DB CAS reservation/commit, lease fencing, bounded UTF-8 file content and expired reservation recovery. This continuation did not add workspace list/read/delete/history APIs or Git/project operations.

## Commits
- `ac571bd3589ef09393ee7f94043986f2bdc573c6` — browser proxy cancellation and tunnel cleanup.
- `1735c5700db427b822648fdfad13b9655959a4fd` — browser request budget and WebSocket denial.

## Acceptance status
Phase 04 remains **IN PROGRESS — NOT ACCEPTED**. Source changes do not prove network isolation. The browser service still depends on deployment-level packet filtering that denies direct egress from the browser container and permits only the authenticated proxy. That policy has not been provisioned or verified; `MOREAI_BROWSER_EGRESS_ENFORCED` remains an operator assertion and must not be set to true without independent network evidence.

SWE still lacks complete OpenManus SWE parity: workspace listing, explicit file read, delete/tombstone, immutable version-history enumeration/restore, and project/Git workflow integration have not been completed. The current workspace CAS table stores only the current file pointer; immutable object paths alone do not provide a discoverable version-history index.

Remaining OpenManus Phase 04 parity also includes complete upstream Flow lifecycle adapters, session persistence and server/WebSocket API behavior, plus capability-by-capability reconciliation of all upstream backend tools/agents. No full parity claim is made.

## Verification and constraints
- No tests, lint, typecheck, build, browser runtime, network isolation, staging, provider calls, or deployment were run.
- No UI files were modified.
- No Supabase schema was changed in this increment.
- Browser and sandbox remain disabled unless all independent deployment security gates are satisfied.
