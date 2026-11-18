# Task 1 — RLS & Permission Drift Report
Date: 2026-11-18
Scope: read-only catalog introspection of public schema.

## Observed facts
- 94 public base tables; RLS enabled on all 94.
- FORCE ROW LEVEL SECURITY is false on all 94.
- 95 public policies:
  - 44 permissive server-deny policies (USING false, WITH CHECK false, anon/authenticated).
  - 37 restrictive server-deny policies (USING false, WITH CHECK false, anon/authenticated).
  - 14 owner/member-scoped policies (user_id/auth.uid(), workspace membership, partner membership, or equivalent).
- 56 SECURITY DEFINER public functions.
  - 0 executable by anon.
  - 0 executable by authenticated.
  - 56 executable by service_role.
- `information_schema.role_table_grants` showed 665 public table grant rows for postgres and 653 for service_role; no anon/authenticated table grants were returned.
- Function inventory and policy definitions were captured by catalog queries; no source-side expected grant/policy baseline was available for a full equality check.

## Drift classification
- RLS enabled status: NO_DRIFT_EVIDENCE within observed public tables (94/94 enabled).
- Client table grants: NO_DRIFT_EVIDENCE in the information_schema inventory (none for anon/authenticated).
- SECURITY DEFINER client execution: NO_DRIFT_EVIDENCE for the observed 56 functions (none for anon/authenticated).
- Exact expected policy expressions, ownership, grant options, FORCE RLS expectations and function security settings vs migration source: NOT_VERIFIABLE without an authoritative schema baseline.
- No claim is made that all policy/function definitions are drift-free.

## Decision
DOCUMENT_ONLY for observed catalog baseline. Full RLS/permission parity remains NOT_VERIFIABLE and requires a trusted expected-state source. No GRANT/REVOKE, RLS policy, ownership or function change was executed.
