# Expected schema dependency map (analytical)

This map is limited to dependencies proven by the five browser SQL sources and Task 1 catalog existence checks. It is not a complete database dependency graph.

```text
Applied/observed base:
  public.moreai_browser_sessions
  public.moreai_browser_session_events
  public.agent_runs
  public.artifacts
       |
       +-- 20261116250000 takeover_grants table + grant RPCs + session-close trigger
              |
              +-- 20261116260000 run-terminal grant revocation trigger
              +-- 20261116270000 logout grant revocation RPC
              +-- 20261116280000 takeover command queue (source malformed)
       |
       +-- 20261116300000 preview request table + claim/finish RPCs
             (base dependencies exist; no direct dependency on grants/command queue)
```

Observed catalog confirms base tables exist and grants/commands/preview tables and related functions are absent. Migration history contains no row for any of these five versions.

Other relevant dependency: 15084819 references `moreai_customer_agent_configs`, `llm_models`, `conversations`, `conversation_messages`, `agent_runs`, and `llm_providers`. Its historical SQL is lexically matched to Git source commit cc5563e; full schema replay is not performed.

No database changes or migration operations were performed.
