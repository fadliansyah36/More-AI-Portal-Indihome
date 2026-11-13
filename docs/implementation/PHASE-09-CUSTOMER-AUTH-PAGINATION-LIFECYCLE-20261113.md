# Phase 09 — Customer Authorization, Pagination & Lifecycle Continuation

Date: 2026-11-13  
Branch: `main`  
Scope: source-only continuation of the existing Customer dashboard integration. Existing UI structure and visual design remain protected.

## Work completed in this increment

### Customer authorization boundary
- Replaced generic authenticated-user dependencies with `customer_principal` across the Customer router's context, conversation, message, Agent Run, network session, wallet, ledger, usage, analytics, entitlement, quota and access-code routes.
- Customer notifications and notification-preference endpoints now also require `customer_principal`; each query/mutation remains scoped by the authenticated `user_id`.
- Customer agent, tool and model capability catalogue endpoints now require `customer_principal`, keeping Partner and platform principals on their separate API boundaries.
- Existing owner checks for conversation/run/workspace/artifact/approval resources remain in place. This is source inspection and implementation, not a live RLS or cross-tenant proof.

### Pagination and collection lifecycle
- Added incremental keyset loading for private artifact collections in Artifact Results and Workflow, and for saved Code Assistant snapshots and Agent Run selection.
- Analyse document selection now uses the Knowledge Library paged API for initial load, refresh and incremental loading.
- Files upload conflict/ambiguous-response reconciliation now refreshes the selected workspace file page and updates its cursor, avoiding stale pagination state after a server-side CAS commit.
- Ledger incremental loading now de-duplicates rows by ID and preserves a dedicated pagination error so a failed next-page request can be retried without replacing the first-page state.
- Existing keyset cursors for notifications, approvals, workspace files/versions, Agent Runs, conversations/messages, ledger and usage remain wired through the typed page client.

### Approval and cancellation lifecycle
- Workflow approval decisions remain sourced from the durable decision endpoint. A successful decision is now kept visible even if the separate Agent Run list refresh fails; refresh failure is reported independently instead of implying that the approval decision failed.
- Approval decision status is applied from the typed API response without a client-side status cast.
- Customer, conversation-session and Agent Run cancellation routes return persisted terminal status for already-terminal owner-scoped runs rather than submitting a redundant cancellation RPC. Chat copy distinguishes a confirmed cancellation from a worker-accepted cancellation request.
- Cancellation response schemas and TypeScript status unions include `cancel_requested`, `cancelled`, `succeeded`, `failed`, `timed_out` and `expired`.

### Response contract reconciliation
- Typed the nested Customer network-session relation and reconciled nullable fields against the Supabase network schema, including JSONB location address.
- Reconciled workspace file optional storage/version fields and artifact JSONB metadata nullability with the persisted schema.
- Customer profile identity envelope and related frontend types were aligned in the preceding continuation and retained.
- JSON endpoints in Customer, conversation, Agent Run, notification, approval, workspace, artifact, profile, learning and catalog routers have explicit Pydantic response contracts; streaming and binary responses remain transport-specific.

## Source commits in this continuation

- `7c8646a4b0785580f56ab3e2d3ab892e56f3b36b` — complete Customer principal dependency wiring for notifications.
- `8346c6cc160747a4e2950e1dca97a827e2498f53` — complete Customer principal dependency wiring for catalog.
- `3e5aae18ab88c5f06e2cfdfe810ec770fc853e77` — complete Customer principal dependency wiring for Customer routes.
- `82f812a8367d2c78e09b934791865ac469e512ae` — scope Customer agent/model catalogue to Customer principal.
- `af4b68c24b6c55b9f2de54c678e4c8ee6b022f35` — require Customer principal across Customer API routes.
- `15257ace00c0d7b53c7d115d73718953432a0aae` — separate approval decision persistence from Agent Run refresh errors.
- `9ff71fbd281a9d6127c620dcc739182214c115fe` — initial Customer principal enforcement for notifications.
- Pagination, schema and sample-content corrections are recorded in the latest direct-main commit history, including `4888d625`, `0fbb38a8`, `0638df8a`, `d8454a46`, `eac4dc1e` and `33a01753`.

## Explicit verification boundary

Per product-owner instruction, this increment did **not** run tests, lint, typecheck, build, browser interaction, screenshots, API probes, worker execution, provider calls, staging, migrations, Supabase writes or deployment. No claim of runtime correctness, live authorization enforcement or end-to-end acceptance is made. UI files changed only for specific integration behavior; no redesign or broad styling changes were made.

## Remaining Phase 09 work

1. Complete source-level response/authorization review of every remaining Customer-facing action, including profile, notification preferences, learning, Knowledge Library, artifacts, workspace members/runs and all nested session/event routes.
2. Reconcile workspace combined-list pagination beyond the existing bounded fan-in cap; a DB-side union cursor is still needed to guarantee complete traversal at scale.
3. Reconcile pagination and lifecycle semantics for every remaining collection and ensure refresh/optimistic state remains consistent after mutations.
4. Finish workspace/file/version navigation and lifecycle parity across every screen that exposes the action, including delete/restore/download and run association.
5. Continue scanning Customer screens for any local sample content that could be mistaken for persisted business data. Code Assistant starter snippets are editor examples only, not business records.
6. Complete provider-independent integration where canonical data/contracts already exist.

Gateway/ISP/Mikrotik/RADIUS, OTP/consent delivery, authoritative EduTech catalog/video, image/video generation, payment checkout/settlement and support ticketing remain fail-closed until official provider contracts, credentials and operational ownership are supplied. No simulated success or fabricated business data is permitted.

**Phase 09 remains IN PROGRESS.** Phase 10 is not accepted and Phase 11 remains blocked. The next phase after Customer integration is closed is Phase 10 — End-to-End Integration Verification; it must not begin early.
