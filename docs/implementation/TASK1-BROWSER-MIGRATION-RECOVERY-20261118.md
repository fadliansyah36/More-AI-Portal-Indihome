# Task 1 implementation continuation — browser migration recovery

Date: 2026-11-18
Repository: fadliansyah36/More-AI-Portal-Indihome
Branch: main
Supabase project: uunfgimtokhucegqbpce

## Owner direction applied

The product owner approved proceeding with the recovery direction: preserve all previously valid browser lifecycle events, repair the malformed takeover queue lifecycle, keep worker lease expiry outcome-unknown and non-replayable, bind preview artifacts to the owning user/run, and archive duplicate/misnamed source paths rather than applying them.

## Source corrections committed

Five invalid 14-digit migration identifiers had hour components 25, 26, 27, 28 and 30. The migration history was re-read before choosing replacement identifiers. The selected chronological replacements are:
- 20261116250000 → 20261116162500
- 20261116260000 → 20261116162600
- 20261116270000 → 20261116162700
- 20261116280000 → 20261116162800
- 20261116300000 → 20261116163000

All five corrected paths were created successfully on main. Their original source files were copied byte-for-byte into docs/implementation/migration-source-archive/ before the invalid active paths were retired. Original blob SHAs and corrected blob SHAs are recorded in browser-migration-recovery-manifest-20261118.csv.

### Technical corrections
1. Both grant and run-terminal migrations now preserve the existing eight browser lifecycle values, including close_requested, profile_retention_eligible and profile_deleted, before adding takeover events.
2. Logout revocation remains service_role-only. Its trusted FastAPI caller is explicitly required to bind p_user_id to the authenticated principal.
3. The takeover queue migration now has exactly one claim function, one finish function and one grant-revocation trigger definition. It validates worker/limit inputs, expires queued commands whose grant/session is no longer valid, and marks expired processing leases failed with worker_lease_expired_outcome_unknown. It does not replay uncertain browser input.
4. Preview claim checks that session owner, Agent Run owner, and session run_id/last_run_id association agree. Preview finish requires a matching owner/run PNG artifact and an active, unexpired session.
5. All new migration functions use an empty search_path and schema-qualified objects; public execution is revoked and only service_role receives execute.

## Duplicate/misnamed path cleanup

The following current migration aliases were copied into the source archive and removed from the active supabase/migrations path:
- 20261115090000_moreai_agent_model_preferences.sql — duplicate/misnamed alias of the content represented by 20261115100000 / applied history 20261115085314. The original 20261115084819 source remains historically recoverable from commit cc5563e58fe8e3cc5744335ecd68b2f9d9e6ef31.
- 20261111110000_moreai_durable_run_event_outbox.sql — duplicate alias of applied history 20261111091531. Canonical applied history and original blob are preserved.

No historical migration SQL or Supabase migration-history rows were rewritten.

## Safety and verification boundary

- Supabase migration history was read immediately before replacement-ID selection. None of the five replacement IDs appeared in that history; the corrected repository paths were created successfully.
- Supabase live schema was queried read-only for browser sessions/events, Agent Runs and artifacts. The observed columns support the preview session/run/owner/artifact predicates used by the corrected source.
- Original malformed source copies are retained with their original Git blob SHAs.
- No migration was applied. No production data/schema write occurred. No staging, build, lint, typecheck, runtime or test execution was performed, in accordance with the current execution restriction.
- This is source recovery, not migration execution approval and not proof of runtime correctness. Static review remains required before any later apply operation.

## Remaining Task 1 blockers

1. Trusted immutable full expected-schema baseline is still missing. Current catalog is observed state, not expected state.
2. Full object-level expected-vs-observed comparison remains incomplete for RLS policies, grants, ownership, function ACLs, views, triggers and dependencies.
3. Deployment/execution receipts remain incomplete for selected historical migrations.
4. Later evolution from the historical six-argument enqueue function to current seven/eight-argument overloads still needs full lineage mapping.

## Status

Task 1 remains REVIEW_REQUIRED. It is not READY_FOR_REVIEW and not ACCEPTED. Task 2–5, P1 Acceptance, P2 ADR and Phase 04–09 implementation/status advancement were not started in this continuation.
