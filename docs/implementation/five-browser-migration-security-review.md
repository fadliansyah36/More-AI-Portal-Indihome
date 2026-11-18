# Five browser migration security review

Scope: SQL source only; severity labels describe source risk, not a confirmed production exploit.

| ID | Finding | Classification | Risk |
|---|---|---|---|
| 16250000 | RLS enabled and client roles revoked; service_role-only RPC execution. Session/user relation is checked at grant consumption. Separate FKs do not enforce matching session owner at insert; SECURITY DEFINER search_path includes public, pg_temp. | Potential integrity/hardening risk | MEDIUM |
| 16260000 | Trigger function revoked from client roles; it acts on grants for sessions owned by the Agent Run user. Requires service-side trigger operation. Depends on missing grants table. | No direct client execution path observed; dependency blocker | MEDIUM |
| 16270000 | SECURITY DEFINER RPC accepts arbitrary p_user_id but execute is revoked from public/anon/authenticated and granted only to service_role. Server must bind p_user_id to authenticated principal; no SQL-level auth.uid guard. | Potential confused-deputy risk if server passes client-controlled ID | HIGH |
| 16280000 | Server-only RLS and service_role function grants intended. Malformed source prevents trustworthy security review. Separate session/user/grant FKs need consistency enforcement; encrypted_command secrecy depends on server encryption/key lifecycle. | Unresolved due malformed source | HIGH |
| 16300000 | Server-only RLS and service_role-only claim/finish functions. Claim validates session and run share user but not session-run linkage; finish does not check artifact ownership or artifact/session relationship. | Potential object-association/authorization gap; backend must validate | HIGH |

## Cross-cutting controls and gaps
- Current live CHECK permits `profile_retention_eligible` and `profile_deleted`; four source files would remove these values. This can break retention/cleanup audit behavior. 16250000/16260000 also remove `close_requested`.
- RLS on new tables is enabled and client privileges are revoked in the source. A false deny policy is explicitly created for commands and preview requests; grants table has no explicit policy but has RLS enabled and no client table grants.
- Service_role bypasses RLS; all business validation therefore depends on trusted FastAPI/worker boundaries and parameter derivation.
- `ON DELETE CASCADE` can erase dependent consent/command/preview audit rows when sessions/users/grants are deleted. Retention policy must decide whether this is acceptable for audit requirements.
- SECURITY DEFINER functions with `search_path = public, pg_temp` should be hardened to an empty fixed search path and use schema-qualified references.
- No Storage policy or bucket mutation is in these five SQL files.
- Confirmed issue: malformed SQL in 16280000. Potential risks above require backend contract/owner review; do not label them confirmed exploitable vulnerabilities.
