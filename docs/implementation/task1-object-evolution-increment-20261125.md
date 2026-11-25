# Task 1 — PostgreSQL semantic reducers: incremental implementation

Date: 2026-11-25
Branch: `main`
Baseline for this increment: `81950cb101b5e0825e1de67d47d242d8bea783b1`

## Implemented in this increment

- Role membership statements now receive pair-specific identities (`member:<member>->role:<role>`) instead of collapsing unrelated grants into one generic object.
- `GrantRoleStmt` events are expanded per member/role pair and reduced independently.
- Explicit role membership grants and full revokes are reduced only when grantor and ADMIN/INHERIT/SET options are explicit. The reducer preserves grantor identity.
- Implicit role options, option-only revokes and CASCADE effects remain `NOT_VERIFIABLE`; no role catalog defaults or dependent membership effects are inferred.
- ACL reduction refuses to publish an effective ACL definition if any grantor is unresolved. Explicit `REVOKE GRANT OPTION` retains the privilege and clears only that grant option.
- Default ACL statements now receive owner/schema/object-type identities. The reducer folds explicit GRANT/REVOKE transitions per owner/schema/object type and preserves the owner role as grantor. Implicit owner, unsupported object types, unresolved grantees and CASCADE remain `NOT_VERIFIABLE`.
- Regression source covers role/member identity, explicit role grant/revoke, implicit role options, ACL grantor ambiguity, grant-option revocation, default-ACL identity and default-ACL grant/revoke. 

## Previously implemented reducers retained

- Dependency binding uses exact qualified identity and avoids ambiguous schema suffix matching.
- Typed DROP handling preserves each target and function/procedure signatures.
- RLS policy CREATE/ALTER folding preserves omitted clauses and rejects identity changes.
- Enum evolution supports ADD VALUE append/before/after and RENAME VALUE with fail-closed handling for unknown neighbors.
- Sequence evolution folds supported explicit options only; defaults, OWNED BY dependencies and runtime restart/last_value remain outside its proven scope.
- Column evolution supports selected ALTER subtypes; unknown subtypes remain unverifiable.
- Trigger evolution supports named enable/disable modes; rename/drop/bulk modes remain unsupported.
- Customer Wallet Top Up remains disabled until a real payment-intent and signed-settlement flow exists.

## Files changed in this increment

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`
- `lib/api/client.ts`
- `components/views/super-admin-view.tsx`
- `docs/implementation/task1-object-evolution-increment-20261125.md`

## Verification and safety

- Regression tests were authored but not executed, per the current Master PRD Section 37 P1 execution restriction.
- No reconciliation artifact was regenerated from stale observed snapshots.
- No Supabase production data mutation, migration apply, provider/payment call, staging or deployment was performed.
- Source lineage and migration history records do not constitute an independent database execution receipt.

## Remaining Task 1 work

- Role membership option-only revoke / grantor dependency semantics remain unsupported.
- Ownership history bound to observed owner catalog evidence.
- Composite, range and domain type evolution.
- Function/procedure option evolution and opaque body handling.
- Trigger rename/drop/bulk-mode evolution and remaining ALTER TABLE/constraint subtypes.
- Search-path-aware dependency binding and complete `pg_depend` reconciliation.
- Fresh observed catalog, security and dependency snapshots from the canonical Supabase project, including a normalized `pg_default_acl` view for comparing reduced default ACL state.
- Independent migration execution provenance and regenerated expected-vs-observed artifacts.
- Browser migration source corrections and duplicate/misnamed migration decisions still require evidence-backed finalization.

Task 1 remains IN PROGRESS. This document records source implementation only; it is not a global semantic reconciliation or release acceptance claim.


## Additional increment — default ACL and Super Admin API transport

- `AlterDefaultPrivilegesStmt` identities now bind explicit owner role, schema scope (including global scope) and nested GRANT object type.
- Added explicit default ACL history reduction for table, sequence, function and type defaults. Each migration event is reduced only for its exact owner/schema/object target.
- Added fail-closed handling for missing owner role, unsupported object type, unresolved grantee/privilege, unknown action and CASCADE.
- Added regression source for multi-schema identity, explicit GRANT/REVOKE and implicit owner.
- Centralized Super Admin dashboard reads and mutations through the shared authenticated `platformAdminApi` transport. Removed the dashboard-local fetch/auth implementation so admin API requests share the same token refresh, error normalization and safe-read fallback rules as the rest of MoreAI.
- This is an API transport integration only; it does not expand the set of admin capabilities or claim frontend E2E verification.
