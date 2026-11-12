# Phase 04 Security Increment — Workspace Signed URL Origin
Date: 2026-11-12
Branch: main

## Scope
Phase 04 security hardening for the Customer workspace signed-download endpoint.

## Implementation
- Updated `apps/api/app/routers/workspaces.py`.
- Signed URLs returned by Supabase Storage are now accepted as absolute URLs only when they use HTTPS and match the configured Supabase origin exactly (including host/port).
- Absolute URLs containing userinfo are rejected.
- Relative signed paths must be absolute-path references, not protocol-relative URLs, and may not contain backslashes or control characters.
- Invalid Storage responses fail with HTTP 502 rather than being forwarded to the Customer browser.
- Existing workspace membership authorization, private-bucket check, scoped object lookup, and short-lived signed URL behavior are retained.
- No UI files or visual styles were changed.

## Commit
`7405e5d6fb580b74c0c0d3bd07efe89024907255`

## Verification boundary
Source commit only. No tests, lint, typecheck, build, API runtime, browser QA, staging, migration or deployment was run. Do not treat this increment as full Phase 04 acceptance.

## Remaining Phase 04 work
- Complete workspace CRUD/lifecycle and ensure all file mutations use the lease-fenced OpenManus workspace tool path.
- Complete OpenManus server/session/Flow Engine parity through FastAPI and durable persistence.
- Verify browser supervisor topology, DNS/SSRF controls, isolated Python/Bash runner, process-tree/resource controls and approval enforcement.
- Reconcile and close every backend-capable module in the pinned upstream capability map.

## Dependent phases
Phase 07 (durable retry/timeout/cancellation races/lease recovery/checkpoint/approval continuation/event replay), Phase 08 (all agents/tools/provider fallback/orchestration/memory/RAG), Phase 06 (OpenAPI/auth/tenant/error/idempotency), and Phase 09 (all Customer screens) remain in progress and must follow Phase 04 in that order.

## Constraints
No tests or runtime acceptance were run; no staging, migration or deployment was performed. Existing MoreAI UI/UX was preserved.
