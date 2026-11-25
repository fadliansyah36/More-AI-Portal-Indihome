# Task 1 — Typed DROP and function ACL identity correction

Date: 2026-11-25
Branch: `main`
Baseline: `bdd62195a0997ed2789cff52d15cf55d9b7166ce`

## Implemented

- PostgreSQL `DropStmt` targets are now decoded as typed AST objects rather than flattening all nested string nodes into one object name.
- Multi-target DROP statements preserve one identity per target.
- Supported DROP object kinds map to the same semantic object classes used by corresponding CREATE events (tables, indexes, functions, procedures, sequences, views, types, domains, schemas, extensions, roles, databases, publications, subscriptions and foreign tables).
- Function/procedure identities preserve their argument signatures consistently across CREATE, DROP, GRANT and ownership AST extraction.
- Zero-argument functions retain the explicit `()` signature instead of being represented as an unknown signature or an unqualified bare name.
- Unknown DROP object kinds remain generic rather than being guessed into a false object binding.

## Source changes

- `tools/schema_reconciliation/schema_graph.py`
- `tools/schema_reconciliation/tests/test_schema_graph.py`

## Evidence and safety

Focused regression source covers multi-target DROP tables, typed DROP functions, zero-argument function GRANT/DROP identity, and preservation of distinct object targets. Tests were not executed under the current Master PRD Section 37 restriction. No Supabase read/write, migration apply, staging, provider call or deployment was performed.

This correction improves migration-to-object lineage; it does not close all PostgreSQL object reducers or establish global schema parity.

## Remaining

- Resolve relation/function/type names against captured search_path and exact pg_depend identities.
- Complete semantic evolution reducers for types, sequences, functions, triggers, RLS policies, ACL grantors/ownership and ALTER subtypes.
- Obtain current read-only observed catalog/security/dependency snapshots and exact migration execution evidence.
- Regenerate the graph and reconciliation artifacts from current source and current observations; keep global no-drift disabled until coverage is complete.

## Next

Continue Task 1 reducer coverage and exact object lineage. Do not claim Task 1 completion based on this increment alone.
