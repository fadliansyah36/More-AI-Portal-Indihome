# Task 1 — RLS policy semantic reducer

Date: 2026-11-25
Branch: `main`

## Implemented

- Corrected policy identity extraction to use PostgreSQL's `table` AST field for `CreatePolicyStmt` and `AlterPolicyStmt`; index and trigger statements continue to use their `relation` field.
- Added a source reducer for `CREATE POLICY` followed by `ALTER POLICY`.
- The reducer updates only clauses explicitly present in the ALTER statement. Omitted roles, USING and WITH CHECK clauses are preserved rather than being interpreted as NULL/deletion.
- The reducer verifies that policy name and table identity remain unchanged across the event chain.
- Unsupported event shapes and ALTER-without-CREATE lineage remain `NOT_VERIFIABLE`; the reducer does not infer an observed policy state.

## Changed files

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`

## Verification and safety

Regression source covers explicit clause updates, preservation of omitted WITH CHECK, preservation of command/permissive attributes, table identity mismatch, and policy identity extraction. Tests were not executed under the current Master PRD Section 37 restriction. No Supabase query/write, migration apply, staging, provider call or deployment was performed.

## Remaining Task 1 work

- Extend equivalent safe reducers to remaining object families and ALTER subtypes.
- Bind expected policy definitions to exact observed pg_policy identities/expressions and security fingerprints.
- Complete effective ACL/ownership and grantor provenance.
- Obtain fresh observed catalog, security and dependency snapshots and independent migration execution evidence.
- Regenerate expected graph/reconciliation artifacts from current source and current evidence; do not treat the older 2026-11-18 catalog snapshot as current.

Task 1 remains IN PROGRESS / NOT COMPLETE.
