# Task 1 — Full Schema Inventory & Drift Report
Date: 2026-11-18
Project: `uunfgimtokhucegqbpce` (PostgreSQL 17.11; ACTIVE_HEALTHY)
Method: read-only PostgreSQL catalog introspection and SELECT only. No DDL, migration apply, DB writes, staging or deployment.

## Evidence baseline
- Supabase migration history: 116 rows; latest version `20261116113852`.
- Current repository migration directory: 85 SQL files.
- Historical/repository parity remains incomplete (32 applied history names without same-name current source; 6 repo-only source files including one applied-content alias; 23 same-name SQL mismatch records).
- No complete immutable schema dump or authorized offline migration replay baseline was available. Therefore catalog inventory is observed state, not proof of expected-state parity.

## Live public schema inventory
| Object category | Count / state |
|---|---:|
| Base tables | 94 |
| Views | 1 (`learning_path_progress_summary`) |
| Materialized views | 0 |
| Columns (non-dropped) | 922 |
| Constraints | 562 |
| - CHECK | 224 |
| - FOREIGN KEY | 185 |
| - PRIMARY KEY | 94 |
| - UNIQUE | 59 |
| - EXCLUSION | 0 |
| Indexes | 245 |
| - Valid / ready | 245 / 245 |
| - Unique | 163 |
| - Partial | 28 |
| - Expression | 2 |
| Functions/procedures | 98 |
| - SECURITY DEFINER | 56 |
| Non-internal triggers | 5 |
| RLS policies | 95 |
| RLS enabled on base tables | 94/94 |
| FORCE RLS | 0/94 |
| Public sequences | 0 |
| Public enums/domains | 0 |

The database has 7 extensions: pg_cron 1.6.4, pg_stat_statements 1.11, pgcrypto 1.3, plpgsql 1.0, supabase_vault 0.3.1, uuid-ossp 1.1, vector 0.8.2. Twelve enum types are in Supabase-managed auth/realtime/storage schemas, not public.

## Security and RLS snapshot
- 95 public policies: 44 permissive server-deny policies and 37 restrictive server-deny policies (both use false for USING and WITH CHECK); remaining 14 are owner/member-scoped policies.
- All 94 public base tables have RLS enabled. None has FORCE ROW LEVEL SECURITY.
- 56 SECURITY DEFINER functions were observed; all 56 returned false for anon EXECUTE and authenticated EXECUTE, and true for service_role EXECUTE.
- `information_schema.role_table_grants` returned grants only for postgres (665 rows) and service_role (653 rows); no anon/authenticated table grants were observed.
- These are observed catalog facts. They do not replace comparison to a canonical expected grant/policy snapshot.

## Confirmed source-to-live risk findings
1. **Event-type constraint regression in unapplied migration sources.** Live `moreai_browser_session_events_event_type_check` currently permits `created`, `restored`, `state_saved`, `close_requested`, `closed`, `expired`, `profile_retention_eligible`, and `profile_deleted`. Migration 16250000 and 16260000 recreate the check without `close_requested`, `profile_retention_eligible`, or `profile_deleted`. Migration 16280000 and 16300000 preserve `close_requested` but still omit the two profile-retention events. The table currently has zero event rows, but future profile-retention/close events would fail after such a replacement. This is a migration source regression, not a live drift finding.
2. **Model preference source identity.** Live `moreai_customer_agent_configs.preferred_model_id` and partial index exist. Applied history 20261115084819 created them. Repo `20261115090000` has the same Git blob as `20261115100000` and exact SQL MD5 matching applied 20261115085314 attachment compatibility, not 15084819. This leaves a source mapping/provenance gap for the original migration.
3. **Unapplied browser objects.** The five unapplied migrations' grants/commands/preview objects and associated functions are absent. Their absence is expected while migrations remain unapplied; do not classify this as live schema drift.
4. **Chat enqueue overloads.** The live catalog contains both 7-argument and 8-argument `moreai_enqueue_chat_run_with_config` overloads. Their history is present across earlier applied migrations, but the full expected contract requires source/history-to-FastAPI reconciliation.

## Drift classification
- `POTENTIAL_DRIFT`: 2 source-to-live risks (event-type constraint regression in unapplied SQL; model-preference source identity).
- `EXPECTED_DIFFERENCE`: unapplied browser takeover/preview objects absent.
- `NOT_VERIFIABLE`: full expected-vs-observed definitions for tables, columns, constraints, indexes, functions, triggers, views, grants, RLS, extensions, and dependencies. A full schema drift-free claim is not supported.

## Decision register
See `MOREAI_TASK1_SCHEMA_DRIFT_MATRIX_20261118.csv` and `MOREAI_TASK1_FULL_SCHEMA_INVENTORY_20261118.csv`.
