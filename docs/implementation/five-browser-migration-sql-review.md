# Five browser migration SQL source review

All five files were fetched from GitHub main and reviewed statically, statement by statement at the SQL/object/behavior level. No parser, migration execution, tests or database writes were run.

| ID | SQL objects and behavior | Static findings |
|---|---|---|
| 16250000 | Replaces browser session event CHECK; creates takeover_grants table, owner index, RLS/server grants, consume/revoke SECURITY DEFINER RPCs, session-close trigger | CHECK list drops currently supported `close_requested`, `profile_retention_eligible`, `profile_deleted`. Grants table has separate session_id and user_id FKs but no composite ownership FK. consume RPC checks session/user match and active/unexpired session; token hash is one-time/expiry bounded. |
| 16260000 | Replaces event CHECK; adds Agent Run terminal trigger to revoke unconsumed grants | Depends on grants table from 16250000. CHECK also drops `close_requested` and both profile-retention event types. Trigger scans sessions matching run user and run_id/last_run_id; service-only trigger function. |
| 16270000 | Adds logout revocation SECURITY DEFINER RPC, writes revocation audit event per affected session | Depends on grants table from 16250000. Function accepts p_user_id and is service_role-only; caller must derive user id from authenticated principal server-side, not accept arbitrary client identity. |
| 16280000 | Replaces event CHECK; creates encrypted command queue, indexes, RLS/server-only policy, claim/finish RPCs and grant-revocation trigger | CHECK preserves close_requested but drops both profile-retention event types. SQL is structurally malformed: worker-id IF condition is cut off before body; SELECT fragment appears inside condition; orphaned `or p_limit...` appears after trigger creation; claim function body fragments are split; finish/revoke function and trigger definitions are duplicated. Not safely parseable as supplied. |
| 16300000 | Replaces event CHECK; creates browser_preview_requests table, queue/owner indexes, RLS/server-only policy, claim/finish RPCs | CHECK preserves close_requested but drops both profile-retention event types. Claim joins session and run on same user but does not prove run is the session's run_id/last_run_id. Finish accepts artifact_id if non-null but does not validate artifact ownership/purpose/session association in SQL. |

## Shared observations
- No data backfill or explicit row deletion is present in these sources.
- Tables use `ON DELETE CASCADE` from session/user (and grant for command queue); preview artifact uses `ON DELETE SET NULL`. Cascade behavior is destructive to dependent queue/grant/request rows when parent records are deleted and must be included in retention design.
- Server-only posture is intended through RLS enabled, anon/authenticated revokes, service_role grants, and false policies in 16280000/16300000. The actual security baseline is not fully verifiable without expected grants/policy snapshot.
- Functions are SECURITY DEFINER. 16250000/16260000/16270000 use `search_path = public, pg_temp`; 16280000/16300000 use empty search_path. Prefer an empty fixed search_path and fully qualified object references for SECURITY DEFINER functions.
- No migration modifies Storage policies or buckets directly.
- Current live session event CHECK includes profile-retention event values; source replacements narrow this vocabulary and would reject future retention events.
- These are source findings only, not proof of exploitable runtime vulnerabilities. Backend caller behavior is outside the SQL-only scope.
