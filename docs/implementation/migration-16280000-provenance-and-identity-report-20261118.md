# Migration 20261116280000 — provenance and identity report (superseded source)

**Status: SUPERSEDED BY CORRECTED ACTIVE SOURCE.** This report documents the malformed original identity and its defects; it is not the implementation instruction for the current migration directory.

Original path: `docs/implementation/migration-source-archive/20261116280000_moreai_browser_takeover_command_queue.sql.original.sql`  
Original blob SHA-1: `dac0d2796ebef75570a7ca79ed10a13025579615`  
Original size: 11,052 bytes.  
Supabase history: no row for malformed ID `20261116280000`.

The identifier parses as 2026-11-16 28:00:00 and is invalid as a `YYYYMMDDHHMMSS` timestamp-style migration ID. The original source is retained in the archive; it is not an active migration.

## Original SQL defects (historical evidence)

- Claim-function body contained incomplete fragments.
- An orphaned `or p_limit < 1 or p_limit > 25 then` fragment followed a trigger definition.
- Claim, finish and revoke-trigger implementations were duplicated or fragmented.
- The original event CHECK replacement removed previously supported profile-retention values.

## Implemented correction

The corrected active source is:

- Path: `supabase/migrations/20261116162800_moreai_browser_takeover_command_queue.sql`
- Replacement ID: `20261116162800`
- Corrected Git blob SHA-1: `eaa688946b91215fec04d8382e2eff3eb3ada3b8`
- Recovery manifest: `browser-migration-recovery-manifest-20261118.csv`

The active file contains one complete claim function, one finish function and the associated trigger/revoke behavior; it preserves the existing eight browser event values and appends `takeover_command_queued`. Expired processing leases are terminalized as outcome-unknown and are not replayed. The original bytes remain archived.

## Execution status

The corrected active source has no Supabase migration-history row and is **NOT_APPLIED**. No production DDL or database write was executed. Source correction does not prove database effect or runtime behavior. This file is retained as historical provenance, not as a pending owner decision.
