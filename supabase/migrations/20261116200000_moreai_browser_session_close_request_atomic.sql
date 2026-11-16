-- Atomically request browser-session closure and append its lifecycle event.
create or replace function public.moreai_request_browser_session_close(
  p_session_id uuid,
  p_user_id uuid,
  p_source text,
  p_reason text default null
) returns jsonb
language plpgsql
security definer
set search_path=''
as $function$
declare
  v_row public.moreai_browser_sessions%rowtype;
begin
  if p_session_id is null or p_user_id is null
     or p_source not in ('customer','ttl_reconciler','acquire_guard')
     or (p_reason is not null and p_reason not in ('ttl','idle','ttl_or_idle')) then
    raise exception 'browser_session_close_request_invalid' using errcode='22023';
  end if;

  select * into v_row
  from public.moreai_browser_sessions
  where id=p_session_id and user_id=p_user_id
  for update;

  if not found then
    raise exception 'browser_session_not_found' using errcode='P0002';
  end if;

  if v_row.status in ('close_requested','closed') then
    return jsonb_build_object(
      'session_id',p_session_id,'status',v_row.status,'replayed',true
    );
  end if;

  if v_row.status <> 'active' then
    raise exception 'browser_session_not_active' using errcode='P0002';
  end if;

  update public.moreai_browser_sessions
  set status='close_requested'
  where id=p_session_id and user_id=p_user_id;

  insert into public.moreai_browser_session_events(
    session_id,user_id,event_type,metadata
  ) values (
    p_session_id,p_user_id,'close_requested',
    jsonb_strip_nulls(jsonb_build_object('source',p_source,'reason',p_reason))
  );

  return jsonb_build_object('session_id',p_session_id,'status','close_requested');
end;
$function$;

revoke all on function public.moreai_request_browser_session_close(uuid,uuid,text,text)
  from public,anon,authenticated;
grant execute on function public.moreai_request_browser_session_close(uuid,uuid,text,text)
  to service_role;
