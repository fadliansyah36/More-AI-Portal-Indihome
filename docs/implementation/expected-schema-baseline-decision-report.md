# Expected schema baseline decision report

Date: 2026-11-18. Decision: **BASELINE_SELECTION_BLOCKED**.

## Candidates
- Applied history (116 rows, latest 20261116113852): strongest evidence of recorded migration sequence and stored SQL, but not a complete deterministic schema source. Thirty-two applied names have no current same-name source, 23 same-name pairs have raw differences, and history has no native checksum. Provenance for 15084819 is now improved by a Git history match, but does not close all source gaps.
- Current repository migrations (85 SQL files): authoritative current branch content, but not equivalent to history. Five browser migrations are absent from history; 15090000 is a duplicate/misnamed alias of 15100000/15085314.
- Live project catalog: authoritative for what was observed in the connected Supabase project on 2026-11-18, not for what should exist. Counts: 94 tables, 1 view, 922 columns, 562 constraints, 245 indexes, 98 functions/procedures, 5 triggers, 95 policies; RLS enabled on 94/94. This is observed state only.
- Master PRD v1.2 Draft: product/architecture intent, not DDL-complete.
- Immutable complete schema dump or approved offline replay: not found/authorized.

## Selection
No single candidate can be selected as the auditable expected schema baseline. A live catalog is an observed baseline; it must not be relabelled as expected. A migration directory is not a baseline merely because it is newest. A history table records migration metadata/statements but lacks a native checksum and is not an independently validated replay.

## Confidence
- Observed catalog counts: high confidence for the read-only snapshot.
- 15084819 SQL source identity: supported by 619/619 lexical token match.
- Full expected schema object definitions: BASELINE_UNVERIFIABLE.
- Five unapplied browser objects: EXPECTED_DIFFERENCE while sources remain unapplied.
- Overall expected baseline: BASELINE_SELECTION_BLOCKED.

## Required evidence to unblock
1. Owner-approved immutable schema dump (DDL only, provenance, source environment/project ref, timestamp, hash) from a named known-good snapshot; or
2. Explicit authorization for offline-only replay into a disposable isolated database, with pinned source commits, full ordered migration source set, all missing historical SQL recovered, duplicate decisions resolved, and no connection/write access to Supabase.
3. A source-to-history checksum manifest or approved mapping for every applied migration, including source path/commit and hash.
4. Explicit environment designation for the Supabase project (production/non-production) if production assertions are required.

No live replay, test, staging, migration apply, DB write or deployment was performed.
