# Task 1 — Dependency Identity Binding Hardening

Date: 2026-11-25
Branch: `main`
Baseline: `69dcc4200be589375247278a2d4a5f0f79964822`

## Scope

Harden PostgreSQL AST-to-`pg_depend` candidate matching so the reconciliation tool cannot claim an exact dependency binding from an ambiguous schema suffix or relation prefix.

## Change

- `tools/schema_reconciliation/reconcile.py`: function references now compare the complete qualified function name while allowing the catalog's rendered argument signature; type references require exact qualified identity; relation references require exact identity.
- Unqualified references no longer bind to an arbitrary schema-qualified catalog identity. PostgreSQL `search_path` is required to resolve that ambiguity, and is not inferred by this matcher.
- Relation-prefix matching no longer treats a column-like identity as an exact relation match.
- Added focused regression cases in `tools/schema_reconciliation/tests/test_dependency_identity_binding.py`.

## Safety and verification

- Source-only change. No Supabase query/write, migration apply, provider call, staging action or deployment was performed.
- Tests were added but not executed in this session. Master PRD Section 37 currently prohibits real test execution for this workstream; the repository CI workflow remains the execution path once that restriction is lifted.
- Generated expected/observed reconciliation artifacts were not regenerated because the committed observed snapshots are static captures and current PRD governance does not authorize replacing them with guessed or partial evidence.
- This change intentionally may reduce the number of dependency candidates reported as bound. That is preferable to false-positive semantic evidence. Unqualified candidates remain unbound until captured search-path evidence or an exact catalog identity is available.

## Remaining Task 1 work

- Add evidence-backed search-path resolution for unqualified relation/function/type references.
- Complete supported reducers for ALTER TABLE, constraints, ACL/grant/revoke, ownership, types, sequences, functions, triggers and RLS.
- Reconcile source events against fresh observed catalog snapshots and exact applied migration provenance.
- Regenerate graph and reconciliation artifacts from the current code and current read-only snapshots.
- Keep global no-drift disabled until source coverage and semantic comparisons are complete.

## Next phase

Continue Task 1 semantic reducer and catalog evidence closure. Do not declare Task 1 complete from this hardening change alone.
