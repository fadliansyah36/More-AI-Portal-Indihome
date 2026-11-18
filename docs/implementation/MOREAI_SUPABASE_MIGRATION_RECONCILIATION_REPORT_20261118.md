# MoreAI Supabase Migration History Reconciliation — 2026-11-18

Repository: `fadliansyah36/More-AI-Portal-Indihome`  
Branch: `main`  
Audit baseline before archive commit: `2069f9cc55bff7e98a0e3caefad5b3bd59562950`  
Supabase project: `uunfgimtokhucegqbpce`  
Mode: read-only database inspection plus repository evidence/archive commits. No migration, DDL, reset, repair, seed, or production data mutation was executed.

## 1. Evidence created

- `MOREAI_SUPABASE_MIGRATION_PARITY_20261118.csv`: 116 applied history rows + 6 repository-only rows.
- `MOREAI_SUPABASE_MIGRATION_HISTORY_116_ROW_EVIDENCE_20261118.csv`: 116 rows with statement count, rollback count, reconstructed MD5 and SHA-256.
- `MOREAI_SUPABASE_HISTORICAL_MIGRATION_ARCHIVE_MANIFEST_20261118.md` and 32 JSON archive records under `migration-history-archive/`.
- `MOREAI_SUPABASE_REPO_ONLY_MIGRATION_VERIFICATION_20261118.csv`: six file-level verification records.
- `MOREAI_SUPABASE_MIGRATION_ANOMALY_REGISTER_20261118.csv`: anomaly status, impact and next action.

## 2. Applied migration history — 116 rows

Read-only query confirms 116 rows. Every row contains exactly one element in the statements array: 113 are SQL text and 3 are migration-path references (not SQL text). Three rows have a non-null rollback array; 113 have NULL rollback. The history table has no checksum column. MD5/SHA-256 values are reconstructed evidence, not historical execution checksums. Use the corrected file `MOREAI_SUPABASE_MIGRATION_HISTORY_116_ROW_RECONCILIATION_CORRECTED_20261118.csv`; the earlier 116-row evidence CSV hashes the three path references as values and is superseded.

The three rollback-bearing rows are:
- `20261111030000 moreai_enqueue_chat_run`
- `20261111033000 moreai_llm_reserve_with_entitlement_quota`
- `20261111040000 moreai_llm_quota_settlement_reconciliation`

## 3. Historical source recovery — 32 rows

All 32 applied history rows with no same-name source in current `supabase/migrations` were recovered into immutable JSON archive records. Each record preserves the original statement array, rollback value, version/name, creator/idempotency metadata and per-statement SHA-256.

All 32 contain one SQL statement and NULL rollback. A basic credential-pattern scan returned no matches. This limited scan is not a complete secrets audit. Archive files are under `docs/implementation/migration-history-archive/`; they are intentionally outside the active migration directory and must never be replayed.

Git path-history provenance was sampled for five representative historical paths; all five returned no path commits. The remaining 27 paths have not yet been individually checked against Git history. Database-history provenance is preserved; original Git commit/blob provenance remains REVIEW_REQUIRED.

## 4. Repository SQL content comparison — 85 files

Every current SQL migration file was fetched from `main` and its exact SQL string MD5 was compared to stored applied statement MD5 values. This is a raw string comparison, not normalized SQL or semantic equivalence.

Observed file-level classification (corrected after identifying three history path references):
- 54 repository files have an exact raw SQL content match to at least one applied SQL history statement. One is a different-name alias described below.
- 23 same-name repository files have a raw SQL hash mismatch against their applied SQL history statement.
- 3 exact version+name history rows store a migration path reference rather than SQL text; their SQL content cannot be compared from the history row.
- 5 repository files have no matching name or exact SQL content in applied history.
- Of 7 exact version+name matches, 3 are path-reference-only, 3 have exact SQL content matches, and 1 has a raw SQL content mismatch.

All 23 SQL-content mismatches were additionally compared after collapsing whitespace and stripping SQL line/block comments using a conservative regex normalization; all 23 still differ. This is not a SQL parser/AST equivalence proof, and differences inside quoted or dollar-quoted strings may affect normalization. The per-file MD5 evidence and normalized mismatch status are recorded in `MOREAI_SUPABASE_MIGRATION_SQL_MISMATCH_REVIEW_20261118.csv`. No equivalence claim is made; exact SQL diff and semantic classification remain required.

## 5. Duplicate applied names

Five logical names occur twice in applied history:
- Identical statement hash pairs: `moreai_customer_learning_progress`, `moreai_knowledge_rag_vector`, `moreai_workspace_file_cas_versioning`.
- Divergent statement hash pairs: `moreai_workspace_file_version_history`, `moreai_workspace_restore_approval_key`.

All history rows are retained. No deduplication, deletion or history repair was performed.

## 6. Six repository-only migration files

1. `20261111110000_moreai_durable_run_event_outbox.sql`: not present by name, but its SQL MD5 exactly matches applied history `20261111091531_moreai_durable_run_event_outbox_phase_07a`. The `agent_run_event_counters` relation and `moreai_worker_append_run_event` function exist. Treat as already represented by an applied content alias; do not apply.
2. `20261116250000_moreai_browser_human_takeover_grants.sql`: grants table and three functions absent. Not applied; approval intent unproven.
3. `20261116260000_moreai_browser_takeover_run_terminal_revocation.sql`: trigger function absent; depends on takeover grants migration.
4. `20261116270000_moreai_browser_takeover_logout_revocation.sql`: logout revocation function absent; depends on grants table.
5. `20261116280000_moreai_browser_takeover_command_queue.sql`: command table and functions absent. Static inspection found malformed SQL at line 54 (incomplete worker-ID regex/condition joined to SELECT), duplicated function definitions and orphaned fragments. BLOCKED; must not apply.
6. `20261116300000_moreai_browser_preview_requests.sql`: preview table and two worker functions absent; not applied.

For items 2–6, the evidence proves not applied by name/content and key objects are absent. It does not prove that the product owner intentionally deferred them. They remain REVIEW_REQUIRED/BLOCKED, not “intentionally pending”.

## 7. Migration risk and status

| Area | Status |
|---|---|
| 116 history row inventory and statement hashes | COMPLETE |
| 32 historical SQL archive records | RECOVERED; Git provenance partial |
| 6 repository-only verification | COMPLETE as read-only classification; 5 remain approval/review blockers |
| Duplicate name/content review | REVIEW_REQUIRED |
| 26 raw SQL mismatches | REVIEW_REQUIRED |
| Full schema drift comparison | NOT STARTED |
| Migration execution | NOT PERFORMED |

## 8. Acceptance decision

**Task 1 is NOT COMPLETE and P1 remains IN_PROGRESS.** Blocking items:
1. Review all 23 raw SQL mismatches with exact diff and semantic classification; recover/verify the 3 path-reference rows against immutable source evidence.
2. Reconcile the two divergent duplicate-name pairs.
3. Individually search Git history for all 32 historical source paths and update provenance where recoverable.
4. Obtain owner/reviewer decision on the five genuinely unapplied migration files; repair the malformed command-queue migration before it can be considered.
5. Complete read-only schema drift comparison (columns, constraints, indexes, triggers, functions, RLS, grants and Storage policies).

No Task 2 security advisory work or Phase 04–09 implementation is started before Task 1 is resolved under the requested sequence. No Supabase migration was applied.
