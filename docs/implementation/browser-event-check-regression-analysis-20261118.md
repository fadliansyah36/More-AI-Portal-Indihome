# Browser event CHECK regression — corrected source status

## Applied live lineage (read-only evidence)

- `20261115084424` creates the browser session event table with the initial lifecycle vocabulary.
- `20261116083451` adds `close_requested`.
- `20261116083458` adds `profile_retention_eligible` and `profile_deleted`.
- `20261116083502` defines retention RPCs that emit the two profile-retention events.
- The live CHECK observed on 2026-11-18 contains exactly eight values: `created`, `restored`, `state_saved`, `close_requested`, `closed`, `expired`, `profile_retention_eligible`, `profile_deleted`.

## Regression found in original source and correction implemented

The five original browser migration files used malformed timestamp-style IDs with invalid hour components (25, 26, 27, 28 and 30). The original files remain preserved byte-for-byte under `docs/implementation/migration-source-archive/`.

The original CHECK replacements in `16250000`, `16260000`, `16280000` and `16300000` removed values already required by the applied lifecycle contract. The active corrected replacements now preserve all eight applied values and append only the new values required by each feature:

- `20261116162500`: retains the eight applied values and adds the five takeover grant/input events.
- `20261116162600`: retains the applied and takeover values; adds run-terminal revocation behavior without dropping prior values.
- `20261116162700`: adds service-role-only logout revocation; it does not replace the CHECK.
- `20261116162800`: retains all prior values and adds `takeover_command_queued`.
- `20261116163000`: retains all prior values and adds `preview_requested`.

The corrected active SQL has been committed under valid chronological IDs. The five active files remain **unapplied** and absent from Supabase migration history. Therefore their new objects and event values are source-only expectations, not observed production state. Do not infer their execution.

## Evidence and decision

The recovery manifest `browser-migration-recovery-manifest-20261118.csv` records each malformed ID, replacement ID, original Git blob SHA-1, archived path, corrected blob SHA-1 and `NOT_APPLIED` status. The exact correction diff is documented in `browser-migration-exact-correction-diffs-20261118.md`.

Decision: **SOURCE_REGRESSION_CORRECTED / SOURCE_ONLY / NOT_APPLIED**. The currently observed live eight-value CHECK remains unchanged. No database write, migration apply, staging, testing or deployment was performed.
