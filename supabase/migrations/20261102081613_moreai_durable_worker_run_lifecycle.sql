create or replace function public.moreai_worker_claim_run(p_lease_seconds integer default 90)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype;
begin
 if p_lease_seconds not between 15 and 900 then raise exception 'invalid lease duration'; end if;
 select * into r from public.agent_runs
 where status='queued' and available_at<=now() and attempt<max_attempts
 order by available_at,created_at
 for update skip locked limit 1;
 if not found then return null; end if;
 update public.agent_runs set status='running',attempt=attempt+1,started_at=coalesce(started_at,now()),updated_at=now()
 where id=r.id returning * into r;
 insert into public.agent_run_events(run_id,event_type,sequence,payload)
 select r.id,'worker.claimed',coalesce(max(sequence),0)+1,jsonb_build_object('attempt',r.attempt,'lease_seconds',p_lease_seconds)
 from public.agent_run_events where run_id=r.id;
 return jsonb_build_object('id',r.id,'user_id',r.user_id,'workspace_id',r.workspace_id,'conversation_id',r.conversation_id,'status',r.status,'attempt',r.attempt,'max_attempts',r.max_attempts,'input',r.input);
end $$;

create or replace function public.moreai_worker_checkpoint(p_run_id uuid,p_checkpoint_key text,p_state jsonb,p_event_type text default 'worker.checkpoint')
returns jsonb language plpgsql security definer set search_path='' as $$
declare seq bigint;
begin
 if not exists(select 1 from public.agent_runs where id=p_run_id and status='running') then raise exception 'run is not running'; end if;
 insert into public.agent_run_checkpoints(run_id,checkpoint_key,state)
 values(p_run_id,p_checkpoint_key,p_state)
 on conflict(run_id,checkpoint_key) do update set state=excluded.state,created_at=now();
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=p_run_id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(p_run_id,p_event_type,seq,jsonb_build_object('checkpoint_key',p_checkpoint_key));
 return jsonb_build_object('run_id',p_run_id,'checkpoint_key',p_checkpoint_key,'sequence',seq);
end $$;

create or replace function public.moreai_worker_finish_run(p_run_id uuid,p_status text,p_output jsonb default null,p_error jsonb default null,p_retry_delay_seconds integer default 30)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint; next_status text;
begin
 if p_status not in('succeeded','failed','cancelled') then raise exception 'invalid terminal status'; end if;
 select * into r from public.agent_runs where id=p_run_id for update;
 if not found then raise exception 'run not found'; end if;
 if r.status in('succeeded','failed','cancelled') then return jsonb_build_object('run_id',r.id,'status',r.status); end if;
 if p_status='failed' and r.attempt<r.max_attempts then
   next_status:='queued';
   update public.agent_runs set status=next_status,error=p_error,available_at=now()+make_interval(secs=>greatest(1,least(p_retry_delay_seconds,3600))),updated_at=now() where id=r.id;
 else
   next_status:=p_status;
   update public.agent_runs set status=next_status,output=p_output,error=p_error,finished_at=now(),updated_at=now() where id=r.id;
 end if;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload)
 values(r.id,'worker.'||next_status,seq,jsonb_build_object('attempt',r.attempt,'error',p_error));
 return jsonb_build_object('run_id',r.id,'status',next_status,'attempt',r.attempt);
end $$;

revoke all on function public.moreai_worker_claim_run(integer) from public,anon,authenticated;
revoke all on function public.moreai_worker_checkpoint(uuid,text,jsonb,text) from public,anon,authenticated;
revoke all on function public.moreai_worker_finish_run(uuid,text,jsonb,jsonb,integer) from public,anon,authenticated;
grant execute on function public.moreai_worker_claim_run(integer) to service_role;
grant execute on function public.moreai_worker_checkpoint(uuid,text,jsonb,text) to service_role;
grant execute on function public.moreai_worker_finish_run(uuid,text,jsonb,jsonb,integer) to service_role;