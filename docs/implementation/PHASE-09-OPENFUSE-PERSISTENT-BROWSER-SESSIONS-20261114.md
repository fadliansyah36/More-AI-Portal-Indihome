# Phase 09 Continuation — Persistent OpenFuse Browser Session Lifecycle

Date: 2026-11-14  
Branch: `main`  
Status: **SOURCE IMPLEMENTED — RUNTIME NOT VERIFIED; PHASE 09 IN PROGRESS**

## Implemented

- Added `moreai_browser_sessions` and immutable lifecycle event rows in a forward-only migration. Rows are owner-bound to Auth users and Agent Runs; service-role only, RLS enabled, no direct client table grants.
- Added FastAPI customer endpoints to list active sessions and close an owned session. Browser state is never returned to the customer API.
- Added worker-internal acquire/restore and state-save endpoints. They require the existing worker internal token and a matching active Agent Run/user pair.
- Browser state is encrypted at rest using Fernet with the deployment secret `MOREAI_BROWSER_SESSION_ENCRYPTION_KEY`. The key is never stored in Supabase or returned by the API.
- Session restore enforces origin-host binding, fixed eight-hour absolute expiry and 30-minute idle expiry. Closed/expired sessions clear encrypted state.
- Worker BrowserSupervisor now acquires a session before browser execution, restores Playwright storage state, and persists the updated state back through FastAPI. A caller may pass an existing `session_id`; otherwise the first action creates one and returns its ID.
- Browser supervisor keeps download acceptance disabled and retains existing HTTPS/domain allowlist/egress checks.

## Deployment configuration required

Set `MOREAI_BROWSER_SESSION_ENCRYPTION_KEY` to a Fernet key generated outside the repository (32-byte URL-safe base64 key). Do not commit the key. Browser sessions remain unavailable if it is missing or invalid.

## Explicit limitations

- Browser session persistence covers Playwright storage state (cookies and local storage), not in-memory JavaScript heap, open tabs, service workers, or live browser process state.
- Session state is transferred only over the internal worker-to-FastAPI-to-supervisor channel. The browser UI receives metadata only.
- Download lifecycle is deliberately not enabled: downloads remain cancelled until quarantine, malware scanning, MIME/content validation and private artifact persistence are implemented.
- No UI redesign was made. Customer APIs are available for a future minimal session-management surface; existing dashboard integration remains a subsequent task.

## Verification boundary

No tests, lint, typecheck, build, browser execution, API/provider probes, Supabase execution, staging or deployment were run, per instruction. This is a source implementation record, not runtime acceptance.
