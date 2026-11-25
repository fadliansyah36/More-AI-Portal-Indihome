# MoreAI Task 1 — ALTER COLUMN TYPE USING Expression Preservation

Date: 2026-11-25
Branch: `main`
Starting HEAD: `bfb24ee5541b1bf02714531b837643f27efba303`

## Implemented

Updated `tools/schema_reconciliation/schema_graph.py::_reduce_table_subobject_history`:
- For `AT_AlterColumnType`, continue reducing the explicit target `typeName`.
- Preserve a non-null `AlterTableCmd.transform` expression as `ColumnDef.type_change_using`.
- Remove a prior `type_change_using` value when a later type-change event explicitly has no transform, preventing stale conversion logic from leaking into the final state.
- The expression is copied as normalized AST data; it is not executed or simplified.

Added regression source in `tools/schema_reconciliation/tests/test_schema_graph.py` for preserving a USING expression and clearing a stale expression after a subsequent plain type change.

Commits:
- `a0442c77eba5e4efb15ff86a29ed99a4bef21312` — preserve type-change USING expression.
- `3637238f77752644dbfc8a29a9f2a834e407f5e7` — regression source.

## Verification and safety

Tests/build/lint/typecheck were not run. The Master PRD v1.2 Section 37 current-workstream constraints prohibit real test execution, staging, provider calls, migrations applied, Supabase data mutation and deployment. Regression source is not test-pass evidence. No database or production data was changed.

## Remaining

Task 1 remains `REVIEW_REQUIRED`. This narrow column reducer improvement does not certify all column subcommands, constraint evolution, type/domain/range/composite semantics, ACL/ownership, dependency graph, migration provenance or global expected-vs-observed schema parity.
