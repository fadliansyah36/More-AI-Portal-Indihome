# MoreAI Phase 04–09 Continuation — Approval Lifecycle Contract
Date: 2026-11-11
Branch: main (direct commits; no branch created)
Repository: fadliansyah36/More-AI-Portal-Indihome

## Scope requested
Continue Phase 04 full upstream tool/approval integration, then Phases 06–09, with priority on connecting existing UI to OpenManus through FastAPI and removing hardcoded/static business data. Product owner explicitly instructed that real tests and other tests be skipped for this continuation.

## Repository rules reviewed
Read `AGENTS.md` and Master PRD sections governing complete upstream backend parity, protected existing UI, FastAPI as the trusted data boundary, Supabase persistence, sandbox/browser security and phase gates. The upstream pin remains `YunQiAI/OpenManusWeb@3ceaa9182b39bbb9898ddda0a4b1c50c2758ab5f`; the 111-file pristine snapshot remains under `vendor/openmanusweb`.

## Implemented in this continuation
1. Added `supabase/migrations/20261111050000_moreai_tool_approval_lifecycle.sql`.
   - Durable `agent_tool_approvals` records bind run, user, tool and canonical argument SHA-256.
   - Includes pending/approved/denied/expired/consumed lifecycle, expiry, unique pending request protection and one-time consumption.
   - Enables RLS, revokes direct anon/authenticated access and grants server-only service_role access.
   - Adds server-only RPCs for request, decision and atomic consume.
2. Added `apps/api/app/routers/tool_approvals.py`.
   - Customer-principal scoped list, request and decision endpoints.
   - Request and decision are delegated to server-only database RPCs.
3. Registered the router in `apps/api/app/main.py`.
4. Added typed `customerToolApprovalApi` and approval response types to `lib/api/client.ts`.
5. Updated `docs/implementation/openmanus-backend-capability-map.json` and `docs/implementation/PHASE-TRACKER.md` with this increment and its remaining gates.

## Critical limitations — not complete / not activated
- The new migration is authored but has NOT been applied to the Supabase project.
- Worker tool dispatcher does not yet create approval requests, pause a run in a durable awaiting-approval state, resume after decision, or atomically consume the approval immediately before sandbox execution.
- The production worker registry still does not expose Bash/Python/Browser/file tools. This remains fail-closed.
- Browser isolation, SSRF/private-IP filtering, DNS rebinding resistance, redirect revalidation and download scanning are not implemented as an integrated browser supervisor.
- File execution/editor workspace isolation and artifact handoff are not complete.
- Upstream agent/flow/workflow parity is still partial; the capability map records remaining source-to-target gaps.
- Phase 06 complete OpenAPI/domain contract coverage is not achieved.
- Phase 09 is not globally complete: Customer Chat and Partner Portal integrations were previously implemented, and the typed approval client is now added, but all other existing UI screens have not yet been systematically connected to their domain APIs. No claim is made that all static/hardcoded UI data has been removed.
- Phases 10 and 11 remain blocked/not started. No deployment or worker activation.

## Verification policy and evidence
Per explicit product-owner instruction, no tests, lint, build, browser, SQL apply, runtime or production verification were run in this continuation. Therefore there is no new passing verification evidence and no gate is marked passed. Existing historical CI results in earlier reports are not evidence for these new changes.

A local Git checkout was not available in the execution environment because outbound GitHub DNS resolution failed. File updates were committed directly through the GitHub connector on `main`.

## Next required implementation sequence
1. Worker approval request → durable awaiting-approval status/event → server decision → worker resume → atomic one-time approval consumption.
2. Sandbox supervisor dispatch contract for Python/Bash with immutable image and no host mounts/secrets; keep tools disabled until deployed supervisor and security evidence exist.
3. Browser isolated worker with domain allowlist, resolved-address pinning, private/reserved IP rejection, redirect revalidation, DNS rebinding protection and controlled downloads.
4. File workspace adapter with per-run isolated root, traversal/symlink protection, quotas, artifact persistence and owner-scoped download.
5. Complete upstream agent/flow/workflow parity and update every capability entry with target module, API, persistence and evidence.
6. Finish Phase 06 API contracts and Phase 07 durable lifecycle/lease fencing.
7. Connect each existing UI route to its corresponding FastAPI domain API; remove demo/static business data and show explicit unavailable/loading/error states where a real endpoint is not yet available. Preserve existing visual structure.
8. Phase 10 and Phase 11 remain acceptance gates; they cannot be declared complete without the evidence required by AGENTS.md.

## Status
Phase 04: IN PROGRESS.
Phases 06–09: IN PROGRESS.
Phase 10: BLOCKED.
Phase 11: NOT STARTED.
