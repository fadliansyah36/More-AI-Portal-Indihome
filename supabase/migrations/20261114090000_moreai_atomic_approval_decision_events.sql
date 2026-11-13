-- Phase 09: persist approval decision and run-resume lifecycle events in the
-- same transaction as the approval/pause/run/checkpoint state transition.
-- Forward-only: replaces the existing RPC; does not mutate live data on creation.

create or replace function public.moreai_append_approval_lifecycle_event(
  p_run_id uuid, p_event_key text, p_event_type text, p_payload jsonb
) returns bigint
language plpgsql security definer set search_path='' as $$
declare
  v_existing public.outbox_events;
  v_sequence bigint;
  v_event_id uuid := gen_random_uuid();
  v_created_at timestamptz := now();
begin
  if p_run_id is null or p_event_key is null or char_length(p_event_key) not between 1 and 200
     or p_event_type is null or p_event_type !~ '^[a-z][a-z0-9_.-]{0,79}$'
     or jsonb_typeof(coalesce(p_payload,'{}'::jsonb)) <> 'object'
     or octet_length(coalesce(p_payload,'{}'::jsonb)::text) > 16384 then
    raise exception 'invalid_approval_lifecycle_event' using errcode='22023';
  end if;

  select * into v_existing
    from public.outbox_events
   where aggregate_type='agent_run' and aggregate_id=p_run_id and event_key=p_event_key;
  if found then
    if v_existing.payload->>'event_type' <> p_event_type
       or v_existing.payload->'event_payload' <> coalesce(p_payload,'{}'::jsonb) then
      raise exception 'approval_event_idempotency_conflict' using errcode='22023';
    end if;
    return v_existing.run_sequence;
  end if;

  insert into public.agent_run_event_counters(run_id,last_sequence)
  values(p_run_id,coalesce((select max(sequence) from public.agent_run_events where run_id=p_run_id),0))
  on conflict(run_id) do nothing;
  perform 1 from public.agent_run_event_counters where run_id=p_run_id for update;

  -- Re-check after taking the per-run counter lock to serialize concurrent
  -- decision requests and preserve the existing unique event-key invariant.
  select * into v_existing
    from public.outbox_events
   where aggregate_type='agent_run' and aggregate_id=p_run_id and event_key=p_event_key;
  if found then
    if v_existing.payload->>'event_type' <> p_event_type
       or v_existing.payload->'event_payload' <> coalesce(p_payload,'{}'::jsonb) then
      raise exception 'approval_event_idempotency_conflict' using errcode='22023';
    end if;
    return v_existing.run_sequence;
  end if;

  update public.agent_run_event_counters
     set last_sequence=last_sequence+1,updated_at=v_created_at
   where run_id=p_run_id returning last_sequence into v_sequence;

  insert into public.agent_run_events(id,run_id,event_type,sequence,payload,created_at)
  values(v_event_id,p_run_id,p_event_type,v_sequence,coalesce(p_payload,'{}'::jsonb),v_created_at);

  insert into public.outbox_events(
    id,aggregate_type,aggregate_id,event_type,payload,status,attempts,available_at,
    created_at,event_key,run_sequence
  ) values(
    v_event_id,'agent_run',p_run_id,'run.event',
    jsonb_build_object(
      'run_id',p_run_id,'event_id',v_event_id,'sequence',v_sequence,
      'event_type',p_event_type,'event_payload',coalesce(p_payload,'{}'::jsonb),
      'created_at',v_created_at
    ),
    'pending',0,v_created_at,v_created_at,p_event_key,v_sequence
  );
  return v_sequence;
end;
$$;

revoke all on function public.moreai_append_approval_lifecycle_event(uuid,text,text,jsonb)
  from public,anon,authenticated;
grant execute on function public.moreai_append_approval_lifecycle_event(uuid,text,text,jsonb)
  to service_role;

create or replace function public.moreai_decide_tool_approval(
  p_approval_id uuid,p_user_id uuid,p_decision text
) returns jsonb
language plpgsql security definer set search_path='public',pg_temp as $$
declare
  a public.agent_tool_approvals%rowtype;
  p public.agent_run_approval_pauses%rowtype;
  v_status text;
  v_run_status text;
  v_event_type text;
  v_event_payload jsonb;
begin
  if p_decision not in ('approved','denied') then
    raise exception 'invalid_approval_decision' using errcode='22023';
  end if;

  select * into a
    from public.agent_tool_approvals
   where id=p_approval_id and user_id=p_user_id
   for update;
  if not found then
    raise exception 'approval_not_found' using errcode='P0002';
  end if;

  select * into p
    from public.agent_run_approval_pauses
   where approval_id=p_approval_id
   for update;

  if not found then
    if a.status in ('approved','denied','expired','consumed') then
      v_status:=a.status;
    else
      update public.agent_tool_approvals
         set status=case when expires_at<=now() then 'expired' else p_decision end,
             decided_at=now(),decided_by=p_user_id
       where id=p_approval_id
       returning * into a;
      v_status:=a.status;
    end if;

    v_event_type:=case v_status
      when 'approved' then 'tool.approval_granted'
      when 'denied' then 'tool.approval_denied'
      when 'expired' then 'tool.approval_expired'
      else null end;
    if v_event_type is not null then
      v_event_payload:=jsonb_build_object(
        'approval_id',a.id,'tool',a.tool_key,'status',v_status,
        'arguments_hash',a.arguments_hash,'decided_at',a.decided_at
      );
      perform public.moreai_append_approval_lifecycle_event(
        a.run_id,'approval.decision:'||a.id::text||':'||v_status,
        v_event_type,v_event_payload
      );
    end if;

    return jsonb_build_object(
      'id',a.id,'run_id',a.run_id,'status',v_status,'resumed',false
    );
  end if;

  if a.status='pending' then
    v_status:=case when a.expires_at<=now() then 'expired' else p_decision end;
    update public.agent_tool_approvals
       set status=v_status,decided_at=now(),decided_by=p_user_id
     where id=a.id
     returning * into a;
    update public.agent_run_approval_pauses
       set status=v_status,decided_at=now()
     where id=p.id
     returning * into p;
  else
    v_status:=a.status;
    if p.status<>v_status then
      raise exception 'approval_pause_state_conflict' using errcode='40001';
    end if;
  end if;

  v_event_type:=case v_status
    when 'approved' then 'tool.approval_granted'
    when 'denied' then 'tool.approval_denied'
    when 'expired' then 'tool.approval_expired'
    else null end;
  if v_event_type is not null then
    v_event_payload:=jsonb_build_object(
      'approval_id',a.id,'tool',a.tool_key,'status',v_status,
      'arguments_hash',a.arguments_hash,'decided_at',a.decided_at,
      'checkpoint_key',p.checkpoint_key
    );
    perform public.moreai_append_approval_lifecycle_event(
      a.run_id,'approval.decision:'||a.id::text||':'||v_status,
      v_event_type,v_event_payload
    );
  end if;

  update public.agent_runs
     set status='queued',resume_pending=true,available_at=now(),updated_at=now()
   where id=p.run_id and status='waiting_approval'
   returning status into v_run_status;

  update public.agent_run_checkpoints
     set state=state||jsonb_build_object(
       'status',v_status,'decided_at',a.decided_at,'resume_pending',true
     ),created_at=now()
   where run_id=p.run_id and checkpoint_key=p.checkpoint_key;

  if coalesce(v_run_status='queued',false) then
    perform public.moreai_append_approval_lifecycle_event(
      p.run_id,'approval.resume_queued:'||a.id::text,
      'run.resume_queued',
      jsonb_build_object(
        'approval_id',a.id,'status',v_status,
        'checkpoint_key',p.checkpoint_key,'resume_pending',true
      )
    );
  end if;

  return jsonb_build_object(
    'id',a.id,'run_id',a.run_id,'status',v_status,
    'resumed',coalesce(v_run_status='queued',false)
  );
end;
$$;

revoke all on function public.moreai_decide_tool_approval(uuid,uuid,text)
  from public,anon,authenticated;
grant execute on function public.moreai_decide_tool_approval(uuid,uuid,text)
  to service_role;
