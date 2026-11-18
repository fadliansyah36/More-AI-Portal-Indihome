# Task 1 — Schema Object & Migration Dependency Report
Date: 2026-11-18
Scope: static source dependency analysis plus read-only live object existence checks.

## Applied base objects used by the browser migration set
Live catalog confirms:
- `public.moreai_browser_sessions` exists.
- `public.moreai_browser_session_events` exists.
- `public.agent_runs` exists.
- `public.artifacts` exists.
- `public.agent_run_event_counters` exists.
- `public.moreai_browser_takeover_grants` is absent.
- `public.moreai_browser_takeover_commands` is absent.
- `public.moreai_browser_preview_requests` is absent.
- Functions for grant consumption/revocation, takeover queue claim/finish, and preview claim/finish are absent.

## Dependency graph

```text
Applied browser session base (sessions + session_events)
        |
        +--> 20261116250000 grants table + grant RPCs + session-close revocation trigger
                 |
                 +--> 20261116260000 Agent Run terminal revocation trigger
                 |
                 +--> 20261116270000 logout revocation RPC
                 |
                 +--> 20261116280000 command queue table + worker claim/finish + grant-revocation trigger
                          [source malformed; do not apply]

Applied base sessions + session_events + agent_runs + artifacts
        |
        +--> 20261116300000 browser preview request table + worker claim/finish RPCs
             (no direct grants/command table dependency; its CHECK definition still regresses profile event types)
```

## Event constraint compatibility
Current live `moreai_browser_session_events_event_type_check` allows:
`created`, `restored`, `state_saved`, `close_requested`, `closed`, `expired`, `profile_retention_eligible`, `profile_deleted`.

Unapplied source behavior:
- 16250000 and 16260000 omit `close_requested`, `profile_retention_eligible`, `profile_deleted`.
- 16280000 and 16300000 include `close_requested` but omit `profile_retention_eligible` and `profile_deleted`.
- 16270000 does not replace this CHECK constraint.

Current row count in `moreai_browser_session_events` is zero. The regression still matters because future profile-retention and/or close-request events would be rejected after constraint replacement.

## Additional migration source issue
`20261116280000_moreai_browser_takeover_command_queue.sql` has an incomplete worker-id regex/IF condition, SQL fragments in the function body, an orphaned `or p_limit < 1 ...` fragment and duplicate function/trigger definitions. This is a static source blocker independent of missing prerequisites.

## Decision
- 16250000: UNRESOLVED — constraint regression and no approval.
- 16260000: BLOCKED_BY_DEPENDENCY — requires 16250000; same constraint regression.
- 16270000: BLOCKED_BY_DEPENDENCY — requires grants table from 16250000.
- 16280000: BLOCKED_BY_DEPENDENCY — requires 16250000 and malformed SQL.
- 16300000: UNRESOLVED — base objects exist, but CHECK regression and no approval.

No migrations were applied and no database objects were modified.

## Execution continuation addendum — 2026-11-18

The dependency map has been updated in `TASK1-DEPENDENCY-MAPPING-20261118.csv`. Current active browser migration IDs are `20261116162500`, `20261116162600`, `20261116162700`, `20261116162800`, and `20261116163000`. Original malformed files and two current alias paths are archived and not active. Corrected source dependencies are: grants table/RPCs → run-terminal revocation, logout revocation and command queue; preview requests depend on existing sessions, auth users, agent runs and artifacts. The full object names/signatures and Skill Registry → Agent Studio → FastAPI enqueue → OpenManus resolver path are in the dependency CSV.

All five migrations remain unapplied. The current live catalog correctly lacks their new tables/functions; this is an expected difference, not live drift. The corrected command queue has one claim function, one finish function and one grant-revocation trigger. No migration apply or production DB write was performed. SQL runtime validity is not claimed because tests/replay were prohibited.
