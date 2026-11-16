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
