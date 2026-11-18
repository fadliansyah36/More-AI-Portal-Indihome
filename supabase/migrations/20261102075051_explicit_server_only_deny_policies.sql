
-- Explicitly document server-only tables as deny-all for browser/mobile roles.
-- The FastAPI service uses the server-only Supabase secret and remains subject
-- to application authorization; service_role bypasses RLS by design.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'admin_audit_logs',
    'entitlement_policies',
    'network_providers',
    'network_session_events',
    'network_verification_configs',
    'network_verification_evidence',
    'permissions',
    'provider_partnerships',
    'role_permissions',
    'roles',
    'security_events',
    'user_devices',
    'user_role_assignments'
  ] LOOP
    EXECUTE format(
      'CREATE POLICY %I ON public.%I AS RESTRICTIVE FOR ALL TO anon, authenticated USING (false) WITH CHECK (false)',
      'deny_client_access_' || t,
      t
    );
  END LOOP;
END $$;
