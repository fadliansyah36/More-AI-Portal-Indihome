# Phase 09 — Browser Session, Computer Workspace and Customer surface reconciliation

Date: 2026-11-16  
Branch: `main`  
Scope: source-level reconciliation of Customer Profile settings, Browser Session API, OpenFuse BrowserSupervisor, Computer action receipts and the worker lifecycle.

## Findings confirmed in source

### Browser Session / OpenFuse

- Customer list endpoint returns only owner-scoped `active` and `close_requested` sessions. Customer close is a backend RPC request; the UI correctly distinguishes a close request from a completed worker close.
- A separate owner-scoped history endpoint returns closed/expired sessions and per-user session events, including `profile_retention_after` and `profile_deleted_at`. The typed client already exposes `browserSessionHistory()`, but the current Profile screen does not consume it.
- Worker-only endpoints are protected by `MOREAI_WORKER_INTERNAL_TOKEN`; acquisition validates a running Agent Run with the same user, encrypts persisted storage state, enforces session/idle TTL, records session events and acquires a capacity lease.
- The worker uses the same validated BrowserSupervisor instance for OpenManus browser tools and the close/profile-retention reconciliation loop (previous source hardening).
- Profile deletion depends on a separately maintained OpenFuse `delete-profile` patch. Browser downloads are scanner-gated and remain disabled until the private scanner-backed artifact path is enabled.
- The Customer API currently has no authenticated same-session Human Takeover grant/reconnect endpoint or short-lived scoped grant contract. The current UI only closes and lists sessions; it does not offer takeover.

### Computer Workspace

- Customer-facing API exposes owner-scoped action receipts only.
- Claim/finish endpoints are worker-internal, authenticate the worker token, verify run owner and workspace binding, use idempotency/action hashes, cap stored result size and prevent receipt finalization conflicts.
- Bash/Python execution is behind a separately configured isolated supervisor and explicit release gates. The UI's current history view is not an execution console and must not imply that an interactive desktop/terminal takeover is available.
- No Customer-authorized computer session reconnect/terminal streaming contract was found in the inspected router. No UI action should be added that would claim this capability exists.

## Safe reconciliation decisions

1. Keep browser session ownership, storage state, action receipts, event history and capacity leases in the existing Supabase-backed contracts. Do not create a second OpenFuse task/session database.
2. Do not expose worker-internal endpoints or tokens to the browser.
3. Do not add a Human Takeover button until a scoped, expiring, revocable grant, authenticated Customer endpoint, same-profile reconnect transport and audit lifecycle are implemented.
4. Do not add interactive Computer Workspace controls until the isolated supervisor exposes a customer-authorized session contract with workspace/run ownership, streaming, cancellation, limits and audit.
5. Use the existing history endpoint in a future minimal Profile screen integration only after the protected-UI before/after evidence gate can be honored. No screen redesign is authorized.
6. Treat deployment/runtime readiness as unproven. Existing source-level fail-closed gates must remain in place until the private worker/supervisor, encrypted profile key, worker token, proxy, scanner and capacity resources are provisioned and verified.

## Current source-to-screen status

| Customer surface | API / persistence | Status |
|---|---|---|
| Profile identity/preferences | Typed FastAPI profile and notification APIs; Supabase Auth is used only for identity fallback | Integrated in source; runtime not verified |
| Browser active sessions | Owner-scoped FastAPI list and Supabase session rows | Integrated in source |
| Browser close request | Owner-scoped close RPC; worker reconciliation completes actual close | Integrated in source; worker operation not verified |
| Browser session history / retention | Owner-scoped history endpoint and typed client method | API/client exist; Profile UI not yet wired |
| Browser Human Takeover | No Customer grant/reconnect contract found | Missing; blocked from UI activation |
| Browser action history | Owner-scoped receipts API | Integrated in source |
| Computer action history | Owner-scoped receipts API | Integrated in source |
| Interactive Computer Workspace | No Customer session/stream/reconnect contract found | Missing; isolated supervisor remains release-gated |

## UI preservation

No UI file was changed in this continuation. Existing Profile layout and visual tokens are preserved. The missing takeover/interactive controls are deliberately not represented by fake buttons or simulated success states.

## Verification boundary

Source inspection only. No tests, build, lint, type-check, screenshot capture, browser/API/worker runtime, Docker, OpenFuse service, scanner, OAuth/provider call, staging, deployment, migration apply or Supabase data mutation was performed.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED**.
