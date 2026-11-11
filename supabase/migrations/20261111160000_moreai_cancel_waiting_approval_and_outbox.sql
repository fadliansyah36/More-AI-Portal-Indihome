-- Cancellation is terminal for queued/approval-paused runs and observable through the durable outbox.
create or replace function public.moreai_worker_request_cancel(p_run_id uuid,p_user_id uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint; next_status text; event_type text; event_key text; v_event uuid:=gen_random_uuid(); v_payload jsonb;
begin
 select * into r from public.agent_runs where id=p_run_id and user_id=p_user_id for update;
 if not found then raise exception 'run not found' using errcode='P0002'; end if;
 if r.status in ('succeeded','failed','cancelled') then return jsonb_build_object('run_id',r.id,'status',r.status); end if;

 if r.status='queued' or r.status='waiting_approval' then
  next_status:='cancelled';
  update public.agent_runs set status='cancelled',cancel_requested_at=coalesce(cancel_requested_at,now()),
   finished_at=now(),lease_owner=null,lease_expires_at=null,heartbeat_at=null,updated_at=now()
   where id=r.id;
  update public.agent_tool_approvals set status='denied',decided_at=coalesce(decided_at,now()),decided_by=p_user_id
   where run_id=r.id and status='pending';
  update public.agent_run_approval_pauses set status='denied',decided_at=coalesce(decided_at,now())
   where run_id=r.id and status='pending';
  update public.agent_run_checkpoints set state=state||jsonb_build_object('status','cancelled','resume_pending',false),created_at=now()
   where run_id=r.id and checkpoint_key in (select checkpoint_key from public.agent_run_approval_pauses where run_id=r.id);
  event_type:='run.cancelled';
 else
  next_status:='cancel_requested';
  update public.agent_runs set cancel_requested_at=coalesce(cancel_requested_at,now()),updated_at=now() where id=r.id;
  event_type:='run.cancel_requested';
 end if;
 event_key:='user.cancel:'||r.id::text;
 v_payload:=jsonb_build_object('status',next_status,'requested_by',p_user_id);
 insert into public.agent_run_event_counters(run_id,last_sequence)
  values(r.id,coalesce((select max(sequence) from public.agent_run_events where run_id=r.id),0))
  on conflict(run_id) do nothing;
 perform 1 from public.agent_run_event_counters where run_id=r.id for update;
 if not exists(select 1 from public.outbox_events where aggregate_type='agent_run' and aggregate_id=r.id and event_key=event_key) then
  update public.agent_run_event_counters set last_sequence=last_sequence+1,updated_at=now()
   where run_id=r.id returning last_sequence into seq;
  insert into public.agent_run_events(id,run_id,event_type,sequence,payload,created_at)
   values(v_event,r.id,event_type,seq,v_payload,now());
  insert into public.outbox_events(id,aggregate_type,aggregate_id,event_type,payload,status,attempts,available_at,created_at,event_key,run_sequence)
   values(v_event,'agent_run',r.id,'run.event',jsonb_build_object('run_id',r.id,'event_id',v_event,'sequence',seq,
    'event_type',event_type,'event_payload',v_payload,'created_at',now()),'pending',0,now(),now(),event_key,seq);
 end if;
 return jsonb_build_object('run_id',r.id,'status',next_status);
end; $$;
revoke all on function public.moreai_worker_request_cancel(uuid,uuid) from public,anon,authenticated;
grant execute on function public.moreai_worker_request_cancel(uuid,uuid) to service_role;