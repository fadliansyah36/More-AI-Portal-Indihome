# MoreAI Customer Supabase Migration & EduTech Progress Integration

Date: 2026-11-12  
Canonical repository: fadliansyah36/More-AI-Portal-Indihome (main)  
Canonical Supabase project: `uunfgimtokhucegqbpce`

## Supabase migrations applied

The following forward-only migrations were applied to the canonical Supabase project:

1. `moreai_workspace_file_version_history`
   - Creates `public.agent_workspace_file_versions`.
   - Enables RLS with explicit server-only deny policy for anon/authenticated.
   - Grants server-side service_role access.
   - Adds trigger/function to preserve previous committed version metadata when a CAS version advances.
2. `moreai_workspace_restore_approval_key`
   - Extends the persisted approval constraint and request RPC allowlist with `workspace_restore_version`.
3. `moreai_customer_learning_progress`
   - Creates user/module/lesson completion persistence.
   - Enables RLS with explicit server-only deny policy.
   - Adds a service-role-only atomic upsert/delete RPC.

Supabase migration history records versions:
- `20261112044816` — moreai_workspace_file_version_history
- `20261112044822` — moreai_workspace_restore_approval_key
- `20261112044926` — moreai_customer_learning_progress

## Database verification

Read-only database verification confirmed:
- Workspace file version history table exists.
- Version archive trigger and function exist.
- Approval check constraint and RPC accept `workspace_restore_version`.
- Learning progress table and RPC exist.
- RLS is enabled on the new history/progress tables.
- service_role grants are present.
- `moreai-artifacts` Storage bucket exists and is private.

No destructive reset, table drop, or data rewrite was performed.

## Customer EduTech integration

- Added `apps/api/app/routers/learning.py`:
  - `GET /api/v1/customer/learning/progress`
  - `PUT /api/v1/customer/learning/progress`
- Registered the router in FastAPI.
- Added typed `learningApi` client methods.
- Connected the existing EduTech module lesson-completion state to the Customer API and persisted Supabase progress.
- Kept the existing UI structure and visual styling; only data loading and persistence behavior changed.

## Related workspace/runtime integration already in main

- Workspace list/create, member-scoped file listing and immutable version history APIs.
- Private Storage signed downloads for current/historical versions.
- OpenManus `workspace_restore_version` tool uses private historical object bytes, validates SHA-256/size and commits restore as a new lease-fenced CAS version.
- Restore is included in high-risk approval policy and approval API schema.

## Verification boundary

Supabase migration application and schema/RLS/grant/private-bucket checks succeeded. No app tests, lint, typecheck, build, browser E2E, staging, or deployment were run in this increment. Database verification does not prove end-to-end runtime behavior. UI screenshot-based regression evidence is not claimed.

## Remaining integration work

- Phase 04: full upstream OpenManus Flow/server/session parity, full SWE workspace read/write/delete/restore UX, browser supervisor/egress hardening and sandbox lifecycle.
- Phase 07: retry/timeout/cancellation race handling, lease recovery, outbox/event replay and approval continuation acceptance.
- Phase 08: all upstream LLM provider adapters/fallback, agents, tool coverage, orchestration, memory and RAG.
- Phase 06: complete versioned FastAPI contracts, schemas, pagination/idempotency/correlation and tenant authorization.
- Phase 09: bind every remaining existing Customer screen to real API contracts, including Wi-Fi device inventory, Captive Portal, wallet/ledger/top-up, notifications, analytics, profile/security settings and remaining EduTech learning workflows.

No integration phase is declared complete. The application is not yet represented as production-ready or fully operational.
