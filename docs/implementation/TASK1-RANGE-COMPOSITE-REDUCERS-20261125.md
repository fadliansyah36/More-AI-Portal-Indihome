# Task 1 — Range and Composite Type Semantic Reducers

- Date: 2026-11-25
- Baseline before this reducer increment: `5e2dc50c33b082c657600a0a9885448222f67bf2`
- Implementation commits: `b5d3c04348f82eb1934011284bb4aac2fd8f81c7`, `4cee74e4332da95450fcbd11a16f4b16d6d571b9`, `a571fe3245a008f884ded07ad443cb7184b9843c`, `8352a5a63a37d9e9df9e077a39284f05f4a53186`, `de758fbd1f28b0e8c2f89cb60b1cf0e7c0ae469a`, `94261391d3994aa9411aa859699ff07fd3621c40`
- Regression-source commits: `6d15315314545c94fa80cf7d9f5f971186b9bfb8`, `12090ce5f280a9a40e49021970c302b76ec56f3b`, `d58a8a557490c5819de763739ead222ac6e9ee2e`, `026e77a99e95040d51e4f9a420c53905d9fd63a5`

## Implemented

### Range types
- Validates that a CREATE TYPE AS RANGE event has a resolvable target identity and an explicit subtype parameter.
- Preserves the complete explicit parameter AST.
- Rejects duplicate/malformed parameter nodes, missing subtype, mismatched identity, and unexpected multi-event history as `NOT_VERIFIABLE`.
- Range parameter dependencies remain candidates only; they are not claimed as fully bound catalog edges.

### Composite types
- Classifies `AlterTableStmt` with `objtype=OBJECT_TYPE` as TYPE rather than TABLE.
- Normalizes composite type ALTER identity to the same schema-qualified identity used by CREATE.
- Emits distinct `TYPE_ATTRIBUTE` source events from `CompositeTypeStmt.coldeflist` and composite ALTER commands.
- Reduces composite attribute add/drop/type-change lineage with exact parent type and attribute identity.
- Unsupported rename/command shapes fail closed. Attribute-level reducer dispatch is wired into the graph builder.

### Domain AST correction carried into this increment
PostgreSQL raw AST evidence was checked against pglast's AST reference. `CreateDomainStmt.domainname` is the created object identity and `typeName` is its base type. `AlterDomainStmt` uses subtype codes `C/X/V/O/N/T` and explicit `name` / `def` fields. The reducer now follows those raw AST fields rather than guessed descriptive subtype names. Absent optional domain constraints are normalized to an empty list.

AST reference: https://github.com/lelit/pglast/blob/3aae4e93fb2229fbd01dc3d32619eca29c8bf0ff/docs/ast.rst

## Files changed

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`

## Verification restrictions

Focused regression source was added but **not executed**. No test/build/lint/type-check, provider call, migration apply, Supabase mutation, staging, or deployment was run. Source is implemented but runtime-unverified.

## Remaining Task 1 gaps

- Trigger definition and identity completeness.
- ACL grantor/role resolution and full privilege/default-ACL parity.
- Ownership source/target identity and historical owner lineage.
- Dependency graph semantic binding, edge direction/type and cascade effects.
- Migration execution provenance reconciliation.
- Global expected-versus-observed schema parity.

Task 1 remains `REVIEW_REQUIRED`; Phase 05 is not complete.
