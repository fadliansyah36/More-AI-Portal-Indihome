# Task 1 — RLS policy and enum type semantic reducers

Date: 2026-11-25
Branch: `main`

## Implemented

### RLS policy lineage
- Corrected `CreatePolicyStmt` / `AlterPolicyStmt` identity extraction to read PostgreSQL's `table` AST field.
- Added a reducer for CREATE POLICY followed by ALTER POLICY.
- Only explicitly supplied ALTER clauses update the stored state. Omitted `roles`, `qual` and `with_check` fields are preserved.
- Policy/table identity changes and unsupported event chains fail closed as `NOT_VERIFIABLE`.

### Enum type evolution
- Added a reducer for CREATE TYPE AS ENUM with ALTER TYPE ADD VALUE and RENAME VALUE events.
- Supports appending values and inserting values before/after an existing label.
- Supports renaming an existing enum label.
- Duplicate values with `IF NOT EXISTS` are treated as no-op; invalid or missing neighbor identities remain `NOT_VERIFIABLE`.
- The reducer does not claim support for composite, range, domain or arbitrary ALTER TYPE operations.

## Changed files

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`

## Verification boundary

Regression source was added for RLS policy identity and partial ALTER semantics, enum value insertion ordering, enum label rename, and unknown-neighbor failure. Tests were not executed under the current Master PRD Section 37 restriction. No Supabase access/mutation, migration apply, staging, provider call or deployment was performed.

## Remaining Task 1 work

- Reducers for sequences, composite/range/domain types, function/procedure alterations, trigger evolution and remaining ALTER TABLE subtypes.
- Exact observed policy/enum definitions and security fingerprints.
- Complete ACL grantor/ownership/effective privilege reconciliation.
- Search-path-aware dependency binding and complete pg_depend identity coverage.
- Fresh observed catalog/security/dependency evidence and independent migration execution receipts.
- Regenerate graph and reconciliation artifacts from current source and fresh evidence.

Task 1 remains IN PROGRESS / NOT COMPLETE.
