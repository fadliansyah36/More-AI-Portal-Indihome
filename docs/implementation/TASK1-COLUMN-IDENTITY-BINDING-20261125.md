# MoreAI Task 1 — Column Alteration Identity Binding

Date: 2026-11-25
Branch: `main`
Starting HEAD: `d2d17f3552334c87fb8019a0385d67fafc2bed8c`

## Implemented

Updated `tools/schema_reconciliation/schema_graph.py::_reduce_table_subobject_history`:
- Column ALTER events now require a non-empty source `ColumnDef.colname`.
- Each `AlterTableCmd.name` must be present and exactly match the source column name.
- Missing names and mismatched names fail closed with `NOT_VERIFIABLE`.
- Existing ALTER COLUMN TYPE USING expression preservation remains intact.

Updated `tools/schema_reconciliation/tests/test_schema_graph.py`:
- Existing reducer fixtures now carry explicit column names.
- Added a regression case proving that an ALTER targeting a different column cannot be folded into the source column's history.

Commits:
- `a286ddd055871b2bf1aa8b43c76bfa0f1f73993c` — exact column identity binding.
- `6417e047e4184fb1960cfd99397bf2c241790022` — regression source and explicit fixture identities.

## Verification and safety

No test/build/lint/typecheck execution, provider call, staging, migration apply, Supabase data mutation or deployment was performed. Master PRD v1.2 Section 37 remains restrictive. Regression source is not a test-pass claim. No database state was changed.

## Remaining

Task 1 remains `REVIEW_REQUIRED`. Exact column identity binding and USING-expression preservation are narrow improvements; complete column command coverage, type/domain/range/composite semantics, constraints, ACL/ownership, dependencies, migration provenance and global expected-vs-observed reconciliation remain open or not verifiable.
