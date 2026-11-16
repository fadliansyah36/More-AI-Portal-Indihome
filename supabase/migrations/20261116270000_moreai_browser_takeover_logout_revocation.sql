-- Logout revocation RPC. Revokes every still-unconsumed grant owned by the authenticated
-- customer and records one audit event per affected browser session.
create or replace function public.moreai_revoke_user_browser_takeover_grants(p_user_id uuid)
returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_session record;
  v_total integer := 0;
  v_count integer;
begin
  if p_user_id is null then
    raise exception 'user_id_required';
  end if;
  for v_session in
    select distinct g.session_id
      from public.moreai_browser_takeover_grants g
     where g.user_id = p_user_id
       and g.consumed_at is null and g.revoked_at is null
  loop
    update public.moreai_browser_takeover_grants
       set revoked_at = now()
     where session_id = v_session.session_id and user_id = p_user_id
       and consumed_at is null and revoked_at is null;
    get diagnostics v_count = row_count;
    v_total := v_total + v_count;
    if v_count > 0 then
      insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
      values (v_session.session_id,p_user_id,'takeover_grants_revoked',
        jsonb_build_object('reason','customer_logout','count',v_count));
    end if;
  end loop;
  return v_total;
end;
$$;
revoke all on function public.moreai_revoke_user_browser_takeover_grants(uuid) from public, anon, authenticated;
grant execute on function public.moreai_revoke_user_browser_takeover_grants(uuid) to service_role;
