create or replace function public.moreai_submit_partner_application(
  p_user_id uuid,
  p_legal_name text,
  p_display_name text,
  p_correlation_id text default null
) returns jsonb
language plpgsql security definer set search_path = public, pg_temp
as $$
declare
  v_partner public.partner_organizations%rowtype;
  v_member public.partner_members%rowtype;
  v_count integer;
  v_correlation text := coalesce(nullif(p_correlation_id, ''), gen_random_uuid()::text);
begin
  if p_user_id is null or length(trim(coalesce(p_legal_name, ''))) < 2
    or length(trim(coalesce(p_legal_name, ''))) > 160
    or length(trim(coalesce(p_display_name, ''))) < 2
    or length(trim(coalesce(p_display_name, ''))) > 120 then
    raise exception using errcode = '22023', message = 'PARTNER_APPLICATION_INVALID';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(p_user_id::text, 0));
  select count(*) into v_count from public.partner_members where user_id = p_user_id;
  if v_count > 1 then
    raise exception using errcode = '23505', message = 'PARTNER_CONTEXT_AMBIGUOUS';
  elsif v_count = 1 then
    select po.* into v_partner from public.partner_members pm
      join public.partner_organizations po on po.id = pm.partner_id
      where pm.user_id = p_user_id limit 1;
    select pm.* into v_member from public.partner_members pm where pm.user_id = p_user_id limit 1;
    return jsonb_build_object('partner', to_jsonb(v_partner), 'membership', to_jsonb(v_member), 'replayed', true);
  end if;

  insert into public.partner_organizations(legal_name, display_name, status, created_by)
  values(trim(p_legal_name), trim(p_display_name), 'pending', p_user_id) returning * into v_partner;
  insert into public.partner_members(partner_id, user_id, role_key, location_id, status)
  values(v_partner.id, p_user_id, 'partner_owner', null, 'active') returning * into v_member;
  insert into public.admin_audit_logs(actor_user_id, action, resource_type, resource_id, scope_type, scope_id, correlation_id, outcome, metadata)
  values(p_user_id, 'partner.application.submitted', 'partner_organization', v_partner.id::text, 'partner', v_partner.id, v_correlation, 'success',
    jsonb_build_object('legal_name', v_partner.legal_name, 'display_name', v_partner.display_name));
  return jsonb_build_object('partner', to_jsonb(v_partner), 'membership', to_jsonb(v_member), 'replayed', false);
end;
$$;