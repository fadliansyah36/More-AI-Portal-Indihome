-- Phase 07A: extend the canonical outbox_events table; do not create a parallel outbox.
-- Reconciled against live MoreAI schema: outbox_events status supports
-- pending/processing/published/failed/dead_letter and has aggregate/event payload columns.
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

alter table public.outbox_events
  add column if not exists event_key text,
  add column if not exists run_sequence bigint,
  add column if not exists worker_id text,
  add column if not exists lease_expires_at timestamptz;

create unique index if not exists outbox_events_run_event_key_uq
  on public.outbox_events(aggregate_type,aggregate_id,event_key)
  where event_key is not null;
create unique index if not exists outbox_events_run_sequence_uq
  on public.outbox_events(aggregate_id,run_sequence)
  where aggregate_type='agent_run' and run_sequence is not null;

create index if not exists outbox_events_worker_lease_idx
  on public.outbox_events(status,available_at,lease_expires_at,created_at)
  where status in ('pending','failed','processing');

alter table public.agent_run_event_counters enable row level security;
revoke all on public.agent_run_event_counters from anon, authenticated;

create or replace function public.moreai_worker_append_run_event(
  p_run_id uuid, p_worker_id text, p_event_key text, p_event_type text, p_payload jsonb default '{}'::jsonb
) returns jsonb
language plpgsql security definer set search_path='' as $$
declare
  v_existing public.outbox_events;
  v_sequence bigint;
  v_event_id uuid := gen_random_uuid();
  v_payload jsonb := coalesce(p_payload,'{}'::jsonb);
begin
  if p_run_id is null or p_event_key is null or char_length(p_event_key) not between 1 and 200
     or p_event_type is null or p_event_type !~ '^[a-z][a-z0-9_.-]{0,79}$'
     or jsonb_typeof(v_payload) <> 'object' or octet_length(v_payload::text) > 16384 then
    raise exception 'invalid_run_event' using errcode='22023';
  end if;
  if p_worker_id is null or not exists(
    select 1 from public.agent_runs
    where id=p_run_id and status='running' and lease_owner=p_worker_id and lease_expires_at>now()
  ) then
    raise exception 'worker_lease_not_held' using errcode='42501';
  end if;
  insert into public.agent_run_event_counters(run_id,last_sequence)
  values(p_run_id,coalesce((select max(sequence) from public.agent_run_events where run_id=p_run_id),0))
  on conflict(run_id) do nothing;
  perform 1 from public.agent_run_event_counters where run_id=p_run_id for update;

  select * into v_existing from public.outbox_events
    where aggregate_type='agent_run' and aggregate_id=p_run_id and event_key=p_event_key;
  if found then
    if v_existing.payload->>'event_type' <> p_event_type
       or v_existing.payload->'event_payload' <> v_payload then
      raise exception 'run_event_idempotency_conflict' using errcode='22023';
    end if;
    return jsonb_build_object(
      'event_id',v_existing.id,'sequence',v_existing.run_sequence,'duplicate',true
    );
  end if;

  update public.agent_run_event_counters
    set last_sequence=last_sequence+1,updated_at=now()
    where run_id=p_run_id returning last_sequence into v_sequence;

  insert into public.agent_run_events(id,run_id,event_type,sequence,payload,created_at)
    values(v_event_id,p_run_id,p_event_type,v_sequence,v_payload,now());

  insert into public.outbox_events(
    id,aggregate_type,aggregate_id,event_type,payload,status,attempts,available_at,
    created_at,event_key,run_sequence
  ) values(
    v_event_id,'agent_run',p_run_id,'run.event',
    jsonb_build_object(
      'run_id',p_run_id,'event_id',v_event_id,'sequence',v_sequence,
      'event_type',p_event_type,'event_payload',v_payload,'created_at',now()
    ),
    'pending',0,now(),now(),p_event_key,v_sequence
  );

  return jsonb_build_object('event_id',v_event_id,'sequence',v_sequence,'duplicate',false);
end;
$$;

-- Route legacy checkpoint writes through the same serialized counter/outbox path.
create or replace function public.moreai_worker_checkpoint(
  p_run_id uuid, p_worker_id text, p_checkpoint_key text, p_state jsonb
) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_event jsonb;
begin
  if p_checkpoint_key is null or char_length(p_checkpoint_key) not between 1 and 200
     or jsonb_typeof(p_state) <> 'object' then
    raise exception 'invalid_checkpoint' using errcode='22023';
  end if;
  if not exists(select 1 from public.agent_runs where id=p_run_id and status='running'
      and lease_owner=p_worker_id and lease_expires_at>now()) then
    raise exception 'worker_lease_not_held' using errcode='42501';
  end if;
  insert into public.agent_run_checkpoints(run_id,checkpoint_key,state)
    values(p_run_id,p_checkpoint_key,p_state)
    on conflict(run_id,checkpoint_key) do update
      set state=excluded.state,created_at=now();
  update public.agent_runs set last_checkpoint_key=p_checkpoint_key,updated_at=now()
    where id=p_run_id;
  v_event := public.moreai_worker_append_run_event(
    p_run_id,p_worker_id,'worker.checkpoint:'||p_checkpoint_key,
    'worker.checkpoint',jsonb_build_object('checkpoint_key',p_checkpoint_key)
  );
  return jsonb_build_object(
    'run_id',p_run_id,'checkpoint_key',p_checkpoint_key,
    'sequence',(v_event->>'sequence')::bigint
  );
end;
$$;

-- Finish writes the terminal/queued event before releasing the worker lease.
create or replace function public.moreai_worker_finish_run(
  p_run_id uuid, p_worker_id text, p_status text,
  p_output jsonb default null, p_error jsonb default null,
  p_retry_delay_seconds integer default 30
) returns jsonb
language plpgsql security definer set search_path='' as $$
declare
  r public.agent_runs%rowtype;
  next_status text;
  dead boolean := false;
  event_type text;
  event_key text;
begin
  if p_status not in ('succeeded','failed','cancelled') then
    raise exception 'invalid terminal status';
  end if;
  select * into r from public.agent_runs where id=p_run_id for update;
  if not found then raise exception 'run not found'; end if;
  if r.status in ('succeeded','failed','cancelled') then
    return jsonb_build_object('run_id',r.id,'status',r.status);
  end if;
  if r.lease_owner is distinct from p_worker_id or r.lease_expires_at <= now() then
    raise exception 'worker lease mismatch';
  end if;
  if r.cancel_requested_at is not null then
    next_status := 'cancelled';
  elsif p_status='failed' and r.attempt<r.max_attempts then
    next_status := 'queued';
  elsif p_status='failed' then
    next_status := 'failed'; dead := true;
  else
    next_status := p_status;
  end if;
  event_type := case when dead then 'worker.dead_lettered' else 'worker.'||next_status end;
  event_key := 'worker.finish:'||r.attempt::text||':'||next_status;
  perform public.moreai_worker_append_run_event(
    p_run_id,p_worker_id,event_key,event_type,
    jsonb_build_object('attempt',r.attempt,'error_code',
      case when p_error is null then null else coalesce(p_error->>'code','execution_failed') end)
  );
  if next_status='queued' then
    update public.agent_runs set status=next_status,error=p_error,
      available_at=now()+make_interval(secs=>greatest(1,least(p_retry_delay_seconds,3600))),
      lease_owner=null,lease_expires_at=null,heartbeat_at=null,updated_at=now()
      where id=r.id;
  else
    update public.agent_runs set status=next_status,output=p_output,error=p_error,
      finished_at=now(),dead_lettered_at=case when dead then now() else dead_lettered_at end,
      lease_owner=null,lease_expires_at=null,heartbeat_at=null,updated_at=now()
      where id=r.id;
  end if;
  return jsonb_build_object('run_id',r.id,'status',next_status,'attempt',r.attempt,'dead_lettered',dead);
end;
$$;

create or replace function public.moreai_worker_claim_event_outbox(
  p_worker_id text, p_limit integer default 20, p_lease_seconds integer default 45
) returns setof public.outbox_events
language plpgsql security definer set search_path=public,pg_temp as $$
begin
  if p_worker_id is null or char_length(p_worker_id) not between 8 and 128
     or p_limit not between 1 and 100 or p_lease_seconds not between 10 and 300 then
    raise exception 'invalid_outbox_claim' using errcode='22023';
  end if;
  return query
  with candidates as (
    select id from public.outbox_events
    where aggregate_type='agent_run' and event_type='run.event'
      and (
        status in ('pending','failed') and available_at <= now()
        or status='processing' and lease_expires_at < now()
      )
    order by created_at,id for update skip locked limit p_limit
  )
  update public.outbox_events o
    set status='processing',worker_id=p_worker_id,locked_at=now(),
        lease_expires_at=now()+make_interval(secs=>p_lease_seconds)
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
  update public.outbox_events
    set status='published',published_at=now(),worker_id=null,lease_expires_at=null,last_error=null
    where id=p_event_id and status='processing' and worker_id=p_worker_id
      and lease_expires_at > now();
  get diagnostics v_count=row_count;
  return v_count=1;
end;
$$;

create or replace function public.moreai_worker_retry_event_outbox(
  p_event_id uuid, p_worker_id text, p_error_code text
) returns text
language plpgsql security definer set search_path=public,pg_temp as $$
declare v_state text;
begin
  update public.outbox_events
    set attempts=attempts+1,
        status=case when attempts+1 >= 12 then 'dead_letter' else 'failed' end,
        available_at=now()+make_interval(secs=>least(3600,power(2,least(attempts,10))::integer)),
        worker_id=null,lease_expires_at=null,last_error=left(coalesce(p_error_code,'publish_failed'),200)
    where id=p_event_id and status='processing' and worker_id=p_worker_id
    returning status into v_state;
  if not found then raise exception 'outbox_lease_lost' using errcode='40001'; end if;
  return v_state;
end;
$$;

revoke all on function public.moreai_worker_append_run_event(uuid,text,text,text,jsonb) from public,anon,authenticated;
revoke all on function public.moreai_worker_claim_event_outbox(text,integer,integer) from public,anon,authenticated;
revoke all on function public.moreai_worker_ack_event_outbox(uuid,text) from public,anon,authenticated;
revoke all on function public.moreai_worker_retry_event_outbox(uuid,text,text) from public,anon,authenticated;
grant execute on function public.moreai_worker_append_run_event(uuid,text,text,text,jsonb) to service_role;
grant execute on function public.moreai_worker_claim_event_outbox(text,integer,integer) to service_role;
grant execute on function public.moreai_worker_ack_event_outbox(uuid,text) to service_role;
grant execute on function public.moreai_worker_retry_event_outbox(uuid,text,text) to service_role;
