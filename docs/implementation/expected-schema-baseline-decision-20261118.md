# Expected schema baseline decision — 2026-11-18

Decision: INSUFFICIENT_EVIDENCE. Full baseline selection remains BLOCKED.

The applied history (116 rows) is the strongest lineage source, augmented by recovered historical SQL. It is not a complete source set with deterministic replay provenance. Current main has 85 migration files, 23 same-name differences (22 previously explained; 15084819 historical source now recovered), and five repository-only browser sources whose identifiers have invalid timestamp hour components. Live Supabase introspection is a valid observed-state snapshot, not an expected-state definition. The Master PRD v1.2 Draft is not DDL-complete.

A narrow expected schema contract is supported for the browser event CHECK and retention columns from applied history 16083451/16083458, and the current live CHECK matches that contract. This cannot be generalized to all schemas, tables, columns, indexes, functions, triggers, views, RLS policies, grants, ownership, extensions or dependencies.

Required to unblock:
1. Owner-approved immutable schema-only dump from a named known-good snapshot/environment, with SHA-256, source project identity, timestamp and scope; or explicit approval for offline-only replay in a disposable isolated database that cannot connect to Supabase.
2. Complete migration source lineage mapping for all 116 history records, including missing source files and the 23 current-main comparisons.
3. An owner-approved migration naming/source disposition for the five invalid timestamp IDs and current duplicate path 15090000.
4. Complete expected grants/RLS/ownership/function-privilege baseline.
5. Observed schema capture with environment designation and timestamp for the exact comparison target.

No schema migration, replay, DB write, test or deployment was performed.
