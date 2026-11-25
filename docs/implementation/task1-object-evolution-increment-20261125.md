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
- Regression source covers role/member identity, explicit grant/revoke, implicit option fail-closed behavior, ACL grantor ambiguity and grant-option revocation.

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
- `docs/implementation/task1-object-evolution-increment-20261125.md`

## Verification and safety

- Regression tests were authored but not executed, per the current Master PRD Section 37 P1 execution restriction.
- No reconciliation artifact was regenerated from stale observed snapshots.
- No Supabase production data mutation, migration apply, provider/payment call, staging or deployment was performed.
- Source lineage and migration history records do not constitute an independent database execution receipt.

## Remaining Task 1 work

- Default ACL reduction and role membership option-only revoke / grantor dependency semantics.
- Ownership history bound to observed owner catalog evidence.
- Composite, range and domain type evolution.
- Function/procedure option evolution and opaque body handling.
- Trigger rename/drop/bulk-mode evolution and remaining ALTER TABLE/constraint subtypes.
- Search-path-aware dependency binding and complete `pg_depend` reconciliation.
- Fresh observed catalog, security and dependency snapshots from the canonical Supabase project.
- Independent migration execution provenance and regenerated expected-vs-observed artifacts.
- Browser migration source corrections and duplicate/misnamed migration decisions still require evidence-backed finalization.

Task 1 remains IN PROGRESS. This document records source implementation only; it is not a global semantic reconciliation or release acceptance claim.
