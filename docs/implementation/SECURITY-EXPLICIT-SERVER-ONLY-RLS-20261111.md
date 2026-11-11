# Security Remediation — Explicit Server-only RLS Policies
Date: 2026-11-11
Repository: `fadliansyah36/More-AI-Portal-Indihome`
Branch: `main`
Supabase project: `uunfgimtokhucegqbpce`

## Scope
Address the five Security Advisor findings for RLS-enabled tables without policies, while preserving the mandatory browser-to-FastAPI boundary in `AGENTS.md`.

## Decision
The five tables are server-owned workflow/security state and must not be accessed directly by browser roles:
- `agent_tool_approvals`
- `network_gateway_nonces`
- `network_verification_method_catalog`
- `partner_access_code_redemptions`
- `partner_access_codes`

Added explicit `FOR ALL TO anon, authenticated USING (false) WITH CHECK (false)` policies. This is fail-closed for browser roles and does not grant any client access. Trusted FastAPI/worker service-role access remains server-only and continues to bypass RLS as designed.

## Production migration
- Migration: `moreai_explicit_server_only_rls_denials`
- Applied to canonical Supabase project `uunfgimtokhucegqbpce`.
- Post-apply read-only inspection confirmed all five policies exist with roles `{anon,authenticated}`, command `ALL`, `qual=false`, and `with_check=false`.
- No rows were inserted, updated or deleted.

## Security Advisor after migration
The five `rls_enabled_no_policy` findings are no longer present in the latest Security Advisor response.
One finding remains: `auth_leaked_password_protection` (WARN). It requires changing Supabase Auth project configuration; this migration does not alter Auth settings.

## Verification limits
- Migration application: successful.
- Policy catalog verification: successful for all five tables.
- Security Advisor: five policy findings cleared; leaked-password protection remains.
- No authenticated application E2E, service-role API test, worker test or production deployment was run as part of this remediation.

## Next action
Enable leaked-password protection in Supabase Auth dashboard/project configuration, then verify Security Advisor again. Continue Phase 07A runtime acceptance in isolated staging. Do not mark Phase 07A runtime or Phase 11 complete based on this policy migration.
