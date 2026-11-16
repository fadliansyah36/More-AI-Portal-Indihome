-- Shared tenant/global admission leases for the OpenFuse persistent browser runtime.
-- A single transaction-scoped advisory lock serializes admission across API/worker replicas.

create table if not exists public.moreai_browser_capacity_leases (
  session_id uuid primary key references public.moreai_browser_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  worker_id text not null,
  lease_token uuid not null default gen_random_uuid(),
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint moreai_browser_capacity_worker_id_check
    check (worker_id ~ '^[A-Za-z0-9._:-]{1,128}$')
);

create index if not exists moreai_browser_capacity_leases_active_idx
  on public.moreai_browser_capacity_leases(expires_at, user_id, session_id);

alter table public.moreai_browser_capacity_leases enable row level security;
revoke all on table public.moreai_browser_capacity_leases from anon, authenticated;
grant all on table public.moreai_browser_capacity_leases to service_role;

drop policy if exists moreai_deny_client_browser_capacity_leases
  on public.moreai_browser_capacity_leases;
create policy moreai_deny_client_browser_capacity_leases
  on public.moreai_browser_capacity_leases
  for all to anon, authenticated
  using (false) with check (false);

comment on table public.moreai_browser_capacity_leases is
  'Short-lived shared admission leases for OpenFuse browser sessions; accessed only by trusted FastAPI service role.';

create or replace function public.moreai_acquire_browser_capacity_lease(
  p_session_id uuid,
  p_user_id uuid,
  p_worker_id text,
  p_lease_seconds integer default 300
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_session public.moreai_browser_sessions%rowtype;
  v_lease public.moreai_browser_capacity_leases%rowtype;
  v_global_count integer;
  v_user_count integer;
  v_token uuid;
  v_expiry timestamptz;
begin
  if p_session_id is null or p_user_id is null
     or p_worker_id is null or p_worker_id !~ '^[A-Za-z0-9._:-]{1,128}$'
     or p_lease_seconds is null or p_lease_seconds not between 60 and 900 then
    raise exception 'browser_capacity_lease_arguments_invalid' using errcode='22023';
  end if;

  perform pg_advisory_xact_lock(hashtextextended('moreai_browser_capacity_global', 0));

  select * into v_session
  from public.moreai_browser_sessions
  where id=p_session_id and user_id=p_user_id and status='active'
  for update;

  if not found then
    return jsonb_build_object('acquired',false,'reason','session_not_active');
  end if;

  select * into v_lease
  from public.moreai_browser_capacity_leases
  where session_id=p_session_id
  for update;

  if found and v_lease.user_id=p_user_id and v_lease.expires_at>now() then
    update public.moreai_browser_capacity_leases
    set worker_id=p_worker_id, expires_at=now()+(p_lease_seconds * interval '1 second'), updated_at=now()
    where session_id=p_session_id
    returning lease_token, expires_at into v_token, v_expiry;
    return jsonb_build_object('acquired',true,'lease_token',v_token,'expires_at',v_expiry,'reused',true);
  end if;

  delete from public.moreai_browser_capacity_leases
  where expires_at<=now();

  select count(*)::integer into v_global_count
  from public.moreai_browser_capacity_leases
  where expires_at>now();

  select count(*)::integer into v_user_count
  from public.moreai_browser_capacity_leases
  where user_id=p_user_id and expires_at>now();

  if v_global_count>=24 then
    return jsonb_build_object('acquired',false,'reason','global_capacity_limit','limit',24);
  end if;
  if v_user_count>=2 then
    return jsonb_build_object('acquired',false,'reason','tenant_capacity_limit','limit',2);
  end if;

  insert into public.moreai_browser_capacity_leases(
    session_id,user_id,worker_id,lease_token,expires_at
  ) values (
    p_session_id,p_user_id,p_worker_id,gen_random_uuid(),now()+(p_lease_seconds * interval '1 second')
  )
  on conflict(session_id) do update set
    user_id=excluded.user_id,
    worker_id=excluded.worker_id,
    lease_token=excluded.lease_token,
    expires_at=excluded.expires_at,
    updated_at=now()
  returning lease_token,expires_at into v_token,v_expiry;

  return jsonb_build_object('acquired',true,'lease_token',v_token,'expires_at',v_expiry,'reused',false);
end;
$function$;

revoke all on function public.moreai_acquire_browser_capacity_lease(uuid,uuid,text,integer)
  from public,anon,authenticated;
grant execute on function public.moreai_acquire_browser_capacity_lease(uuid,uuid,text,integer)
  to service_role;

-- Release capacity in the same transaction that marks a browser session closed.
create or replace function public.moreai_complete_browser_session_close(
  p_session_id uuid, p_user_id uuid
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare v_row public.moreai_browser_sessions%rowtype;
begin
  if p_session_id is null or p_user_id is null then
    raise exception 'browser_session_close_identity_invalid' using errcode='22023';
  end if;
  select * into v_row from public.moreai_browser_sessions
  where id=p_session_id and user_id=p_user_id for update;
  if not found then
    raise exception 'browser_session_close_request_not_found' using errcode='P0002';
  end if;
  if v_row.status='closed' then
    delete from public.moreai_browser_capacity_leases where session_id=p_session_id and user_id=p_user_id;
    return jsonb_build_object('session_id',p_session_id,'status','closed','replayed',true);
  end if;
  if v_row.status<>'close_requested' then
    raise exception 'browser_session_close_request_not_found' using errcode='P0002';
  end if;
  update public.moreai_browser_sessions
  set status='closed',encrypted_state=null,closed_at=now(),
      profile_retention_after=now()+interval '30 days'
  where id=p_session_id and user_id=p_user_id;
  delete from public.moreai_browser_capacity_leases where session_id=p_session_id and user_id=p_user_id;
  insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
  values(p_session_id,p_user_id,'closed',jsonb_build_object('source','worker_reconciler'));
  return jsonb_build_object('session_id',p_session_id,'status','closed');
end;
$function$;
revoke all on function public.moreai_complete_browser_session_close(uuid,uuid) from public,anon,authenticated;
grant execute on function public.moreai_complete_browser_session_close(uuid,uuid) to service_role;

create or replace function public.moreai_mark_browser_session_closed(
  p_session_id uuid,
  p_user_id uuid,
  p_run_id uuid
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare v_row public.moreai_browser_sessions%rowtype;
begin
  if p_session_id is null or p_user_id is null or p_run_id is null then
    raise exception 'browser_session_close_identity_invalid' using errcode='22023';
  end if;
  select * into v_row from public.moreai_browser_sessions
  where id=p_session_id and user_id=p_user_id for update;
  if not found then
    raise exception 'browser_session_not_found' using errcode='P0002';
  end if;
  if v_row.status='closed' then
    delete from public.moreai_browser_capacity_leases where session_id=p_session_id and user_id=p_user_id;
    return jsonb_build_object('session_id',p_session_id,'status','closed','replayed',true);
  end if;
  if v_row.status not in ('active','close_requested') then
    raise exception 'browser_session_not_active' using errcode='P0002';
  end if;
  update public.moreai_browser_sessions
  set status='closed',encrypted_state=null,closed_at=now(),
      profile_retention_after=now()+interval '30 days'
  where id=p_session_id and user_id=p_user_id;
  delete from public.moreai_browser_capacity_leases where session_id=p_session_id and user_id=p_user_id;
  insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
  values(p_session_id,p_user_id,'closed',
    jsonb_build_object('source','worker','run_id',p_run_id));
  return jsonb_build_object('session_id',p_session_id,'status','closed');
end;
$function$;
revoke all on function public.moreai_mark_browser_session_closed(uuid,uuid,uuid)
  from public,anon,authenticated;
grant execute on function public.moreai_mark_browser_session_closed(uuid,uuid,uuid)
  to service_role;
