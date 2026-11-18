create or replace function public.moreai_submit_partner_application(
  p_user_id uuid,
  p_legal_name text,
  p_display_name text,
  p_correlation_id text default null
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_partner public.partner_organizations%rowtype;
  v_member public.partner_members%rowtype;
  v_count integer;
  v_correlation text := coalesce(nullif(p_correlation_id, ''), gen_random_uuid()::text);
begin
  if p_user_id is null
    or length(trim(coalesce(p_legal_name, ''))) < 2
    or length(trim(coalesce(p_legal_name, ''))) > 160
    or length(trim(coalesce(p_display_name, ''))) < 2
    or length(trim(coalesce(p_display_name, ''))) > 120 then
    raise exception using errcode = '22023', message = 'PARTNER_APPLICATION_INVALID';
  end if;

  select count(*) into v_count from public.partner_members where user_id = p_user_id;
  if v_count > 1 then
    raise exception using errcode = '23505', message = 'PARTNER_CONTEXT_AMBIGUOUS';
  elsif v_count = 1 then
    select po.* into v_partner
    from public.partner_members pm
    join public.partner_organizations po on po.id = pm.partner_id
    where pm.user_id = p_user_id
    limit 1;
    select pm.* into v_member
    from public.partner_members pm
    where pm.user_id = p_user_id
    limit 1;
    return jsonb_build_object(
      'partner', to_jsonb(v_partner),
      'membership', to_jsonb(v_member),
      'replayed', true
    );
  end if;

  insert into public.partner_organizations(
    legal_name, display_name, status, created_by
  ) values (
    trim(p_legal_name), trim(p_display_name), 'pending', p_user_id
  ) returning * into v_partner;

  insert into public.partner_members(
    partner_id, user_id, role_key, location_id, status
  ) values (
    v_partner.id, p_user_id, 'partner_owner', null, 'active'
  ) returning * into v_member;

  insert into public.admin_audit_logs(
    actor_user_id, action, resource_type, resource_id, scope_type, scope_id,
    correlation_id, outcome, metadata
  ) values (
    p_user_id, 'partner.application.submitted', 'partner_organization',
    v_partner.id::text, 'partner', v_partner.id, v_correlation, 'success',
    jsonb_build_object('legal_name', v_partner.legal_name, 'display_name', v_partner.display_name)
  );

  return jsonb_build_object(
    'partner', to_jsonb(v_partner),
    'membership', to_jsonb(v_member),
    'replayed', false
  );
end;
$$;

create or replace function public.moreai_admin_review_partner(
  p_actor_user_id uuid,
  p_partner_id uuid,
  p_decision text,
  p_reason text default null,
  p_correlation_id text default null
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_partner public.partner_organizations%rowtype;
  v_next_status text;
  v_correlation text := coalesce(nullif(p_correlation_id, ''), gen_random_uuid()::text);
begin
  if p_actor_user_id is null or p_partner_id is null
    or p_decision is null or p_decision not in ('approve', 'reject', 'suspend')
    or length(coalesce(p_reason, '')) > 500 then
    raise exception using errcode = '22023', message = 'PARTNER_REVIEW_INVALID';
  end if;

  if not exists (
    select 1
    from public.user_role_assignments ura
    join public.roles r on r.id = ura.role_id
    join public.role_permissions rp on rp.role_id = r.id
    join public.permissions p on p.id = rp.permission_id
    where ura.user_id = p_actor_user_id
      and ura.scope_type = 'platform'
      and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at > now())
      and r.scope = 'platform'
      and p.key = 'partner.organization.manage'
  ) then
    raise exception using errcode = '42501', message = 'ADMIN_PERMISSION_DENIED';
  end if;

  select * into v_partner
  from public.partner_organizations
  where id = p_partner_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'PARTNER_NOT_FOUND';
  end if;

  v_next_status := case p_decision
    when 'approve' then 'active'
    when 'reject' then 'rejected'
    when 'suspend' then 'suspended'
  end;

  if v_partner.status = v_next_status then
    return jsonb_build_object('partner', to_jsonb(v_partner), 'replayed', true);
  end if;

  if (p_decision in ('approve', 'reject') and v_partner.status <> 'pending')
    or (p_decision = 'suspend' and v_partner.status <> 'active') then
    raise exception using errcode = '55000', message = 'PARTNER_STATUS_TRANSITION_INVALID';
  end if;

  update public.partner_organizations
  set status = v_next_status, updated_at = now()
  where id = p_partner_id
  returning * into v_partner;

  update public.partner_members
  set status = case when p_decision = 'approve' then 'active' else 'suspended' end
  where partner_id = p_partner_id;

  insert into public.admin_audit_logs(
    actor_user_id, action, resource_type, resource_id, scope_type, scope_id,
    correlation_id, outcome, metadata
  ) values (
    p_actor_user_id, 'partner.application.' || p_decision, 'partner_organization',
    p_partner_id::text, 'partner', p_partner_id, v_correlation, 'success',
    jsonb_build_object('previous_status', case when p_decision in ('approve','reject') then 'pending' else 'active' end,
      'new_status', v_next_status, 'reason', p_reason)
  );

  return jsonb_build_object('partner', to_jsonb(v_partner), 'replayed', false);
end;
$$;

revoke all on function public.moreai_submit_partner_application(uuid, text, text, text) from public, anon, authenticated;
grant execute on function public.moreai_submit_partner_application(uuid, text, text, text) to service_role;
revoke all on function public.moreai_admin_review_partner(uuid, uuid, text, text, text) from public, anon, authenticated;
grant execute on function public.moreai_admin_review_partner(uuid, uuid, text, text, text) to service_role;