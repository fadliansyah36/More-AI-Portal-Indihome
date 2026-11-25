# Task 1 — PostgreSQL Domain Identity and Semantic Reducer

- Date: 2026-11-25
- Baseline HEAD before this increment: `5e2dc50c33b082c657600a0a9885448222f67bf2`
- Source implementation commit: `8f2f9bcda35f3ce55e98d19b5fa4d8ba6dc835f0`
- Domain-state correction: `e31c2cccf0545e6fe54e7e26a79f5864bda05ced`
- Regression-source commits: `339c93384a08bf316af285ef5df3b7eeff051ef4`, `0638f2aae0d734c95baef675cb9cf4e4d7cccca0`
- Scope: PostgreSQL `CreateDomainStmt` / `AlterDomainStmt` source lineage.

## Implemented

1. Registered `AlterDomainStmt` as a DOMAIN ALTER event.
2. Corrected CREATE DOMAIN identity extraction: `domainname` identifies the created domain; `typeName` is only the underlying base type and must not be used as the object key.
3. Added fail-closed source/target domain identity binding between CREATE and ALTER.
4. Added explicit folding for named constraint add/drop/validate, NOT NULL set/drop, and default set/drop.
5. Kept unsupported subtypes, missing identities, ambiguous constraint names, and invalid validation transitions as `NOT_VERIFIABLE`.
6. Prevented stale CREATE-time default/NOT NULL constraint AST nodes from contradicting later ALTER state.
7. Added focused regression source for object identity, validation, default/nullability, named constraint add/drop, and mismatched domain identity.

## Files changed

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`

## Verification and restrictions

Regression source was added but **not executed**. No test, build, lint, type-check, provider call, migration apply, Supabase mutation, staging, or deployment was run. The implementation is therefore source-implemented but runtime-unverified. No production database state is claimed.

## Remaining Task 1 work

- Range type definition and option semantics.
- Composite type attribute lineage and ALTER TYPE/ALTER TABLE binding.
- Trigger identity/definition completeness beyond current enablement reducer.
- ACL grantor/role resolution and default privilege parity.
- Ownership source/target object identity and historical owner lineage.
- Dependency graph semantic binding, edge direction/type and drop/cascade effects.
- Migration execution provenance reconciliation and global expected-versus-observed schema parity.

Task 1 remains `REVIEW_REQUIRED`. This increment does not certify global schema parity or Phase 05 completion.
