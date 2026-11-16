-- Fence an unexpired browser capacity lease to one worker replica.
-- A different replica must wait for expiry instead of stealing an active profile.

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
    if v_lease.worker_id<>p_worker_id then
      return jsonb_build_object(
        'acquired',false,
        'reason','session_lease_owned_by_other_worker',
        'expires_at',v_lease.expires_at
      );
    end if;
    update public.moreai_browser_capacity_leases
    set expires_at=now()+(p_lease_seconds * interval '1 second'), updated_at=now()
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
