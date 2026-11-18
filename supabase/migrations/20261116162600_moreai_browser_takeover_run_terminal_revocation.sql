-- Revoke unconsumed browser takeover grants when the owning Agent Run becomes terminal.
-- Corrected source identity: 20261116162600 (original ID encoded hour 26).
alter table public.moreai_browser_session_events
  drop constraint if exists moreai_browser_session_events_event_type_check;
alter table public.moreai_browser_session_events
  add constraint moreai_browser_session_events_event_type_check
  check (event_type in (
    'created','restored','state_saved','close_requested','closed','expired',
    'profile_retention_eligible','profile_deleted',
    'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
    'takeover_input_succeeded','takeover_input_failed'
  ));

create or replace function public.moreai_revoke_takeover_grants_on_run_terminal()
returns trigger
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_session record;
  v_count integer;
begin
  if new.status in ('succeeded','failed','cancelled','timed_out','expired')
     and old.status is distinct from new.status then
    for v_session in
      select s.id, s.user_id
        from public.moreai_browser_sessions s
       where s.user_id = new.user_id
         and (s.run_id = new.id or s.last_run_id = new.id)
    loop
      update public.moreai_browser_takeover_grants
         set revoked_at = pg_catalog.now()
       where session_id = v_session.id and user_id = v_session.user_id
         and consumed_at is null and revoked_at is null;
      get diagnostics v_count = row_count;
      if v_count > 0 then
        insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
        values (v_session.id,v_session.user_id,'takeover_grants_revoked',
          pg_catalog.jsonb_build_object('reason','agent_run_terminal','run_id',new.id,'count',v_count));
      end if;
    end loop;
  end if;
  return new;
end;
$function$;
revoke all on function public.moreai_revoke_takeover_grants_on_run_terminal() from public, anon, authenticated;
drop trigger if exists moreai_agent_run_revoke_browser_takeover_grants on public.agent_runs;
create trigger moreai_agent_run_revoke_browser_takeover_grants
after update of status on public.agent_runs
for each row execute function public.moreai_revoke_takeover_grants_on_run_terminal();
