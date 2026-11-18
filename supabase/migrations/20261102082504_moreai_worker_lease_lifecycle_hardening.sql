alter table public.agent_runs add column if not exists lease_owner text, add column if not exists lease_expires_at timestamptz, add column if not exists heartbeat_at timestamptz, add column if not exists cancel_requested_at timestamptz, add column if not exists dead_lettered_at timestamptz, add column if not exists last_checkpoint_key text;
create index if not exists agent_runs_lease_expiry_idx on public.agent_runs(lease_expires_at) where status='running';
create or replace function public.moreai_worker_claim_run(p_worker_id text,p_lease_seconds integer default 90) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint; d record;
begin
 if p_worker_id is null or length(p_worker_id)<8 or length(p_worker_id)>128 or p_lease_seconds not between 15 and 900 then raise exception 'invalid worker claim'; end if;
 for d in update public.agent_runs set status='failed',finished_at=now(),dead_lettered_at=now(),lease_owner=null,lease_expires_at=null,updated_at=now()
 where status='running' and lease_expires_at<now() and attempt>=max_attempts returning id loop
  select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=d.id;
  insert into public.agent_run_events(run_id,event_type,sequence,payload) values(d.id,'worker.dead_lettered',seq,'{"reason":"lease_expired_max_attempts"}'::jsonb);
 end loop;
 select * into r from public.agent_runs where ((status='queued' and available_at<=now()) or (status='running' and lease_expires_at<now())) and attempt<max_attempts and cancel_requested_at is null order by available_at,created_at for update skip locked limit 1;
 if not found then return null; end if;
 update public.agent_runs set status='running',attempt=attempt+1,lease_owner=p_worker_id,lease_expires_at=now()+make_interval(secs=>p_lease_seconds),heartbeat_at=now(),started_at=coalesce(started_at,now()),updated_at=now() where id=r.id returning * into r;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(r.id,'worker.claimed',seq,jsonb_build_object('worker_id',p_worker_id,'attempt',r.attempt,'lease_seconds',p_lease_seconds));
 return jsonb_build_object('id',r.id,'user_id',r.user_id,'workspace_id',r.workspace_id,'conversation_id',r.conversation_id,'agent_definition_id',r.agent_definition_id,'status',r.status,'attempt',r.attempt,'max_attempts',r.max_attempts,'input',r.input,'lease_owner',r.lease_owner,'lease_expires_at',r.lease_expires_at);
end $$;
create or replace function public.moreai_worker_heartbeat(p_run_id uuid,p_worker_id text,p_lease_seconds integer default 90) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype;
begin
 if p_lease_seconds not between 15 and 900 then raise exception 'invalid lease duration'; end if;
 update public.agent_runs set heartbeat_at=now(),lease_expires_at=now()+make_interval(secs=>p_lease_seconds),updated_at=now() where id=p_run_id and status='running' and lease_owner=p_worker_id and cancel_requested_at is null returning * into r;
 if not found then return jsonb_build_object('alive',false,'cancel_requested',exists(select 1 from public.agent_runs where id=p_run_id and cancel_requested_at is not null)); end if;
 return jsonb_build_object('alive',true,'lease_expires_at',r.lease_expires_at);
end $$;
create or replace function public.moreai_worker_request_cancel(p_run_id uuid,p_user_id uuid) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint;
begin
 select * into r from public.agent_runs where id=p_run_id and user_id=p_user_id for update;
 if not found then raise exception 'run not found'; end if;
 if r.status in('succeeded','failed','cancelled') then return jsonb_build_object('run_id',r.id,'status',r.status); end if;
 update public.agent_runs set cancel_requested_at=coalesce(cancel_requested_at,now()),updated_at=now() where id=r.id;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(r.id,'worker.cancel_requested',seq,'{}'::jsonb);
 return jsonb_build_object('run_id',r.id,'status','cancel_requested');
end $$;
create or replace function public.moreai_worker_resume_run(p_run_id uuid,p_user_id uuid) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint;
begin
 select * into r from public.agent_runs where id=p_run_id and user_id=p_user_id for update;
 if not found then raise exception 'run not found'; end if;
 if r.status not in('failed','cancelled','expired') then raise exception 'run cannot be resumed'; end if;
 update public.agent_runs set status='queued',attempt=0,available_at=now(),finished_at=null,dead_lettered_at=null,cancel_requested_at=null,lease_owner=null,lease_expires_at=null,error=null,updated_at=now() where id=r.id returning * into r;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(r.id,'worker.resumed',seq,'{}'::jsonb);
 return jsonb_build_object('run_id',r.id,'status',r.status);
end $$;
create or replace function public.moreai_worker_checkpoint(p_run_id uuid,p_worker_id text,p_checkpoint_key text,p_state jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare seq bigint;
begin
 if not exists(select 1 from public.agent_runs where id=p_run_id and status='running' and lease_owner=p_worker_id and lease_expires_at>now()) then raise exception 'worker lease not held'; end if;
 insert into public.agent_run_checkpoints(run_id,checkpoint_key,state) values(p_run_id,p_checkpoint_key,p_state) on conflict(run_id,checkpoint_key) do update set state=excluded.state,created_at=now();
 update public.agent_runs set last_checkpoint_key=p_checkpoint_key,updated_at=now() where id=p_run_id;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=p_run_id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(p_run_id,'worker.checkpoint',seq,jsonb_build_object('checkpoint_key',p_checkpoint_key));
 return jsonb_build_object('run_id',p_run_id,'checkpoint_key',p_checkpoint_key,'sequence',seq);
end $$;
create or replace function public.moreai_worker_finish_run(p_run_id uuid,p_worker_id text,p_status text,p_output jsonb default null,p_error jsonb default null,p_retry_delay_seconds integer default 30) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint; next_status text; dead boolean:=false;
begin
 if p_status not in('succeeded','failed','cancelled') then raise exception 'invalid terminal status'; end if;
 select * into r from public.agent_runs where id=p_run_id for update;
 if not found then raise exception 'run not found'; end if;
 if r.status in('succeeded','failed','cancelled') then return jsonb_build_object('run_id',r.id,'status',r.status); end if;
 if r.lease_owner is distinct from p_worker_id then raise exception 'worker lease mismatch'; end if;
 if r.cancel_requested_at is not null then next_status:='cancelled'; elsif p_status='failed' and r.attempt<r.max_attempts then next_status:='queued'; elsif p_status='failed' then next_status:='failed'; dead:=true; else next_status:=p_status; end if;
 if next_status='queued' then update public.agent_runs set status=next_status,error=p_error,available_at=now()+make_interval(secs=>greatest(1,least(p_retry_delay_seconds,3600))),lease_owner=null,lease_expires_at=null,heartbeat_at=null,updated_at=now() where id=r.id;
 else update public.agent_runs set status=next_status,output=p_output,error=p_error,finished_at=now(),dead_lettered_at=case when dead then now() else dead_lettered_at end,lease_owner=null,lease_expires_at=null,heartbeat_at=null,updated_at=now() where id=r.id; end if;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(r.id,case when dead then 'worker.dead_lettered' else 'worker.'||next_status end,seq,jsonb_build_object('attempt',r.attempt,'error',p_error));
 return jsonb_build_object('run_id',r.id,'status',next_status,'attempt',r.attempt,'dead_lettered',dead);
end $$;
revoke all on function public.moreai_worker_claim_run(text,integer) from public,anon,authenticated;
revoke all on function public.moreai_worker_heartbeat(uuid,text,integer) from public,anon,authenticated;
revoke all on function public.moreai_worker_request_cancel(uuid,uuid) from public,anon,authenticated;
revoke all on function public.moreai_worker_resume_run(uuid,uuid) from public,anon,authenticated;
revoke all on function public.moreai_worker_checkpoint(uuid,text,text,jsonb) from public,anon,authenticated;
revoke all on function public.moreai_worker_finish_run(uuid,text,text,jsonb,jsonb,integer) from public,anon,authenticated;
grant execute on function public.moreai_worker_claim_run(text,integer) to service_role;
grant execute on function public.moreai_worker_heartbeat(uuid,text,integer) to service_role;
grant execute on function public.moreai_worker_request_cancel(uuid,uuid) to service_role;
grant execute on function public.moreai_worker_resume_run(uuid,uuid) to service_role;
grant execute on function public.moreai_worker_checkpoint(uuid,text,text,jsonb) to service_role;
grant execute on function public.moreai_worker_finish_run(uuid,text,text,jsonb,jsonb,integer) to service_role;