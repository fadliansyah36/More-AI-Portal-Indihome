-- Durable, monotonic per-run event append with idempotent outbox records.
-- Apply only after reviewing against the live schema; this file is not applied by this commit.
create table if not exists public.agent_run_event_counters (
  run_id uuid primary key references public.agent_runs(id) on delete cascade,
  last_sequence bigint not null default 0 check (last_sequence >= 0),
  updated_at timestamptz not null default now()
);
alter table public.agent_run_event_counters enable row level security;
drop policy if exists agent_run_event_counters_server_only on public.agent_run_event_counters;
create policy agent_run_event_counters_server_only on public.agent_run_event_counters
  for all to anon, authenticated using (false) with check (false);
revoke all on public.agent_run_event_counters from anon, authenticated;
grant all on public.agent_run_event_counters to service_role;

create table if not exists public.agent_run_event_outbox (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  event_id uuid not null,
  event_key text not null check (char_length(event_key) between 1 and 200),
  event_type text not null check (char_length(event_type) between 1 and 80),
  sequence bigint not null check (sequence > 0),
  payload jsonb not null default '{}'::jsonb,
  delivery_state text not null default 'pending' check (delivery_state in ('pending','published','dead_letter')),
  attempts integer not null default 0 check (attempts >= 0),
  next_attempt_at timestamptz not null default now(),
  locked_by text,
  locked_until timestamptz,
  last_error_code text,
  created_at timestamptz not null default now(),
  published_at timestamptz,
  unique(run_id,event_key),
  unique(run_id,sequence)
);
create index if not exists agent_run_event_outbox_pending_idx
  on public.agent_run_event_outbox(next_attempt_at,created_at)
  where delivery_state='pending';

alter table public.agent_run_event_outbox
  add column if not exists next_attempt_at timestamptz not null default now(),
  add column if not exists locked_by text,
  add column if not exists locked_until timestamptz,
  add column if not exists last_error_code text;
alter table public.agent_run_event_outbox enable row level security;
drop policy if exists agent_run_event_outbox_server_only on public.agent_run_event_outbox;
create policy agent_run_event_outbox_server_only on public.agent_run_event_outbox
  for all to anon, authenticated using (false) with check (false);
revoke all on public.agent_run_event_outbox from anon, authenticated;
grant all on public.agent_run_event_outbox to service_role;

create or replace function public.moreai_worker_append_run_event(
  p_run_id uuid,
  p_event_key text,
  p_event_type text,
  p_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_existing public.agent_run_event_outbox;
  v_sequence bigint;
  v_event_id uuid := gen_random_uuid();
  v_payload jsonb := coalesce(p_payload,'{}'::jsonb);
begin
  if p_run_id is null or p_event_key is null or char_length(p_event_key) not between 1 and 200
     or p_event_type is null or p_event_type !~ '^[a-z][a-z0-9_.-]{0,79}$'
     or jsonb_typeof(v_payload) <> 'object' or octet_length(v_payload::text) > 16384 then
    raise exception 'invalid_run_event' using errcode='22023';
  end if;
  if not exists(select 1 from public.agent_runs where id=p_run_id) then
    raise exception 'agent_run_not_found' using errcode='P0002';
  end if;

  insert into public.agent_run_event_counters(run_id,last_sequence)
  values(
    p_run_id,
    coalesce((select max(sequence) from public.agent_run_events where run_id=p_run_id),0)
  ) on conflict(run_id) do nothing;

  -- Serialize appends for this run and return the original event on retries.
  perform 1 from public.agent_run_event_counters where run_id=p_run_id for update;
  select * into v_existing from public.agent_run_event_outbox
    where run_id=p_run_id and event_key=p_event_key;
  if found then
    if v_existing.event_type <> p_event_type or v_existing.payload <> v_payload then
      raise exception 'run_event_idempotency_conflict' using errcode='22023';
    end if;
    return jsonb_build_object('event_id',v_existing.event_id,'sequence',v_existing.sequence,'duplicate',true);
  end if;

  update public.agent_run_event_counters
    set last_sequence=last_sequence+1,updated_at=now()
    where run_id=p_run_id returning last_sequence into v_sequence;

  insert into public.agent_run_events(id,run_id,event_type,sequence,payload,created_at)
    values(v_event_id,p_run_id,p_event_type,v_sequence,v_payload,now());

  insert into public.agent_run_event_outbox(
    run_id,event_id,event_key,event_type,sequence,payload
  ) values(p_run_id,v_event_id,p_event_key,p_event_type,v_sequence,v_payload);

  return jsonb_build_object('event_id',v_event_id,'sequence',v_sequence,'duplicate',false);
end;
$$;

revoke all on function public.moreai_worker_append_run_event(uuid,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.moreai_worker_append_run_event(uuid,text,text,jsonb) to service_role;

-- Lease a batch for exactly one publisher. SKIP LOCKED supports horizontal workers.
create or replace function public.moreai_worker_claim_event_outbox(
  p_worker_id text, p_limit integer default 20, p_lease_seconds integer default 30
) returns setof public.agent_run_event_outbox
language plpgsql security definer set search_path=public,pg_temp as $$
begin
  if p_worker_id is null or char_length(p_worker_id) not between 8 and 128
     or p_limit not between 1 and 100 or p_lease_seconds not between 10 and 300 then
    raise exception 'invalid_outbox_claim' using errcode='22023';
  end if;
  return query
  with candidates as (
    select id from public.agent_run_event_outbox
    where delivery_state='pending' and next_attempt_at <= now()
      and (locked_until is null or locked_until < now())
    order by created_at,id
    for update skip locked
    limit p_limit
  )
  update public.agent_run_event_outbox o
    set locked_by=p_worker_id,locked_until=now()+make_interval(secs=>p_lease_seconds)
    from candidates c where o.id=c.id
    returning o.*;
end;
$$;

create or replace function public.moreai_worker_ack_event_outbox(
  p_event_id uuid, p_worker_id text
) returns boolean
language plpgsql security definer set search_path=public,pg_temp as $$
declare v_count integer;
begin
  update public.agent_run_event_outbox
    set delivery_state='published',published_at=now(),locked_by=null,locked_until=null,last_error_code=null
    where id=p_event_id and delivery_state='pending' and locked_by=p_worker_id
      and locked_until > now();
  get diagnostics v_count=row_count;
  return v_count=1;
end;
$$;

create or replace function public.moreai_worker_retry_event_outbox(
  p_event_id uuid, p_worker_id text, p_error_code text
) returns text
language plpgsql security definer set search_path=public,pg_temp as $$
declare v_attempts integer; v_state text;
begin
  update public.agent_run_event_outbox
    set attempts=attempts+1,
        delivery_state=case when attempts+1 >= 12 then 'dead_letter' else 'pending' end,
        next_attempt_at=now()+make_interval(secs=>least(3600,power(2,least(attempts,10))::integer)),
        locked_by=null,locked_until=null,
        last_error_code=left(coalesce(p_error_code,'publish_failed'),80)
    where id=p_event_id and delivery_state='pending' and locked_by=p_worker_id
    returning attempts,delivery_state into v_attempts,v_state;
  if not found then raise exception 'outbox_lease_lost' using errcode='40001'; end if;
  return v_state;
end;
$$;

revoke all on function public.moreai_worker_claim_event_outbox(text,integer,integer) from public,anon,authenticated;
revoke all on function public.moreai_worker_ack_event_outbox(uuid,text) from public,anon,authenticated;
revoke all on function public.moreai_worker_retry_event_outbox(uuid,text,text) from public,anon,authenticated;
grant execute on function public.moreai_worker_claim_event_outbox(text,integer,integer) to service_role;
grant execute on function public.moreai_worker_ack_event_outbox(uuid,text) to service_role;
grant execute on function public.moreai_worker_retry_event_outbox(uuid,text,text) to service_role;
