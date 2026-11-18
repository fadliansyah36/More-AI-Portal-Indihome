-- One-time, short-lived customer consent for human browser takeover.
-- Recovered source identity: 20261116250000 (invalid hour component).
-- Corrected source identity: 20261116162500.
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

create table if not exists public.moreai_browser_takeover_grants (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.moreai_browser_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  token_sha256 text not null unique check (token_sha256 ~ '^[0-9a-f]{64}$'),
  scopes text[] not null default array['browser.input']::text[]
    check (scopes <@ array['browser.input']::text[] and cardinality(scopes) > 0),
  expires_at timestamptz not null,
  consumed_at timestamptz,
  revoked_at timestamptz,
  consumed_by_worker text,
  created_at timestamptz not null default now(),
  constraint takeover_expiry_bounded
    check (expires_at > created_at and expires_at <= created_at + interval '3 minutes')
);
create index if not exists moreai_browser_takeover_grants_owner_idx
  on public.moreai_browser_takeover_grants(user_id, created_at desc);
alter table public.moreai_browser_takeover_grants enable row level security;
revoke all on public.moreai_browser_takeover_grants from anon, authenticated;
grant select, insert, update, delete on public.moreai_browser_takeover_grants to service_role;

create or replace function public.moreai_consume_browser_takeover_grant(
  p_token_sha256 text,
  p_worker_id text
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_grant public.moreai_browser_takeover_grants%rowtype;
begin
  if p_token_sha256 is null or p_token_sha256 !~ '^[0-9a-f]{64}$'
     or p_worker_id is null or p_worker_id !~ '^[A-Za-z0-9._:-]{8,128}$' then
    return jsonb_build_object('status', 'invalid');
  end if;

  update public.moreai_browser_takeover_grants g
     set consumed_at = pg_catalog.now(), consumed_by_worker = p_worker_id
   where g.token_sha256 = p_token_sha256
     and g.consumed_at is null and g.revoked_at is null
     and g.expires_at > pg_catalog.now()
     and exists (
       select 1 from public.moreai_browser_sessions s
        where s.id = g.session_id and s.user_id = g.user_id
          and s.status = 'active' and s.expires_at > pg_catalog.now()
     )
  returning g.* into v_grant;

  if not found then
    return jsonb_build_object('status', 'unavailable');
  end if;

  insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
  values (v_grant.session_id,v_grant.user_id,'takeover_grant_consumed',
    pg_catalog.jsonb_build_object('grant_id',v_grant.id,'worker_id',p_worker_id,'scopes',v_grant.scopes));

  return pg_catalog.jsonb_build_object(
    'status','consumed','grant_id',v_grant.id,'session_id',v_grant.session_id,
    'user_id',v_grant.user_id,'scopes',v_grant.scopes,'expires_at',v_grant.expires_at
  );
end;
$function$;
revoke all on function public.moreai_consume_browser_takeover_grant(text,text) from public, anon, authenticated;
grant execute on function public.moreai_consume_browser_takeover_grant(text,text) to service_role;

create or replace function public.moreai_revoke_browser_takeover_grants(
  p_session_id uuid,
  p_user_id uuid
) returns integer
language plpgsql
security definer
set search_path = ''
as $function$
declare v_count integer;
begin
  update public.moreai_browser_takeover_grants
     set revoked_at = pg_catalog.now()
   where session_id = p_session_id and user_id = p_user_id
     and consumed_at is null and revoked_at is null;
  get diagnostics v_count = row_count;
  insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
  values (p_session_id,p_user_id,'takeover_grants_revoked',pg_catalog.jsonb_build_object('count',v_count));
  return v_count;
end;
$function$;
revoke all on function public.moreai_revoke_browser_takeover_grants(uuid,uuid) from public, anon, authenticated;
grant execute on function public.moreai_revoke_browser_takeover_grants(uuid,uuid) to service_role;

create or replace function public.moreai_revoke_takeover_grants_on_session_close()
returns trigger
language plpgsql
security definer
set search_path = ''
as $function$
declare v_count integer;
begin
  if old.status = 'active' and new.status <> 'active' then
    update public.moreai_browser_takeover_grants
       set revoked_at = pg_catalog.now()
     where session_id = new.id and user_id = new.user_id
       and consumed_at is null and revoked_at is null;
    get diagnostics v_count = row_count;
    if v_count > 0 then
      insert into public.moreai_browser_session_events(session_id,user_id,event_type,metadata)
      values (new.id,new.user_id,'takeover_grants_revoked',
        pg_catalog.jsonb_build_object('reason','session_status_changed','count',v_count));
    end if;
  end if;
  return new;
end;
$function$;
revoke all on function public.moreai_revoke_takeover_grants_on_session_close() from public, anon, authenticated;
drop trigger if exists moreai_browser_session_revoke_takeover_grants on public.moreai_browser_sessions;
create trigger moreai_browser_session_revoke_takeover_grants
after update of status on public.moreai_browser_sessions
for each row execute function public.moreai_revoke_takeover_grants_on_session_close();
