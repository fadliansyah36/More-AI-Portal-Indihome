-- Atomically finalize a browser session close and append its lifecycle event.
-- Callable only by the trusted FastAPI service-role repository.
create or replace function public.moreai_complete_browser_session_close(
  p_session_id uuid, p_user_id uuid
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare v_row public.moreai_browser_sessions%rowtype;
begin
  if p_session_id is null or p_user_id is null then
    raise exception 'browser_session_close_identity_invalid' using errcode='22023';
  end if;
  select * into v_row from public.moreai_browser_sessions
  where id=p_session_id and user_id=p_user_id for update;
  if not found then
    raise exception 'browser_session_close_request_not_found' using errcode='P0002';
  end if;
  if v_row.status='closed' then
    return jsonb_build_object('session_id',p_session_id,'status','closed','replayed',true);
  end if;
  if v_row.status<>'close_requested' then
    raise exception 'browser_session_close_request_not_found' using errcode='P0002';
  end if;
  update public.moreai_browser_sessions
  set status='closed',encrypted_state=null,closed_at=now(),
      profile_retention_after=now()+interval '30 days'
  where id=p_session_id and user_id=p_user_id;
  insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
  values(p_session_id,p_user_id,'closed',jsonb_build_object('source','worker_reconciler'));
  return jsonb_build_object('session_id',p_session_id,'status','closed');
end;
$function$;
revoke all on function public.moreai_complete_browser_session_close(uuid,uuid) from public,anon,authenticated;
grant execute on function public.moreai_complete_browser_session_close(uuid,uuid) to service_role;
