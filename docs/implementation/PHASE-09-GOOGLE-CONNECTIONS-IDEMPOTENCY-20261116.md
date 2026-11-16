# Phase 09 — Google Connections action idempotency continuation

Date: 2026-11-16  
Branch: `main`  
Scope: Customer UI → typed FastAPI API → Supabase action-receipt idempotency for Gmail send and Google Calendar mutations.

## Source changes committed

1. `2837339b6c06f84cafb5747607a1893baf40fb3a` — `lib/api/client.ts`
   - Customer Connections API methods now accept a caller-supplied idempotency key for Gmail send, Calendar create, update and delete.
   - A generated UUID remains the compatibility default for existing callers.
   - Existing authenticated FastAPI boundary, request bodies, confirmation flags and ETag preconditions are unchanged.

2. `fe9828fc71640bfc9227eeb1990051e85804c6ed` — `components/views/connections-center-view.tsx`
   - The Customer UI now creates a stable idempotency key for the exact confirmed operation payload.
   - Gmail send and Calendar create/update/delete reuse that key after an ambiguous request failure while the component remains mounted.
   - The key is cleared only after the corresponding mutation returns success. A deliberate new operation after success receives a fresh key.
   - This aligns with the FastAPI requirement for `Idempotency-Key` and the existing Supabase action receipt RPCs; it does not create a second receipt store.

## Source-level contract reconciliation

The existing FastAPI routes in `apps/api/app/routers/connections.py` require a 12–128 character `Idempotency-Key` for Gmail send and Calendar create/update/delete. They claim/finish the existing connection action receipt through the existing Supabase RPC boundary. The Customer client previously generated a fresh UUID inside each method call, which meant a user retry after a lost response could be treated as a new external side effect. The updated view now preserves the operation key across that retry path.

## UI and security boundary

- Only the existing Connections Center component was changed; layout, typography, colors, spacing and visual hierarchy were preserved.
- No direct Supabase access was added to the browser. The existing typed Customer API client remains the only business-data path.
- No OAuth scopes, confirmation prompts, approval gates, ETag checks, credentials or provider policies were relaxed.
- No secrets, schema, migrations, database rows or provider settings were changed.

## Limitations

- The stable key is retained in component memory while the Customer view remains mounted. A full page reload/unmount loses the local key; durable client-side recovery across reloads would require a privacy-safe operation draft/recovery contract and must not persist raw email bodies or other sensitive payloads in browser storage.
- The API deployment and external Google credentials/provider outcomes are not verified by this source change.
- This closes one concrete action-to-API retry/idempotency gap; it does not close the complete Customer Dashboard acceptance matrix.

## Verification boundary

Per product-owner instruction, no tests, build, lint, type-check, browser/API/worker runtime, OAuth/provider calls, staging, deployment or Supabase mutation was run. The source files and FastAPI header contract were inspected only.

Phase 09 remains **IN PROGRESS**. Phase 10 remains **NOT ACCEPTED**. Phase 11 remains **BLOCKED**.
