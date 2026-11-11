# MoreAI — Phase 05/06 Governance & Notifications Increment
Date: 2026-11-11
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Supabase project: `uunfgimtokhucegqbpce`

## Scope and status
This is a verified schema-provisioning increment plus source implementation for notifications and one permission-specific Super Admin mutation. It does **not** complete Phases 04–09, and it is not a release acceptance.

## Supabase changes applied
Two forward-only migrations were added to the repository and applied to the bound Supabase project:

- `20261111100000_moreai_notifications_private_artifacts_immutable_audit`
- `20261111103000_moreai_admin_partner_status_atomic_audit`

Verified with read-only catalog queries after apply:
- `notifications`: 12 columns; RLS enabled.
- `notification_preferences`: 5 columns; RLS enabled.
- Both notification tables deny `anon` and `authenticated` access and grant the trusted service role only.
- Private Storage bucket `moreai-artifacts` exists with `public=false`, 2 MiB maximum size and a constrained MIME allowlist.
- `storage.objects` already had RLS enabled and no client policies. The migration role is not the owner of `storage.objects`; the attempted DDL to alter its policies was rejected and removed. No ownership bypass was attempted. Existing default-deny behavior is retained.
- `admin_audit_logs` now has row-level UPDATE/DELETE rejection and statement-level TRUNCATE rejection triggers. Client and service-role UPDATE/DELETE/TRUNCATE privileges are revoked; service role retains SELECT/INSERT for append-only writes.
- `admin_mutation_requests` is server-only and persists actor-scoped idempotency keys, exact JSON payloads and committed responses.

## API and source changes committed
- Added `GET /api/v1/notifications`, unread filtering, owner-scoped mark-read and mark-all-read endpoints.
- Added notification preference GET/PUT endpoints with service-side upsert.
- Registered notification router in FastAPI.
- Added typed notification contracts and methods in `lib/api/client.ts`.
- Added `PATCH /api/v1/admin/partners/{partner_id}/status`, guarded by the explicit `partner.organization.manage` permission in the API and rechecked inside the database function.
- Added `moreai_admin_update_partner_status`: permission validation, idempotency conflict detection, row lock, partner status update, immutable audit append and idempotency response persistence happen in one database transaction.
- Added typed frontend API method for partner status governance.
- API and worker now default to the provisioned private `moreai-artifacts` bucket while allowing an explicit environment override.

## Verification performed
- Supabase migration application returned success for both migrations.
- Read-only SQL verified notification tables and RLS state, private bucket configuration, and both audit triggers.
- Existing partner status constraint and current permission matrix were inspected before defining the mutation contract.
- No notification records, partner records or audit records were inserted as test data.
- No API runtime test, unit test, lint, typecheck, build, browser test, provider call or deployment was run in this increment. The code changes are not behavioral acceptance evidence.

## Security notes and limitations
- Storage bucket creation succeeded. The existing `storage.objects` RLS is already enabled; this migration did not attempt to change its ownership-controlled policy set. Browser Storage access remains prohibited by AGENTS.md; API/worker use server-side credentials and owner-scoped object paths.
- The audit trigger prevents UPDATE, DELETE and TRUNCATE. Audit rows remain append-only; the database owner/superuser can still alter schema/triggers, which is outside normal application roles.
- Only partner organization status is implemented as a transactional Super Admin mutation. User governance, role assignment/revocation, provider/model configuration, finance, network/session actions, dual-control approvals and broader mutation coverage remain open.
- Notification delivery producers, email/push dispatch, realtime delivery, retention policy and UI wiring remain open.
- No UI file was modified. Existing UI screenshot gate remains mandatory before Customer Chat, Agent Studio, Workflow or Files components are changed.

## Commits
- Schema notifications/private bucket/audit migration: `e137c1c4f5db87a66187ff17c14d63ef07d19153`
- Storage ownership-safe migration correction: `5577a74616bb93aff982f55ba00478aababad14f`
- Notifications API route: `4a2af5e55e1de1270b368fa7e745601958ac041e`
- Notification timestamp correction: `ef0bbc50cf8c1d6b1ae4981272fe05ae9f117fd6`
- FastAPI notification router registration: `bebf1c2c45afe3a05ee8317e732a0181c1c9eec9`
- Notification client contract: `62fb05076639a88fc7eebcba3169d30f851d39c1`
- Atomic Super Admin partner status migration: `53f0df754769b6a0c145c9688d30869778bad6ce`
- Permission-specific API mutation: `a8f1bc23b6c4851aac83b1c2db8fcea9dae4d527`
- API private bucket default: `487067ad0bb616404b76aab70858d9c2f451f123`
- Worker private bucket default: `e3813a7ebb8c7585a91fc1792de812c57f7f52c6`
- Typed Super Admin client method: `785b76f883d354973fb8871b8a1e1043d9206dcf`

## Next implementation sequence
1. Phase 04: browser supervisor with socket-level egress/DNS/redirect/subresource/download enforcement; persistent isolated SWE workspace; upstream Flow/server/session parity and structured tenant-safe logging.
2. Phase 07–08: persisted event append/sequence/outbox, cancellation propagation at every tool boundary, timeout/retry/recovery reconciliation and full tool adapter parity.
3. Phase 05–06: reconcile and add only schema/API contracts for notification delivery, Wi-Fi/captive portal, voucher redemption/settlement, network analytics and remaining Partner operations.
4. Super Admin: expand transactional mutation RPCs to each governance domain with explicit permission keys, idempotency, append-only audit, and dual-control for sensitive operations.
5. Phase 09: after required baseline/after screenshots are available, wire existing Customer Chat, Agent Studio, Workflow and Files screens to typed APIs without visual changes.
6. Phase 10–11: run the full integration and release gates only when tests and live verification are authorized and all required credentials/runtime infrastructure are available.
