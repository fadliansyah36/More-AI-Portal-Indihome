create or replace function public.moreai_worker_retry_event_outbox(
  p_event_id uuid, p_worker_id text, p_error_code text
) returns text
language plpgsql security definer set search_path='' as $$
declare v_state text;
begin
  update public.outbox_events
    set attempts=attempts+1,
        status=case when attempts+1 >= 12 then 'dead_letter' else 'failed' end,
        available_at=now()+make_interval(secs=>least(3600,power(2,least(attempts,10))::integer)),
        worker_id=null,lease_expires_at=null,last_error=left(coalesce(p_error_code,'publish_failed'),200)
    where id=p_event_id and status='processing' and worker_id=p_worker_id
      and lease_expires_at > now();
  if not found then raise exception 'outbox_lease_lost' using errcode='40001'; end if;
  return (select status from public.outbox_events where id=p_event_id);
end;
$$;
revoke all on function public.moreai_worker_retry_event_outbox(uuid,text,text) from public,anon,authenticated;
grant execute on function public.moreai_worker_retry_event_outbox(uuid,text,text) to service_role;
