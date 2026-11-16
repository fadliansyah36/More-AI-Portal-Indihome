-- Make profile-retention claims retryable after worker/network failures.
-- A five-minute claim lease prevents hot-loop duplicate work while allowing recovery.
alter table public.moreai_browser_sessions
  add column if not exists profile_retention_claimed_at timestamptz;

create index if not exists moreai_browser_sessions_profile_retention_claim_idx
  on public.moreai_browser_sessions(profile_retention_claimed_at, profile_retention_after, id)
  where profile_deleted_at is null and status in ('closed','expired');

create or replace function public.moreai_claim_browser_profile_retention(p_limit integer default 100)
returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_items jsonb;
begin
  if p_limit is null or p_limit < 1 or p_limit > 100 then
    raise exception 'browser_profile_retention_limit_invalid' using errcode='22023';
  end if;

  with candidates as (
    select id, user_id, profile_retention_after, profile_retention_notified_at
    from public.moreai_browser_sessions
    where status in ('closed','expired')
      and profile_retention_after <= now()
      and profile_deleted_at is null
      and (
        profile_retention_claimed_at is null
        or profile_retention_claimed_at <= now() - interval '5 minutes'
      )
    order by profile_retention_after asc, id asc
    for update skip locked
    limit p_limit
  ), updated as (
    update public.moreai_browser_sessions as sessions
    set
      profile_retention_claimed_at=now(),
      profile_retention_notified_at=coalesce(sessions.profile_retention_notified_at, now())
    from candidates
    where sessions.id=candidates.id
    returning sessions.id, sessions.user_id, sessions.profile_retention_after
  ), events as (
    insert into public.moreai_browser_session_events(
      session_id,user_id,event_type,metadata
    )
    select updated.id,updated.user_id,'profile_retention_eligible',
      jsonb_build_object('retention_after',updated.profile_retention_after,'retention_days',30)
    from updated
    join candidates on candidates.id=updated.id
    where candidates.profile_retention_notified_at is null
    returning session_id
  )
  select coalesce(jsonb_agg(jsonb_build_object(
    'session_id',updated.id,
    'user_id',updated.user_id,
    'retention_after',updated.profile_retention_after
  )), '[]'::jsonb)
  into v_items
  from updated;

  return jsonb_build_object('items',v_items,'retention_days',30,'claim_lease_seconds',300);
end;
$function$;

create or replace function public.moreai_ack_browser_profile_deleted(
  p_session_id uuid,
  p_user_id uuid
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_row public.moreai_browser_sessions%rowtype;
begin
  if p_session_id is null or p_user_id is null then
    raise exception 'browser_profile_ack_identity_invalid' using errcode='22023';
  end if;

  update public.moreai_browser_sessions
  set profile_deleted_at=now(), profile_retention_claimed_at=null
  where id=p_session_id
    and user_id=p_user_id
    and status in ('closed','expired')
    and profile_deleted_at is null
    and profile_retention_after <= now()
  returning * into v_row;

  if found then
    insert into public.moreai_browser_session_events(
      session_id,user_id,event_type,metadata
    ) values (
      p_session_id,p_user_id,'profile_deleted',
      jsonb_build_object('source','worker','retention_policy_days',30)
    );
    return jsonb_build_object('session_id',p_session_id,'status','profile_deleted');
  end if;

  select * into v_row
  from public.moreai_browser_sessions
  where id=p_session_id and user_id=p_user_id;

  if found and v_row.profile_deleted_at is not null then
    return jsonb_build_object('session_id',p_session_id,'status','profile_deleted','replayed',true);
  end if;

  raise exception 'browser_profile_retention_gate_not_satisfied' using errcode='23514';
end;
$function$;

revoke all on function public.moreai_claim_browser_profile_retention(integer) from public,anon,authenticated;
revoke all on function public.moreai_ack_browser_profile_deleted(uuid,uuid) from public,anon,authenticated;
grant execute on function public.moreai_claim_browser_profile_retention(integer) to service_role;
grant execute on function public.moreai_ack_browser_profile_deleted(uuid,uuid) to service_role;
