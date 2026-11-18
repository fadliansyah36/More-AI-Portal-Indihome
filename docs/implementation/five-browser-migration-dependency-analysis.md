# Five browser migration dependency analysis

## Dependency graph

```text
Applied base: moreai_browser_sessions + moreai_browser_session_events
  |                    + agent_runs + artifacts
  |
  +-- 16250000 takeover_grants table / RPCs / session-close trigger
         +-- 16260000 run-terminal grant revocation (requires grants table)
         +-- 16270000 logout grant revocation (requires grants table)
         +-- 16280000 command queue (requires grants table; malformed SQL)
  |
  +-- 16300000 preview requests (base objects exist; no direct grants/queue dependency)
```

## Per-source dependencies and compatibility
- **16250000:** base session/event tables exist; grants table absent. Its event CHECK replacement conflicts with current live CHECK values. No applied predecessor dependency is missing other than the base objects, but owner intent is absent.
- **16260000:** depends on 16250000 table/functions. Dependency absent. Same event CHECK regression.
- **16270000:** depends on grants table from 16250000. Dependency absent. No CHECK replacement of its own.
- **16280000:** depends on grants table from 16250000. Dependency absent. SQL malformed independently of dependency. Event CHECK loses profile events.
- **16300000:** base sessions/events/agent_runs/artifacts exist. No direct FK to grants/commands. Event CHECK loses profile events. Session/run relationship is only same-user join, not explicit run-to-session relation.

## Existing catalog facts
Live catalog confirms `moreai_browser_sessions`, `moreai_browser_session_events`, `agent_runs`, `artifacts`, and `agent_run_event_counters` exist. Takeover grants, takeover commands, preview requests and their relevant RPCs are absent. All five versions are absent from migration history.

## Ordering and reversibility
16250000 must precede 16260000, 16270000 and 16280000. 16300000 can be ordered after the applied base objects independently. All five replace the event CHECK and can narrow accepted event vocabulary. Cascade FKs can delete grant/command/preview rows with parent deletion. No rollback/compensating SQL is supplied in these source files.

No migration was applied. This graph is not a complete schema dependency graph.
