-- Customer-authorized durable preview refresh, separate from browser.input.
-- Corrected source identity: 20261116163000 (original ID encoded hour 30).
-- A preview must remain bound to the same owner, browser session, Agent Run and PNG artifact.
alter table public.moreai_browser_session_events
  drop constraint if exists moreai_browser_session_events_event_type_check;
alter table public.moreai_browser_session_events
  add constraint moreai_browser_session_events_event_type_check
  check (event_type in (
    'created','restored','state_saved','close_requested','closed','expired',
    'profile_retention_eligible','profile_deleted',
    'takeover_grant_created','takeover_grant_consumed','takeover_grants_revoked',
    'takeover_input_succeeded','takeover_input_failed','takeover_command_queued',
    'preview_requested'
  ));

create table if not exists public.moreai_browser_preview_requests (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.moreai_browser_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  scope text not null default 'browser.preview' check (scope = 'browser.preview'),
  status text not null default 'queued' check (status in ('queued','processing','succeeded','failed','expired')),
  attempts integer not null default 0 check (attempts between 0 and 3),
  claimed_by text,
  lease_expires_at timestamptz,
  artifact_id uuid references public.artifacts(id) on delete set null,
  error_code text,
  created_at timestamptz not null default now(),
  claimed_at timestamptz,
  finished_at timestamptz,
  constraint browser_preview_terminal_state check (
    (status in ('succeeded','failed','expired') and finished_at is not null)
    or status in ('queued','processing')
  )
);
create index if not exists moreai_browser_preview_queue_idx
  on public.moreai_browser_preview_requests(status, created_at);
create index if not exists moreai_browser_preview_owner_idx
  on public.moreai_browser_preview_requests(user_id, session_id, created_at desc);
alter table public.moreai_browser_preview_requests enable row level security;
revoke all on public.moreai_browser_preview_requests from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_browser_preview_requests to service_role;
drop policy if exists moreai_browser_preview_server_only on public.moreai_browser_preview_requests;
create policy moreai_browser_preview_server_only
  on public.moreai_browser_preview_requests for all to anon, authenticated
  using (false) with check (false);

create or replace function public.moreai_claim_browser_preview_requests(
  p_worker_id text,
  p_limit integer default 5
) returns setof public.moreai_browser_preview_requests
language plpgsql
security definer
set search_path = ''
as $function$
begin
  if p_worker_id is null or p_worker_id !~ '^[A-Za-z0-9._:-]{8,128}$'
     or p_limit is null or p_limit < 1 or p_limit > 10 then
    raise exception 'browser_preview_claim_payload_invalid' using errcode = '22023';
  end if;

  update public.moreai_browser_preview_requests p
     set status = 'failed',
         error_code = 'worker_lease_expired_outcome_unknown',
         finished_at = pg_catalog.now(),
         lease_expires_at = null
   where p.status = 'processing'
     and p.lease_expires_at is not null
     and p.lease_expires_at <= pg_catalog.now();

  update public.moreai_browser_preview_requests p
     set status = 'expired',
         error_code = 'browser_session_or_run_no_longer_eligible',
         finished_at = pg_catalog.now(),
         lease_expires_at = null
   where p.status = 'queued'
     and not exists (
       select 1
         from public.moreai_browser_sessions s
         join public.agent_runs r
           on r.id = p.run_id and r.user_id = p.user_id
        where s.id = p.session_id
          and s.user_id = p.user_id
          and (s.run_id = p.run_id or s.last_run_id = p.run_id)
          and s.status = 'active'
          and s.expires_at > pg_catalog.now()
          and r.status in ('running','succeeded')
     );

  return query
  with candidates as (
    select p.id
      from public.moreai_browser_preview_requests p
      join public.moreai_browser_sessions s
        on s.id = p.session_id and s.user_id = p.user_id
      join public.agent_runs r
        on r.id = p.run_id and r.user_id = p.user_id
     where p.status = 'queued'
       and p.attempts < 3
       and (s.run_id = p.run_id or s.last_run_id = p.run_id)
       and s.status = 'active'
       and s.expires_at > pg_catalog.now()
       and r.status in ('running','succeeded')
     order by p.created_at, p.id
     for update of p skip locked
     limit p_limit
  )
  update public.moreai_browser_preview_requests p
     set status = 'processing',
         claimed_by = p_worker_id,
         lease_expires_at = pg_catalog.now() + interval '60 seconds',
         claimed_at = pg_catalog.now(),
         attempts = p.attempts + 1
    from candidates
   where p.id = candidates.id
  returning p.*;
end;
$function$;
revoke all on function public.moreai_claim_browser_preview_requests(text,integer) from public, anon, authenticated;
grant execute on function public.moreai_claim_browser_preview_requests(text,integer) to service_role;

create or replace function public.moreai_finish_browser_preview_request(
  p_request_id uuid,
  p_worker_id text,
  p_status text,
  p_artifact_id uuid default null,
  p_error_code text default null
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_row public.moreai_browser_preview_requests%rowtype;
begin
  if p_request_id is null
     or p_worker_id is null
     or p_worker_id !~ '^[A-Za-z0-9._:-]{8,128}$'
     or p_status not in ('succeeded','failed')
     or (p_status = 'succeeded' and p_artifact_id is null) then
    raise exception 'browser_preview_finish_payload_invalid' using errcode = '22023';
  end if;

  update public.moreai_browser_preview_requests p
     set status = p_status,
         artifact_id = case when p_status = 'succeeded' then p_artifact_id else null end,
         error_code = case when p_status = 'failed'
                           then left(coalesce(p_error_code, 'browser_preview_failed'), 100) else null end,
         finished_at = pg_catalog.now(),
         lease_expires_at = null
   where p.id = p_request_id
     and p.status = 'processing'
     and p.claimed_by = p_worker_id
     and p.lease_expires_at > pg_catalog.now()
     and exists (
       select 1
         from public.moreai_browser_sessions s
        where s.id = p.session_id
          and s.user_id = p.user_id
          and (s.run_id = p.run_id or s.last_run_id = p.run_id)
          and s.status = 'active'
          and s.expires_at > pg_catalog.now()
     )
     and (
       p_status = 'failed'
       or exists (
         select 1
           from public.artifacts a
          where a.id = p_artifact_id
            and a.user_id = p.user_id
            and a.run_id = p.run_id
            and a.mime_type = 'image/png'
       )
     )
  returning p.* into v_row;

  if not found then
    raise exception 'browser_preview_worker_lease_or_artifact_invalid' using errcode = '40001';
  end if;

  return pg_catalog.jsonb_build_object(
    'id', v_row.id, 'status', v_row.status, 'artifact_id', v_row.artifact_id
  );
end;
$function$;
revoke all on function public.moreai_finish_browser_preview_request(uuid,text,text,uuid,text) from public, anon, authenticated;
grant execute on function public.moreai_finish_browser_preview_request(uuid,text,text,uuid,text) to service_role;
