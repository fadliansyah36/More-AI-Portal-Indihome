create or replace function public.moreai_worker_request_cancel(p_run_id uuid,p_user_id uuid)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; seq bigint; next_status text;
begin
 select * into r from public.agent_runs where id=p_run_id and user_id=p_user_id for update;
 if not found then raise exception 'run not found'; end if;
 if r.status in('succeeded','failed','cancelled') then return jsonb_build_object('run_id',r.id,'status',r.status); end if;
 if r.status='queued' then
  next_status:='cancelled';
  update public.agent_runs set status='cancelled',cancel_requested_at=coalesce(cancel_requested_at,now()),finished_at=now(),updated_at=now() where id=r.id;
 else
  next_status:='cancel_requested';
  update public.agent_runs set cancel_requested_at=coalesce(cancel_requested_at,now()),updated_at=now() where id=r.id;
 end if;
 select coalesce(max(sequence),0)+1 into seq from public.agent_run_events where run_id=r.id;
 insert into public.agent_run_events(run_id,event_type,sequence,payload) values(r.id,'worker.cancel_requested',seq,jsonb_build_object('status',next_status));
 return jsonb_build_object('run_id',r.id,'status',next_status);
end $$;
drop function if exists public.moreai_worker_claim_run(integer);
drop function if exists public.moreai_worker_checkpoint(uuid,text,jsonb,text);
drop function if exists public.moreai_worker_finish_run(uuid,text,jsonb,jsonb,integer);
revoke all on function public.moreai_worker_request_cancel(uuid,uuid) from public,anon,authenticated;
grant execute on function public.moreai_worker_request_cancel(uuid,uuid) to service_role;