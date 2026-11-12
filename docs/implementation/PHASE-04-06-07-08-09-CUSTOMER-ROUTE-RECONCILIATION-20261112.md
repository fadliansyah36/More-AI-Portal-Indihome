# MoreAI Integration Continuation — 2026-11-12 (Customer API route reconciliation)

## Scope
A source-only correction discovered while continuing Phase 04/06/07/08/09 integration. The protected existing UI was not changed. No production schema or data was changed.

## Baseline and target
- Repository: `fadliansyah36/More-AI-Portal-Indihome`
- Branch: `main`
- Baseline source file: `apps/api/app/routers/customer.py` at blob `06d62823d242d4b8427c677ef690f4a6cb436d3d`
- Resulting commit: `21201caaec53be5b80bdc5e3e2ec07c802d54289`

## Implemented
- Removed an earlier duplicate registration block for Customer `GET /wallet`, `GET /wallet/ledger`, `GET /usage`, `GET /entitlements`, and `GET /quotas`.
- The later implementations remain as the single route definitions. They include consistent timezone-aware cursor validation for ledger/usage, include global plus user-scoped quota policies, and avoid registering duplicate FastAPI method/path handlers.
- No UI routes/components/styles were modified.
- No Supabase migration, DDL, RLS, RPC, or production data write was performed.

## Additional inspection findings
- The current Customer API already has owner-scoped wallet, ledger, usage, entitlement, quota, network-session, access-code redemption and durable agent-run contracts; this does not prove every UI screen is connected.
- The canonical Supabase inventory remains the known 59-table public schema with RLS enabled on all listed tables. The inspected table inventory did not show dedicated EduTech/course/lesson/progress/certificate tables. EduTech cannot safely be wired to real persistence until the product data model and approved schema contract are defined.
- Captive Portal has underlying network verification/session tables, but the existing router coverage does not yet establish the complete gateway challenge → verification → session activation → heartbeat/expiry/revocation lifecycle.
- Worker is containerized in `apps/worker/Dockerfile` and runs as a long-lived polling process in `apps/worker/app/main.py`; this is a deployable artifact, not proof that a persistent worker service is currently deployed and healthy.
- Current worker registry registers Manus and Planning; browser and sandbox tools remain gated. Complete upstream Flow/server/session/tool parity and durable RAG lifecycle are not complete.
- Customer/Partner/Super Admin authorization is based on server-side Supabase Auth identity and database membership/role/permission lookups. Full route-by-route authorization matrix and UI action parity remain outstanding.

## Verification and release boundary
- No tests, lint, typecheck, build, browser QA, API runtime, worker runtime, provider call, migration apply, staging or deployment was run, following the standing product-owner restriction.
- This is a source correction only. No runtime behavior or phase acceptance is claimed.
- No Vercel production deployment was initiated. Production deployment remains blocked by the repository release policy until Phase 11 passes.

## Phase status
- Phase 04: IN PROGRESS
- Phase 05: COMPLETE in tracker; continue object-level security and migration-history reconciliation as needed
- Phase 06: IN PROGRESS
- Phase 07: IN PROGRESS
- Phase 08: IN PROGRESS
- Phase 09: IN PROGRESS
- Phase 10: BLOCKED pending explicit testing authorization and safe test environment
- Phase 11: NOT STARTED

## Next implementation sequence
1. Phase 04: finish SWE workspace CRUD/list/read/delete/history/restore and upstream Flow/server/session parity; preserve browser egress default-deny.
2. Phase 07: complete durable worker recovery, approval resumption, lease/outbox/event replay semantics and persistent runtime deployment configuration.
3. Phase 08: reconcile every upstream agent/provider/tool handler; implement durable retrieval/index lifecycle for RAG and exact per-tool usage/credit settlement.
4. Phase 06/05: complete API contract and schema/RLS/RPC/grant reconciliation against canonical Supabase and Master PRD.
5. Phase 09: finish Customer/Captive Portal, EduTech, Partner and Super Admin screen-to-API binding without changing the visual UI. EduTech needs an approved persistence model before real endpoints are introduced.
6. Request explicit authorization for Phase 10/11 verification; do not mark phases complete before evidence exists.
