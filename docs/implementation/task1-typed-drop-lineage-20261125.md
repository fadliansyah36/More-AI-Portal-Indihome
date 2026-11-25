# Task 1 — PostgreSQL DROP lineage and function signature repair

Date: 2026-11-25
Branch: `main`
Baseline: `bdd62195a0997ed2789cff52d15cf55d9b7166ce`

## Implementation

- Added typed DROP target decoding in `tools/schema_reconciliation/schema_graph.py`.
- Multi-target DROP statements now produce separate object identities instead of flattening every nested AST string into one malformed identity.
- DROP object kinds map to matching semantic object classes where the AST exposes a supported PostgreSQL object kind.
- Function and procedure signatures are retained consistently across CREATE, DROP, GRANT and ownership extraction.
- Zero-argument function signatures are represented as `()`, matching the CREATE function identity.
- Unknown object types are kept generic and are not guessed into a concrete semantic class.

## Changed files

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`
- `docs/implementation/task1-typed-drop-lineage-20261125.md`

## Verification boundary

Regression cases were added for multiple DROP targets, DROP FUNCTION signature, and zero-argument function GRANT/DROP identity. Tests were not executed because the current Master PRD Section 37 workstream restriction prohibits real test execution. No database access or mutation, migration apply, staging, provider call or deployment was performed.

## Status

This closes a source-lineage identity defect; it does not establish full Task 1 completion. ALTER reducers, ACL/ownership semantics, RLS/type/sequence/function/trigger evolution, exact dependency binding, global reconciliation and execution provenance remain open. Reconciliation artifacts were not regenerated from the older static observed snapshot; a fresh observed catalog evidence set is required before presenting new global counts.

## Next

Continue Task 1 reducer coverage and exact migration/object provenance. Then continue the existing Phase 04–09 backend/frontend integration sequence without duplicating modules already present.
