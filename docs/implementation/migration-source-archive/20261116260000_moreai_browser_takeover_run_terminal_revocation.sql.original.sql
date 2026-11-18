-- Revoke unconsumed browser takeover grants when the owning Agent Run becomes terminal.
-- Forward-only and additive; no existing session/run data is rewritten.
alter table public.moreai_browser_session_events
  drop constraint if exists moreai_browser_session_events_event_type_check;
alter table public.moreai_browser_session_events
  add constraint moreai_browser_session_events_event_type_check
  check (event_type in (
    'created','restored','state_saved','closed','expired',
    'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
    'takeover_input_succeeded','takeover_input_failed'
  ));

create or replace function public.moreai_revoke_takeover_grants_on_run_terminal()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
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
         set revoked_at = now()
       where session_id = v_session.id and user_id = v_session.user_id
         and consumed_at is null and revoked_at is null;
      get diagnostics v_count = row_count;
      if v_count > 0 then
        insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
        values (v_session.id,v_session.user_id,'takeover_grants_revoked',
          jsonb_build_object('reason','agent_run_terminal','run_id',new.id,'count',v_count));
      end if;
    end loop;
  end if;
  return new;
end;
$$;
revoke all on function public.moreai_revoke_takeover_grants_on_run_terminal() from public, anon, authenticated;
drop trigger if exists moreai_agent_run_revoke_browser_takeover_grants on public.agent_runs;
create trigger moreai_agent_run_revoke_browser_takeover_grants
after update of status on public.agent_runs
for each row execute function public.moreai_revoke_takeover_grants_on_run_terminal();
