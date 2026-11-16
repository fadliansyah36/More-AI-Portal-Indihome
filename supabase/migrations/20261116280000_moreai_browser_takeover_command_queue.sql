-- Include the existing close lifecycle and the new durable takeover audit event.
alter table public.moreai_browser_session_events
  drop constraint if exists moreai_browser_session_events_event_type_check;
alter table public.moreai_browser_session_events
  add constraint moreai_browser_session_events_event_type_check
  check (event_type in (
    'created','restored','state_saved','close_requested','closed','expired',
    'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
    'takeover_input_succeeded','takeover_input_failed','takeover_command_queued'
  ));

-- Durable, encrypted transport for customer-authorized OpenFuse Human Takeover.
create table if not exists public.moreai_browser_takeover_commands (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.moreai_browser_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  grant_id uuid not null unique references public.moreai_browser_takeover_grants(id) on delete cascade,
  encrypted_command text not null,
  status text not null default 'queued'
    check (status in ('queued','processing','succeeded','failed','expired')),
  attempts integer not null default 0 check (attempts between 0 and 5),
  claimed_by text,
  lease_expires_at timestamptz,
  result jsonb,
  error_code text,
  created_at timestamptz not null default now(),
  claimed_at timestamptz,
  finished_at timestamptz,
  constraint takeover_command_terminal_result check (
    (status in ('succeeded','failed','expired') and finished_at is not null)
    or status in ('queued','processing')
  )
);
create index if not exists moreai_browser_takeover_commands_queue_idx
  on public.moreai_browser_takeover_commands(status, created_at);
create index if not exists moreai_browser_takeover_commands_owner_idx
  on public.moreai_browser_takeover_commands(user_id, created_at desc);
alter table public.moreai_browser_takeover_commands enable row level security;
revoke all on public.moreai_browser_takeover_commands from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_browser_takeover_commands to service_role;
drop policy if exists moreai_browser_takeover_commands_server_only on public.moreai_browser_takeover_commands;
create policy moreai_browser_takeover_commands_server_only
  on public.moreai_browser_takeover_commands for all to anon, authenticated
  using (false) with check (false);

create or replace function public.moreai_claim_browser_takeover_commands(
  p_worker_id text,
  p_limit integer default 10
) returns setof public.moreai_browser_takeover_commands
language plpgsql security definer
set search_path=''
as $function$
begin
  if p_worker_id !~ '^[A-Za-z0-9._:-]{8,128}    select c.id
    from public.moreai_browser_takeover_commands c
    join public.moreai_browser_sessions s on s.id=c.session_id and s.user_id=c.user_id
    join public.moreai_browser_takeover_grants g on g.id=c.grant_id and g.session_id=c.session_id and g.user_id=c.user_id
    where s.status='active' and s.expires_at>now()
      and g.consumed_at is null and g.revoked_at is null and g.expires_at>now()
      and c.attempts < 5
      and c.status='queued'
    order by c.created_at
    for update of c skip locked
    limit p_limit
  )
  update public.moreai_browser_takeover_commands c
  set status='processing', claimed_by=p_worker_id,
      lease_expires_at=now()+interval '45 seconds',
      claimed_at=now(), attempts=c.attempts+1
  from candidates
  where c.id=candidates.id
  returning c.*;
end;
$function$;
revoke all on function public.moreai_claim_browser_takeover_commands(text,integer) from public,anon,authenticated;
grant execute on function public.moreai_claim_browser_takeover_commands(text,integer) to service_role;

create or replace function public.moreai_finish_browser_takeover_command(
  p_command_id uuid,
  p_worker_id text,
  p_status text,
  p_result jsonb default null,
  p_error_code text default null
) returns jsonb
language plpgsql security definer
set search_path=''
as $function$
declare v_row public.moreai_browser_takeover_commands%rowtype;
begin
  if p_status not in ('succeeded','failed') then
    raise exception 'takeover_command_status_invalid' using errcode='22023';
  end if;
  update public.moreai_browser_takeover_commands
  set status=p_status, result=case when p_status='succeeded' then coalesce(p_result,'{}'::jsonb) else null end,
      error_code=case when p_status='failed' then left(coalesce(p_error_code,'takeover_input_failed'),100) else null end,
      finished_at=now(), lease_expires_at=null
  where id=p_command_id and status='processing' and claimed_by=p_worker_id
    and lease_expires_at>now()
  returning * into v_row;
  if not found then
    raise exception 'takeover_command_worker_lease_lost' using errcode='40001';
  end if;
  return jsonb_build_object('id',v_row.id,'status',v_row.status,'finished_at',v_row.finished_at);
end;
$function$;
revoke all on function public.moreai_finish_browser_takeover_command(uuid,text,text,jsonb,text) from public,anon,authenticated;
grant execute on function public.moreai_finish_browser_takeover_command(uuid,text,text,jsonb,text) to service_role;

-- Revoke queued commands alongside grants on logout/session closure.
create or replace function public.moreai_revoke_browser_takeover_commands_on_grant()
returns trigger language plpgsql security definer set search_path=''
as $function$
begin
  if new.revoked_at is not null and old.revoked_at is null then
    update public.moreai_browser_takeover_commands
      set status='expired', encrypted_command='[revoked]', finished_at=now(), lease_expires_at=null,
          error_code='takeover_grant_revoked'
    where grant_id=new.id and status in ('queued','processing');
  end if;
  return new;
end;
$function$;
revoke all on function public.moreai_revoke_browser_takeover_commands_on_grant() from public,anon,authenticated;
drop trigger if exists moreai_browser_takeover_commands_revoke_grant on public.moreai_browser_takeover_grants;
create trigger moreai_browser_takeover_commands_revoke_grant
after update of revoked_at on public.moreai_browser_takeover_grants
for each row execute function public.moreai_revoke_browser_takeover_commands_on_grant();
 or p_limit < 1 or p_limit > 25 then
    raise exception 'takeover_command_claim_payload_invalid' using errcode='22023';
  end if;
  -- Expired queued grants are terminal. A command whose worker lease elapsed
  -- is marked unknown/failed rather than replayed: the one-time grant may
  -- already have been consumed and the browser action may have reached Chromium.
  update public.moreai_browser_takeover_commands c
  set status='expired', encrypted_command='[expired]', finished_at=now(),
      lease_expires_at=null, error_code='takeover_grant_expired'
  where c.status='queued' and not exists (
    select 1 from public.moreai_browser_takeover_grants g
    join public.moreai_browser_sessions s on s.id=g.session_id and s.user_id=g.user_id
    where g.id=c.grant_id and g.consumed_at is null and g.revoked_at is null
      and g.expires_at>now() and s.status='active' and s.expires_at>now()
  );
  update public.moreai_browser_takeover_commands c
  set status='failed', encrypted_command='[outcome_unknown]', finished_at=now(),
      lease_expires_at=null, error_code='worker_lease_expired_outcome_unknown'
  where c.status='processing' and c.lease_expires_at<now();
  return query
  with candidates as (
    select c.id
    from public.moreai_browser_takeover_commands c
    join public.moreai_browser_sessions s on s.id=c.session_id and s.user_id=c.user_id
    join public.moreai_browser_takeover_grants g on g.id=c.grant_id and g.session_id=c.session_id and g.user_id=c.user_id
    where s.status='active' and s.expires_at>now()
      and g.consumed_at is null and g.revoked_at is null and g.expires_at>now()
      and c.attempts < 5
      and (c.status='queued' or (c.status='processing' and c.lease_expires_at<now()))
    order by c.created_at
    for update of c skip locked
    limit p_limit
  )
  update public.moreai_browser_takeover_commands c
  set status='processing', claimed_by=p_worker_id,
      lease_expires_at=now()+interval '45 seconds',
      claimed_at=now(), attempts=c.attempts+1
  from candidates
  where c.id=candidates.id
  returning c.*;
end;
$function$;
revoke all on function public.moreai_claim_browser_takeover_commands(text,integer) from public,anon,authenticated;
grant execute on function public.moreai_claim_browser_takeover_commands(text,integer) to service_role;

create or replace function public.moreai_finish_browser_takeover_command(
  p_command_id uuid,
  p_worker_id text,
  p_status text,
  p_result jsonb default null,
  p_error_code text default null
) returns jsonb
language plpgsql security definer
set search_path=''
as $function$
declare v_row public.moreai_browser_takeover_commands%rowtype;
begin
  if p_status not in ('succeeded','failed') then
    raise exception 'takeover_command_status_invalid' using errcode='22023';
  end if;
  update public.moreai_browser_takeover_commands
  set status=p_status, result=case when p_status='succeeded' then coalesce(p_result,'{}'::jsonb) else null end,
      error_code=case when p_status='failed' then left(coalesce(p_error_code,'takeover_input_failed'),100) else null end,
      finished_at=now(), lease_expires_at=null
  where id=p_command_id and status='processing' and claimed_by=p_worker_id
    and lease_expires_at>now()
  returning * into v_row;
  if not found then
    raise exception 'takeover_command_worker_lease_lost' using errcode='40001';
  end if;
  return jsonb_build_object('id',v_row.id,'status',v_row.status,'finished_at',v_row.finished_at);
end;
$function$;
revoke all on function public.moreai_finish_browser_takeover_command(uuid,text,text,jsonb,text) from public,anon,authenticated;
grant execute on function public.moreai_finish_browser_takeover_command(uuid,text,text,jsonb,text) to service_role;

-- Revoke queued commands alongside grants on logout/session closure.
create or replace function public.moreai_revoke_browser_takeover_commands_on_grant()
returns trigger language plpgsql security definer set search_path=''
as $function$
begin
  if new.revoked_at is not null and old.revoked_at is null then
    update public.moreai_browser_takeover_commands
      set status='expired', encrypted_command='[revoked]', finished_at=now(), lease_expires_at=null,
          error_code='takeover_grant_revoked'
    where grant_id=new.id and status in ('queued','processing');
  end if;
  return new;
end;
$function$;
revoke all on function public.moreai_revoke_browser_takeover_commands_on_grant() from public,anon,authenticated;
drop trigger if exists moreai_browser_takeover_commands_revoke_grant on public.moreai_browser_takeover_grants;
create trigger moreai_browser_takeover_commands_revoke_grant
after update of revoked_at on public.moreai_browser_takeover_grants
for each row execute function public.moreai_revoke_browser_takeover_commands_on_grant();
