# Phase 09 — Human Takeover Preview & Reconnect Continuation (2026-11-16)

## Scope

This continuation adds a customer-authorized, owner-scoped preview lookup for browser sessions. It builds on the existing OpenFuse screenshot capture path, private artifact persistence, short-lived signed artifact download endpoint, takeover grant/command queue and typed customer API client.

## Changes committed on `main`

- FastAPI preview metadata endpoint: `226a8cdb5f2224bd330b0e469cbaa3343940b7f8`
  - `GET /api/v1/artifacts/browser-sessions/{session_id}/preview`
  - Requires authenticated `customer_principal`.
  - Verifies the browser session belongs to the caller and remains active.
  - Resolves only the newest artifact with both `source=openfuse_browser_screenshot` and matching `session_id`, scoped again by caller user ID.
  - Rejects absent preview and invalid/oversized metadata; returns artifact ID and integrity metadata, not a public Storage URL.
  - Customer then obtains the actual short-lived URL through the existing owner-checked `POST /api/v1/artifacts/{artifact_id}/signed-download` contract.
- Typed customer client: `9e395bfc5de02d2ee6263ace59180d13fc486d34`
  - Adds `browserSessionApi.preview(sessionId)` with a typed preview response.

## Reconnect contract

The preview lookup is intentionally stateless and repeatable: after a page reload, the client can list active sessions, request the latest persisted preview, then request a fresh short-lived signed download URL. It does not expose OpenFuse directly and does not persist signed URLs.

## Remaining work — not complete

- No Customer dashboard UI control, preview renderer, reconnect/polling state machine or input form has been added. Existing AGENTS.md UI screenshot gate remains mandatory; baseline and after screenshots were not available for this source-only continuation.
- Screenshot capture still originates from an Agent Run browser action. There is not yet a dedicated durable screenshot-refresh command initiated by the customer session panel.
- Human Takeover command queue/worker path and migrations remain code-only until the product owner authorizes applying migrations; do not assume the migrations are applied.
- Session reconnect still needs an explicit worker/profile reconciliation status contract and customer-facing state mapping for reconnecting, stale, closed and expired sessions.
- No tests, build, lint, typecheck, browser/API/worker runtime, screenshot, staging, deployment, Docker execution or Supabase mutation was performed, per instruction.

## Phase status

Phase 09 remains **IN PROGRESS**. Human Takeover remains **PARTIAL — preview metadata API and typed client added; dashboard interaction and end-to-end reconnect not completed**. Phase 10 is not accepted; Phase 11 remains blocked.


## Follow-up implementation — dedicated preview request lifecycle

Additional commits on `main`:

- OpenFuse screenshot capture adapter, separate from human input: `ad56b0f05368a8e7dfb2eb297f6c5e7aa679d00f`.
- Durable preview queue migration and audit event: `f0844ac8fd21fdaf0f8ffbc43426af070e826d4a`, amended event constraint: `8045b84475a61aeb0eac129f75cf230a34e0bc33`.
- Customer and worker FastAPI request/claim/finish/status endpoints: `e84c434e0174187470ddba66359b92885a25eb31`.
- Worker polling and lease-fenced processing loop: `65139177b9f7f1a78db059b69ad52a785ae68c42`.
- Typed client request/status methods: `50b2a436fbd123f6b91b588dad3017cd499619c9`.
- Typed session history for reconnect state restoration: `299984b0b72548db6d9a297c9cfabc60a6cc07e8`.

The customer endpoint creates a durable request with the explicit `browser.preview` scope. The worker claims it under a lease, verifies the OpenFuse session is active, captures the current page without navigating or sending input, persists the PNG through the existing private artifact boundary, and finishes the request with the artifact ID. Expired sessions are terminalized by the claim RPC; expired worker leases become outcome-unknown failures and are not blindly replayed. The customer can reload request status and session history through the typed client. Preview metadata is retrieved from the existing owner-scoped preview endpoint; the UI can then obtain a short-lived URL through the existing `artifactApi.signedDownload(artifactId)` endpoint.

Still not complete:
- No preview renderer, customer refresh button, request polling hook, reconnect UI, or visible status mapping has been committed. UI screenshot baseline/after evidence required by AGENTS.md is unavailable here, so protected UI files remain untouched.
- Migration `20261116300000_moreai_browser_preview_requests.sql` is committed but not applied. Runtime worker/API configuration and schema availability are not confirmed.
- No tests, build, lint, typecheck, runtime calls, screenshots, staging, deployment or Supabase mutation were performed.

Phase 09 remains **IN PROGRESS**. Human Takeover is now **backend lifecycle implemented in source, UI/runtime integration pending**; it is not declared complete.
