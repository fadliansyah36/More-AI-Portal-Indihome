# Customer Runtime Routing and Approval Resume UI Integration
Date: 2026-11-12
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main

## Scope
Customer-only integration corrections. Existing UI layout, styling, copy and navigation were preserved.

## Changes committed
- `68d22b4bf1901f37d0e2d7387d1793c8f004c1ea`: Workflow Progress now recognizes the persisted backend state `waiting_approval` as “Menunggu persetujuan” and includes it in active-run counts. After an owner decision, the screen reloads durable run state so the re-queued continuation is reflected.
- `3d1b435032ac15ef81f6eda5a8aaf0ff795ccfeb`: Customer agent run list, detail, steps and event history now use `moreAiCustomerApi`, honoring `NEXT_PUBLIC_MOREAI_CUSTOMER_API_URL` rather than silently using the generic API origin.
- `2a2c17612c53bf2f9551e4e545eea22341e383da`: Customer Agent Studio catalog now uses the Customer API origin too.

## Integration boundary
- Browser business calls remain behind FastAPI and the Supabase Auth bearer token.
- No direct browser PostgREST, Storage, RPC or Realtime access was introduced.
- No schema or production Supabase data was modified.
- No UI redesign was performed.

## Remaining work
These changes close source-level routing and UI-state gaps; they do not prove the complete Customer runtime:
- Confirm worker deployment and configured Customer API origin in production.
- Complete OpenManus upstream backend parity for agent/Flow/server/session capabilities.
- Complete durable approval decision/resume/re-enqueue acceptance and race/recovery behavior.
- Complete Phase 06 route-by-route OpenAPI/auth/tenant contract reconciliation.
- Complete all Customer screen integrations, including auth identity, conversation history, wallet/ledger, quota/entitlement, Wi-Fi/network sessions, artifacts, notifications and EduTech where the product schema supports them.
- Complete Phase 10/11 only after explicit authorization for real provider, worker, persistence, security and UI regression tests.

## Verification boundary
No tests, lint, typecheck, build, browser QA, staging, Supabase migration, production API call or deployment was run in this increment. The report describes source changes only.
