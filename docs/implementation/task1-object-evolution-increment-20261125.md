# Task 1 — PostgreSQL object identity and evolution reducer increment

Date: 2026-11-25
Branch: `main`
Starting HEAD: `bdd62195a0997ed2789cff52d15cf55d9b7166ce`

## Implemented source changes

1. Dependency binding: exact qualified identity matching replaces ambiguous schema suffix/prefix matching. Unqualified AST references remain unbound unless exact evidence exists.
2. DROP lineage: decode PostgreSQL typed DROP targets separately; preserve multi-object statements; map supported DROP object types to their CREATE semantic classes; do not invent `public` for unqualified relation/global-object names.
3. Function identity: preserve full argument signatures for ALTER FUNCTION and zero-argument signatures across CREATE/DROP/GRANT/ALTER identity extraction.
4. RLS policy lineage: use the PostgreSQL `table` field for policy identity; reduce CREATE POLICY + ALTER POLICY while preserving clauses omitted by ALTER and rejecting changed table identity.
5. Enum evolution: reduce CREATE TYPE AS ENUM with ADD VALUE (append/before/after) and RENAME VALUE; duplicate/unknown-neighbor cases fail closed.
6. Benefit UI safety: disable the Top Up control until a real payment-intent and signed settlement path exists; no fake wallet crediting or informational click masquerading as a payment action.

## Source files changed

- `tools/schema_reconciliation/reconcile.py`
- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_dependency_identity_binding.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`
- `components/views/benefit-credit-view.tsx`
- `docs/implementation/task1-dependency-binding-hardening-20261125.md`
- `docs/implementation/task1-typed-drop-lineage-20261125.md`
- `docs/implementation/task1-rls-policy-reducer-20261125.md`
- `docs/implementation/task1-rls-enum-reducers-20261125.md`
- `docs/implementation/phase09-benefit-topup-safety-gate-20261125.md`

## Verification and safety boundary

- Regression test source was added for dependency identity, DROP multi-target/function identities, RLS policy evolution and enum evolution. Tests were not executed under the current Master PRD Section 37 restriction.
- No reconciliation graph was regenerated from the old observed snapshot; fresh observed schema/security/dependency evidence is required.
- No Supabase query or write, migration apply, staging, provider call, payment call or deployment was performed.
- Copy Engine implementation was source-confirmed as already present: nine modes, structured output validation, metered gateway adapter, catalog entry and registration in `DurableOpenManusRuntime`. No duplicate engine or runtime was added.

## Remaining

- Full reducers for sequence, composite/range/domain types, function/procedure option evolution, trigger changes and remaining ALTER TABLE subtypes.
- Complete ACL effective state with grantor/role membership/default ACL/ownership and observed catalog binding.
- Search-path-aware dependency resolution and exact pg_depend coverage.
- Fresh full catalog/security/dependency snapshots and independent migration execution receipts.
- Regenerate expected graph/reconciliation artifacts from current source and fresh evidence.
- Complete remaining backend and Phase 09 customer/admin integration domains; payment provider is not configured, so wallet top-up remains safely disabled.

Task 1 and Phase 09 remain IN PROGRESS. This increment is not a global parity or release acceptance claim.
