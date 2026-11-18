# Migration 20261116280000 — provenance and identity report

Path: supabase/migrations/20261116280000_moreai_browser_takeover_command_queue.sql
Current main blob: dac0d2796ebef75570a7ca79ed10a13025579615
Size: 11,052 bytes.
History relationship: no row for 20261116280000 in Supabase migration history.
GitHub search for the ID and command-queue phrase returned no creation commit or owner decision in the linked repository search. This is a search limitation, not proof that no commit exists.

## Identifier

The 14-digit identifier parses as 2026-11-16 28:00:00. Hour 28 is invalid under the YYYYMMDDHHMMSS timestamp convention. It is therefore a malformed timestamp-style migration ID unless an owner-approved alternate numbering convention exists. The same pattern occurs in the other four browser source IDs (25, 26, 27, 30 hours). No replacement ID is inferred or assigned.

## SQL source defects

- The first claim-function body begins an incomplete worker ID regex and runs directly into a SELECT fragment.
- The or p_limit < 1 or p_limit > 25 then clause appears orphaned after the trigger definition.
- The claim function body appears in fragments and the function is defined again later.
- Finish and revoke-trigger function/trigger definitions are duplicated.
- The event CHECK preserves close_requested but drops profile_retention_eligible and profile_deleted.

## Decision

Status: OWNER_DECISION_REQUIRED / SOURCE_REVIEW_COMPLETE / BLOCKED. Do not apply, rename or rewrite. Require owner-confirmed intended migration ID, source of origin/commit, corrected complete SQL file, exact before/after diff and renewed static review.
