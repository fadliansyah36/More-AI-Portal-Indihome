-- Explicitly deny browser roles access to server-owned security and redemption tables.
-- FastAPI/worker access remains server-only; service_role bypasses RLS.
-- This makes the intended default-deny contract explicit without opening client access.
DO $$
DECLARE
  table_name text;
  policy_name text;
BEGIN
  FOREACH table_name IN ARRAY ARRAY[
    'agent_tool_approvals',
    'network_gateway_nonces',
    'network_verification_method_catalog',
    'partner_access_code_redemptions',
    'partner_access_codes'
  ]
  LOOP
    policy_name := table_name || '_deny_client_roles';
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'public'
        AND tablename = table_name
        AND policyname = policy_name
    ) THEN
      EXECUTE format(
        'CREATE POLICY %I ON public.%I FOR ALL TO anon, authenticated USING (false) WITH CHECK (false)',
        policy_name, table_name
      );
    END IF;
  END LOOP;
END
$$;

COMMENT ON POLICY agent_tool_approvals_deny_client_roles ON public.agent_tool_approvals
  IS 'Server-only approval workflow; clients must use FastAPI.';
COMMENT ON POLICY network_gateway_nonces_deny_client_roles ON public.network_gateway_nonces
  IS 'Server-only gateway nonce state; clients must use FastAPI.';
COMMENT ON POLICY network_verification_method_catalog_deny_client_roles ON public.network_verification_method_catalog
  IS 'Server-owned adapter registry; clients must use FastAPI.';
COMMENT ON POLICY partner_access_code_redemptions_deny_client_roles ON public.partner_access_code_redemptions
  IS 'Server-only redemption settlement; clients must use FastAPI.';
COMMENT ON POLICY partner_access_codes_deny_client_roles ON public.partner_access_codes
  IS 'Server-only access-code issuance and validation; clients must use FastAPI.';
