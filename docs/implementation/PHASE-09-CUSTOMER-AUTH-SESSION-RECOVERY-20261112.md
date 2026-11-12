# Customer Authenticated API Session Recovery
Date: 2026-11-12
Branch: main
Repository: fadliansyah36/More-AI-Portal-Indihome

## Scope
A narrow customer-side integration correction in the shared typed API client. Existing UI and routes were not changed.

## Changes
- Standard authenticated JSON API calls now retry once after HTTP 401 by explicitly refreshing the Supabase Auth session.
- If refresh fails or the retried request remains unauthorized, the local Auth session is cleared and the caller receives a clear re-login error.
- HTTP 403 and business errors are not retried. The recovery path therefore does not replay requests after authorization or domain failures.
- The customer SSE workflow stream now performs the same one-time session refresh on 401, preserving its Last-Event-ID cursor when retrying.
- SSE terminal event handling now recognizes run.expired as terminal.

## Security and architecture
- Browser still uses only the Supabase publishable/anon key for Auth.
- Business data and agent execution remain behind FastAPI with the user's bearer JWT.
- No service-role key, provider key, role, tenant, entitlement or credit information is introduced into the browser.
- No UI/UX files or database schema were changed.

## Verification boundary
No tests, lint, typecheck, build, browser, runtime API calls, staging or deployment were run. This is a source-level integration fix only; it is not evidence that customer registration, login, worker execution, provider routing, memory/RAG or end-to-end workflow is accepted.

## Commit
- 030ec8efa6bab34acd5e10a0750f3245d2ccc18a — refresh Supabase Auth after API 401.
- 95d4e5d8df21a30f0624c83ffe9075034b1776d7 — recover authenticated workflow event streams.
