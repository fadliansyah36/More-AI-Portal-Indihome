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
