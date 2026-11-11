-- Permission-checked, idempotent partner governance mutation with audit in the same transaction.
create table if not exists public.admin_mutation_requests (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid not null references auth.users(id) on delete restrict,
  idempotency_key text not null check (char_length(idempotency_key) between 12 and 128),
  action text not null,
  payload jsonb not null,
  response jsonb,
  created_at timestamptz not null default now(),
  unique(actor_user_id, idempotency_key)
);
alter table public.admin_mutation_requests enable row level security;
drop policy if exists admin_mutation_requests_server_only on public.admin_mutation_requests;
create policy admin_mutation_requests_server_only on public.admin_mutation_requests
  for all to anon, authenticated using (false) with check (false);
revoke all on public.admin_mutation_requests from anon, authenticated;
grant all on public.admin_mutation_requests to service_role;

create or replace function public.moreai_admin_update_partner_status(
  p_actor_user_id uuid,
  p_partner_id uuid,
  p_status text,
  p_idempotency_key text,
  p_correlation_id text default null
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_payload jsonb;
  v_request public.admin_mutation_requests;
  v_old_status text;
  v_partner public.partner_organizations;
  v_result jsonb;
begin
  if p_actor_user_id is null or p_partner_id is null
     or p_status not in ('pending','active','suspended','rejected','closed')
     or p_idempotency_key is null or char_length(p_idempotency_key) not between 12 and 128 then
    raise exception 'invalid_partner_status_mutation' using errcode='22023';
  end if;

  if not exists (
    select 1
    from public.user_role_assignments ura
    join public.roles r on r.id=ura.role_id and r.scope='platform'
    join public.role_permissions rp on rp.role_id=r.id
    join public.permissions p on p.id=rp.permission_id and p.key='partner.organization.manage'
    where ura.user_id=p_actor_user_id
      and ura.scope_type='platform'
      and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at > now())
  ) then
    raise exception 'missing_permission_partner_organization_manage' using errcode='42501';
  end if;

  v_payload := jsonb_build_object('partner_id',p_partner_id,'status',p_status);
  insert into public.admin_mutation_requests(actor_user_id,idempotency_key,action,payload)
  values(p_actor_user_id,p_idempotency_key,'partner.organization.status.update',v_payload)
  on conflict(actor_user_id,idempotency_key) do nothing;

  select * into v_request
  from public.admin_mutation_requests
  where actor_user_id=p_actor_user_id and idempotency_key=p_idempotency_key
  for update;

  if v_request.action <> 'partner.organization.status.update' or v_request.payload <> v_payload then
    raise exception 'idempotency_key_reused_with_different_payload' using errcode='22023';
  end if;
  if v_request.response is not null then
    return v_request.response;
  end if;

  select * into v_partner from public.partner_organizations where id=p_partner_id for update;
  if not found then
    raise exception 'partner_not_found' using errcode='P0002';
  end if;
  v_old_status := v_partner.status;

  update public.partner_organizations
  set status=p_status, updated_at=now()
  where id=p_partner_id
  returning * into v_partner;

  insert into public.admin_audit_logs(
    actor_user_id,action,resource_type,resource_id,scope_type,scope_id,
    correlation_id,outcome,metadata
  ) values (
    p_actor_user_id,'partner.organization.status.update','partner_organization',p_partner_id::text,
    'platform',null,left(p_correlation_id,128),'success',
    jsonb_build_object('previous_status',v_old_status,'new_status',p_status,'idempotency_key',p_idempotency_key)
  );

  v_result := jsonb_build_object(
    'partner_id',v_partner.id,'status',v_partner.status,
    'previous_status',v_old_status,'updated_at',v_partner.updated_at
  );
  update public.admin_mutation_requests set response=v_result
  where id=v_request.id;
  return v_result;
end;
$$;

revoke all on function public.moreai_admin_update_partner_status(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.moreai_admin_update_partner_status(uuid,uuid,text,text,text) to service_role;
