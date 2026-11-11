alter table public.agent_runs add column if not exists resume_pending boolean not null default false;
create table if not exists public.agent_run_approval_pauses (
 id uuid primary key default gen_random_uuid(), run_id uuid not null references public.agent_runs(id) on delete cascade,
 approval_id uuid not null unique references public.agent_tool_approvals(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade, tool_key text not null,
 arguments_hash text not null check(arguments_hash ~ '^[0-9a-f]{64}$'),
 status text not null default 'pending' check(status in ('pending','approved','denied','expired','consumed')),
 checkpoint_key text not null, created_at timestamptz not null default now(),
 decided_at timestamptz, resumed_at timestamptz, unique(run_id,tool_key,arguments_hash)
);
create index if not exists agent_run_approval_pauses_pending_idx on public.agent_run_approval_pauses(status,created_at) where status='pending';
alter table public.agent_run_approval_pauses enable row level security;
drop policy if exists agent_run_approval_pauses_server_only on public.agent_run_approval_pauses;
create policy agent_run_approval_pauses_server_only on public.agent_run_approval_pauses for all to anon,authenticated using(false) with check(false);
revoke all on public.agent_run_approval_pauses from public,anon,authenticated;
grant all on public.agent_run_approval_pauses to service_role;

create or replace function public.moreai_worker_pause_for_tool_approval(
 p_run_id uuid,p_user_id uuid,p_worker_id text,p_tool_key text,p_arguments_hash text,p_summary text,p_expires_in_seconds integer default 900
) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; a_id uuid; p public.agent_run_approval_pauses%rowtype; v_key text; v_state jsonb;
begin
 select * into r from public.agent_runs where id=p_run_id for update;
 if not found or r.user_id is distinct from p_user_id then raise exception 'approval_run_owner_mismatch' using errcode='42501'; end if;
 if r.status<>'running' or r.lease_owner is distinct from p_worker_id or r.lease_expires_at<=now() then raise exception 'worker_lease_not_held' using errcode='42501'; end if;
 select * into p from public.agent_run_approval_pauses where run_id=p_run_id and tool_key=p_tool_key and arguments_hash=p_arguments_hash for update;
 if found then
  if p.status in ('approved','denied','expired','consumed') then return jsonb_build_object('approval_id',p.approval_id,'status',p.status,'resumed',true); end if;
  if p.status='pending' then raise exception 'approval_already_pending' using errcode='55000'; end if;
 end if;
 a_id:=public.moreai_request_tool_approval(p_run_id,p_user_id,p_tool_key,p_arguments_hash,p_summary,p_expires_in_seconds);
 v_key:='approval.pause.'||a_id::text;
 insert into public.agent_run_approval_pauses(run_id,approval_id,user_id,tool_key,arguments_hash,status,checkpoint_key)
 values(p_run_id,a_id,p_user_id,p_tool_key,p_arguments_hash,'pending',v_key)
 on conflict(run_id,tool_key,arguments_hash) do update set approval_id=excluded.approval_id,status='pending',checkpoint_key=excluded.checkpoint_key,created_at=now(),decided_at=null,resumed_at=null returning * into p;
 v_state:=jsonb_build_object('approval_id',a_id,'tool_key',p_tool_key,'arguments_hash',p_arguments_hash,'status','pending','attempt',r.attempt,'checkpoint_key',v_key);
 insert into public.agent_run_checkpoints(run_id,checkpoint_key,state) values(p_run_id,v_key,v_state)
 on conflict(run_id,checkpoint_key) do update set state=excluded.state,created_at=now();
 update public.agent_runs set status='waiting_approval',last_checkpoint_key=v_key,lease_owner=null,lease_expires_at=null,heartbeat_at=null,updated_at=now()
 where id=p_run_id and status='running' and lease_owner=p_worker_id;
 return jsonb_build_object('approval_id',a_id,'status','pending','checkpoint_key',v_key);
end; $$;

create or replace function public.moreai_decide_tool_approval(p_approval_id uuid,p_user_id uuid,p_decision text)
returns jsonb language plpgsql security definer set search_path='public',pg_temp as $$
declare a public.agent_tool_approvals%rowtype; p public.agent_run_approval_pauses%rowtype; v_status text; v_run_status text;
begin
 if p_decision not in ('approved','denied') then raise exception 'invalid_approval_decision' using errcode='22023'; end if;
 select * into a from public.agent_tool_approvals where id=p_approval_id and user_id=p_user_id for update;
 if not found then raise exception 'approval_not_found' using errcode='P0002'; end if;
 select * into p from public.agent_run_approval_pauses where approval_id=p_approval_id for update;
 if not found then
  if a.status in ('approved','denied','expired','consumed') then return jsonb_build_object('id',a.id,'run_id',a.run_id,'status',a.status,'resumed',false); end if;
  update public.agent_tool_approvals set status=case when expires_at<=now() then 'expired' else p_decision end,decided_at=now(),decided_by=p_user_id where id=p_approval_id returning * into a;
  return jsonb_build_object('id',a.id,'run_id',a.run_id,'status',a.status,'resumed',false);
 end if;
 if a.status='pending' then
  v_status:=case when a.expires_at<=now() then 'expired' else p_decision end;
  update public.agent_tool_approvals set status=v_status,decided_at=now(),decided_by=p_user_id where id=a.id returning * into a;
  update public.agent_run_approval_pauses set status=v_status,decided_at=now() where id=p.id returning * into p;
 else
  v_status:=a.status;
  if p.status<>v_status then raise exception 'approval_pause_state_conflict' using errcode='40001'; end if;
 end if;
 update public.agent_runs set status='queued',resume_pending=true,available_at=now(),updated_at=now()
 where id=p.run_id and status='waiting_approval' returning status into v_run_status;
 update public.agent_run_checkpoints set state=state||jsonb_build_object('status',v_status,'decided_at',a.decided_at,'resume_pending',true),created_at=now()
 where run_id=p.run_id and checkpoint_key=p.checkpoint_key;
 return jsonb_build_object('id',a.id,'run_id',a.run_id,'status',v_status,'resumed',coalesce(v_run_status='queued',false));
end; $$;

create or replace function public.moreai_worker_claim_run(p_worker_id text,p_lease_seconds integer default 90)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint; d record;
begin
 if p_worker_id is null or length(p_worker_id)<8 or length(p_worker_id)>128 or p_lease_seconds not between 15 and 900 then raise exception 'invalid worker claim'; end if;
 for d in select p.id,p.run_id,p.approval_id,p.checkpoint_key from public.agent_run_approval_pauses p join public.agent_tool_approvals a on a.id=p.approval_id
  where p.status='pending' and a.expires_at<=now() for update of p,a skip locked
 loop
  update public.agent_tool_approvals set status='expired',decided_at=now() where id=d.approval_id and status='pending';
  update public.agent_run_approval_pauses set status='expired',decided_at=now() where id=d.id and status='pending';
  update public.agent_runs set status=case when cancel_requested_at is not null then 'cancelled' else 'queued' end,
   resume_pending=(cancel_requested_at is null),finished_at=case when cancel_requested_at is not null then now() else finished_at end,available_at=now(),updated_at=now()
   where id=d.run_id and status='waiting_approval';
  update public.agent_run_checkpoints set state=state||jsonb_build_object('status','expired','resume_pending',true),created_at=now()
   where run_id=d.run_id and checkpoint_key=d.checkpoint_key;
 end loop;
 for d in update public.agent_runs set status='failed',finished_at=now(),dead_lettered_at=now(),lease_owner=null,lease_expires_at=null,updated_at=now()
  where status='running' and lease_expires_at<now() and attempt>=max_attempts returning id
 loop
  select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=d.id;
  insert into public.agent_run_events(run_id,event_type,sequence,payload) values(d.id,'worker.dead_lettered',seq,'{"reason":"lease_expired_max_attempts"}'::jsonb);
 end loop;
 select * into r from public.agent_runs where ((status='queued' and available_at<=now()) or (status='running' and lease_expires_at<now()))
  and attempt<max_attempts and cancel_requested_at is null
  and not exists(select 1 from public.agent_run_approval_pauses p where p.run_id=agent_runs.id and p.status='pending')
  order by available_at,created_at for update skip locked limit 1;
 if not found then return null; end if;
 update public.agent_runs set status='running',attempt=attempt+case when resume_pending then 0 else 1 end,resume_pending=false,
  lease_owner=p_worker_id,lease_expires_at=now()+make_interval(secs=>p_lease_seconds),heartbeat_at=now(),
  started_at=coalesce(started_at,now()),updated_at=now() where id=r.id returning * into r;
 update public.agent_run_approval_pauses set resumed_at=coalesce(resumed_at,now()) where run_id=r.id and status in ('approved','denied','expired');
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(r.id,'worker.claimed',seq,
  jsonb_build_object('worker_id',p_worker_id,'attempt',r.attempt,'lease_seconds',p_lease_seconds,'approval_resume',r.resume_pending));
 return jsonb_build_object('id',r.id,'user_id',r.user_id,'workspace_id',r.workspace_id,'conversation_id',r.conversation_id,
  'agent_definition_id',r.agent_definition_id,'status',r.status,'attempt',r.attempt,'max_attempts',r.max_attempts,
  'input',r.input,'lease_owner',r.lease_owner,'lease_expires_at',r.lease_expires_at);
end; $$;

revoke all on function public.moreai_worker_pause_for_tool_approval(uuid,uuid,text,text,text,text,integer) from public,anon,authenticated;
grant execute on function public.moreai_worker_pause_for_tool_approval(uuid,uuid,text,text,text,text,integer) to service_role;
revoke all on function public.moreai_decide_tool_approval(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.moreai_decide_tool_approval(uuid,uuid,text) to service_role;
revoke all on function public.moreai_worker_claim_run(text,integer) from public,anon,authenticated;
grant execute on function public.moreai_worker_claim_run(text,integer) to service_role;