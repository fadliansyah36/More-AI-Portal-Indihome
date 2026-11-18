# Migration lineage and provenance map — Task 1

As-of: 2026-11-18. All Supabase evidence was read-only.

## Lineage

20261115084424 moreai_openfuse_persistent_browser_sessions
  -> creates moreai_browser_sessions and moreai_browser_session_events
  -> initial event_type: created, restored, state_saved, closed, expired
20261116083451 moreai_browser_session_close_event_constraint
  -> adds close_requested
20261116083458 moreai_browser_profile_retention
  -> adds profile_retention_after, profile_deleted_at, profile_retention_notified_at
  -> event_type adds profile_retention_eligible, profile_deleted
20261116083502 moreai_browser_profile_retention_rpcs
  -> claim/ack RPCs write profile_retention_eligible and profile_deleted
20261116250000 / 260000 / 280000 / 300000
  -> unapplied repository sources attempt further CHECK replacements;
     four source definitions remove prior lifecycle values

## Evidence status

- History records 20261115084424, 20261116083451, 20261116083458 and 20261116083502 exist in Supabase history. Stored SQL for each was retrieved read-only.
- Current live event CHECK exactly retains the eight values from the 16083458 definition. The 16083502 RPC source inserts the two profile retention events.
- Live browser session/event tables and retention columns exist. This supports recorded lineage and actual object presence, but is not a signed execution receipt for each historical migration.
- All five browser takeover/preview sources in current main have no history rows.
- Their IDs are 14-digit strings with invalid hour components (25, 26, 27, 28 and 30). The IDs are not valid wall-clock timestamps in YYYYMMDDHHMMSS form. No source commit or owner-approved replacement timestamp was found in linked GitHub search.
- The 15084819 source is recovered historically at commit cc5563e...; 619/619 ordered SQL tokens match the stored history SQL. Current main 15090000 remains duplicate alias of 15100000 / history 15085314.

## Provenance limitation

Migration history row + matching SQL source + current object effect provide execution provenance support, not execution provenance confirmation. History has no native checksum or independent deployment receipt. Do not infer exact executed bytes from history metadata alone.

## Execution continuation addendum — 2026-11-18

The original source identities `20261116250000`, `20261116260000`, `20261116270000`, `20261116280000`, and `20261116300000` are retained as archived source evidence only. Their corrected active source paths are `20261116162500`, `20261116162600`, `20261116162700`, `20261116162800`, and `20261116163000`. All five corrected sources remain absent from applied history and unapplied. The eight existing browser event types are preserved by corrected active SQL. The original 15090000 and 11110000 alias paths are archived and removed from active migrations.

The 15084819 source is recovered at Git commit `cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31` with 619/619 ordered SQL tokens matching the history statement. A 513-row regex DDL candidate map from 106 history versions is committed separately; it is not a complete SQL parser or execution receipt. The all-schema observed catalog snapshot is fingerprinted separately. History rows alone are not treated as proof of exact deployed bytes.

## Path-reference source identity addendum

The history statement values for 20261111030000, 20261111033000 and 20261111040000 are path references. They now resolve to exact current-main files:

- 20261111030000 → `supabase/migrations/20261111030000_moreai_enqueue_chat_run.sql` (Git blob `5496f3f51100b843d9b5e96032e52cc10de482d3`).
- 20261111033000 → `supabase/migrations/20261111033000_moreai_llm_reserve_with_entitlement_quota.sql` (Git blob `9b4984abcd100c558a50e676f0f39a7296d49b66`).
- 20261111040000 → `supabase/migrations/20261111040000_moreai_llm_quota_settlement_reconciliation.sql` (Git blob `7bb174c960aeabba71c49a84e95f30a13552eece`).

This closes the path-to-source mapping gap only. It does not attest exact deployed bytes or independent execution.


## Static expected schema baseline addendum — 2026-11-18

The source-derived expected-object event baseline is committed as `TASK1-STATIC-EXPECTED-OBJECT-BASELINE-20261118.csv` (513 regex/lexical DDL candidates across 106 applied history versions). The human-readable category matrix and trust boundary are in `TASK1-STATIC-EXPECTED-SCHEMA-BASELINE-20261118.md`. This baseline is source-traceable, not replay-validated. The source inventory `TASK1-MIGRATION-SOURCE-INVENTORY-20261118.csv` records 121 active migration files, 34 historical SQL archive records and 7 preserved malformed/duplicate source files, with Git blob SHA-1 and file sizes.

The five browser source originals remain preserved; corrected active sources are 20261116162500, 20261116162600, 20261116162700, 20261116162800 and 20261116163000. Their source corrections preserve the eight applied lifecycle event values and append feature-specific values, but all five remain absent from history and unapplied. The malformed command queue report now identifies 20261116162800 as the corrected active source and the old 20261116280000 path as archived provenance only.

Static event lineage does not prove exact execution. The 513 rows are DDL candidates, not unique final objects or AST-normalized definitions. Global semantic expected-vs-observed parity remains NOT_VERIFIABLE; no category is declared globally MATCH. The user waived replay/testing; no replay, migration apply, production write, staging or deployment occurred.


The recovered historical SQL source is now also preserved byte-for-byte at `docs/implementation/migration-source-archive/20261115084819_moreai_agent_model_preferences.historical.sql` with Git blob SHA-1 `b7278df23425678a3009cb5c15f20e7c6cf53327`. The AST graph parser includes this historical source as an archive variant linked to applied history `20261115084819`; its archived events are merged into the expected lineage only because the migration ID is present in the read-only history snapshot. The archive file is not an active migration and provides no independent deployed-byte receipt.
