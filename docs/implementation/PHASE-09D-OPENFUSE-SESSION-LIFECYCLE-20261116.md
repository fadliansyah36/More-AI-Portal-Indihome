# Phase 09D — OpenFuse session supervisor and storage lifecycle continuation

Date: 2026-11-16  
Target branch: `main`

## Scope implemented

- Added an internal FastAPI expiry reconciler for persistent OpenFuse browser sessions. It evaluates the existing eight-hour absolute TTL and thirty-minute idle TTL, then changes eligible active sessions into durable `close_requested` work.
- Added worker polling of the expiry reconciler before consuming close requests. The existing isolated OpenFuse browser supervisor remains responsible for closing Chromium; the API does not pretend a session is physically closed.
- Added a forward-only Supabase migration that includes `close_requested` in the browser session event constraint. This fixes the mismatch between the existing customer close endpoint (which records that event) and the original event constraint.
- Session ownership remains scoped by user ID. Worker-only lifecycle endpoints require the internal worker token. Existing run-state checks continue to defer physical close while a run is active.

## Files changed

- `apps/api/app/routers/browser_sessions.py`
- `apps/worker/app/main.py`
- `supabase/migrations/20261116100000_moreai_browser_session_close_event_constraint.sql`

## Data flow

1. Worker calls FastAPI internal expiry reconciliation.
2. FastAPI reads active session metadata from canonical Supabase tables and applies TTL/idle policy.
3. Eligible sessions are durably marked `close_requested` and an event is written.
4. Worker reads close requests and checks whether the associated Agent Run is still active.
5. When safe, worker asks the isolated OpenFuse service to close the browser context and acknowledges closure through FastAPI.
6. FastAPI clears encrypted browser storage state when closure is acknowledged.

## Safety and boundaries

- No direct browser-to-Supabase access was introduced.
- No new database, task engine, browser runtime, or storage provider was introduced.
- No credentials or provider secrets were added to source.
- The expiry endpoint only schedules durable cleanup; it does not report physical browser termination.
- Storage state remains encrypted through the existing Fernet-backed API path. Malware scanning for browser downloads remains unavailable, so download import remains blocked.
- The worker reconciliation loop only runs when the existing worker/browser runtime is enabled and configured.

## Verification and deployment

Per product-owner instruction, no tests, lint, type checks, builds, browser/API/worker runtime calls, Docker execution, provider calls, staging, or deployment were performed. This report records source changes only. Production supervisor availability, storage persistence, actual OpenFuse cleanup, RLS behavior, and end-to-end lifecycle remain unverified.

## Next work

1. Continue storage lifecycle hardening: explicit session-state save/restore reconciliation, encryption-key rotation compatibility, bounded state retention, and cleanup of orphaned OpenFuse profiles.
2. Complete customer dashboard Browser Sessions UI using existing typed FastAPI client, including expiry/close status and action receipts.
3. Finish Skills Governance publication gates: transitive dependency/license evidence, reviewer decision provenance, and artifact/SBOM download path.
4. Continue route-to-screen integration across customer dashboard capabilities without changing existing visual design.
