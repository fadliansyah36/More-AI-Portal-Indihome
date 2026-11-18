# MoreAI Supabase Migration Parity Audit — 2026-11-18

Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Supabase project: `uunfgimtokhucegqbpce`
Method: read-only GitHub tree inspection and read-only query of `supabase_migrations.schema_migrations`. No migration, DDL, SQL write, reset, seed, or deployment was executed.

## Summary

| Measure | Count |
|---|---:|
| Applied migration-history rows in Supabase | 116 |
| SQL migration files in current main | 85 |
| Exact version + name matches | 7 |
| Current repo files whose logical name exists in history but version differs | 72 |
| Applied history rows with a same-name repo file but version drift | 77 |
| Applied migration names with no current repo source file | 32 |
| Current repo migration files not present as applied by name | 6 |
| Logical migration names duplicated in applied history | 5 |

The 77 applied rows with a name match map to 72 current repository files because five logical names have duplicate applied history entries:
- `moreai_workspace_file_cas_versioning`
- `moreai_workspace_file_version_history`
- `moreai_workspace_restore_approval_key`
- `moreai_customer_learning_progress`
- `moreai_knowledge_rag_vector`

The 116-row applied history plus 85 current files are fully represented in `MOREAI_SUPABASE_MIGRATION_PARITY_20261118.csv` (116 applied rows + 6 repo-only rows = 122 matrix rows).

## Applied history vs repository source

### Exact matches — 7

Only seven current migration files match both the applied version and migration name exactly. The parity matrix identifies each.

### Same logical name, different version — 72 repository files / 77 applied rows

Most current repository migration filenames use different timestamps from the versions recorded in Supabase. Examples include:
- `moreai_tool_approval_lifecycle`: repo `20261111050000`, applied `20261111061443`.
- `moreai_workspace_file_version_history`: repo `20261112100000`, applied `20261112044816` and `20261113002544`.
- `moreai_skill_intelligence_registry`: repo `20261114100000`, applied `20261115084346`.
- `moreai_server_only_deny_rls_policies`: repo `20261116083600`, applied `20261116083654`.
- `moreai_browser_capacity_leases`: repo `20261116090000`, applied `20261116083856`.

Name similarity does not prove SQL content identity. The current repo file cannot safely be assumed equivalent to an applied migration solely because the name matches.

### Applied names with no current source — 32

These include early Phase 02 identity/partner/permission/billing/worker/LLM migrations and several Phase 07/notification/Edutech history names. The current repo tree does not contain a file with the same logical migration name. The parity matrix lists all 32 exact applied versions/names.

### Current repo files not applied by name — 6

1. `20261111110000_moreai_durable_run_event_outbox.sql`
2. `20261116250000_moreai_browser_human_takeover_grants.sql`
3. `20261116260000_moreai_browser_takeover_run_terminal_revocation.sql`
4. `20261116270000_moreai_browser_takeover_logout_revocation.sql`
5. `20261116280000_moreai_browser_takeover_command_queue.sql`
6. `20261116300000_moreai_browser_preview_requests.sql`

These files remain source-only/unapplied at the audit time. Some represent browser takeover and preview capabilities that may have API/UI code but lack matching applied migration history. No attempt was made to apply them.

## Migration-history table structure

Read-only inspection of `supabase_migrations.schema_migrations` found columns:
- `version` (text)
- `statements` (array)
- `name` (text)
- `created_by` (text)
- `idempotency_key` (text)
- `rollback` (array)

There is no checksum column. The statements/rollback arrays may provide historical recovery evidence, but they have not yet been compared against the current repository SQL files. Therefore exact SQL identity cannot be proven for the 72 name-only matches, and the 32 missing-source migrations require recovery/provenance review.

## Risk and required action

**Migration push blocked**

- Do not run `supabase db push`, reset, repair, or apply any of the six repo-only files until migration history is reconciled.
- Do not mark Phase 05 accepted based only on the live schema table/policy snapshot.
- Next governance step: export the 116 history rows' `statements` and `rollback` arrays read-only; compare normalized SQL statements to the 85 repository files; reconstruct or archive the 32 missing historical sources with provenance; resolve the five duplicate logical names; verify whether each repo-only migration is safe and intentionally pending; then obtain product-owner approval before any future migration execution.
- All SQL changes remain forward-only; no destructive schema operation is authorized by this audit.
- P1 remains IN_PROGRESS / NOT ACCEPTED; P2 remains DRAFT / NOT ACCEPTED. Phase 05 is **REVIEW_REQUIRED**; Phase 04, 06–09 remain IN_PROGRESS / REVIEW_REQUIRED. Phase 10/11 remain BLOCKED / NOT ACCEPTED.

No database write, migration, test, build, staging, deployment or production configuration change was performed.
