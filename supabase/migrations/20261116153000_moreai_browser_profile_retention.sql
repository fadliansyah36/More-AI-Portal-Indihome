-- Retain closed browser profiles for 30 days, then delete the OpenFuse profile through the worker.
alter table public.moreai_browser_sessions
  add column if not exists profile_retention_after timestamptz,
  add column if not exists profile_deleted_at timestamptz;

update public.moreai_browser_sessions
set profile_retention_after = coalesce(closed_at, expires_at) + interval '30 days'
where status in ('closed','expired')
  and profile_retention_after is null;

alter table public.moreai_browser_session_events
  drop constraint if exists moreai_browser_session_events_event_type_check;

alter table public.moreai_browser_session_events
  add constraint moreai_browser_session_events_event_type_check
  check (event_type in (
    'created',
    'restored',
    'state_saved',
    'close_requested',
    'closed',
    'expired',
    'profile_retention_eligible',
    'profile_deleted'
  ));

create index if not exists moreai_browser_sessions_profile_retention_idx
  on public.moreai_browser_sessions(profile_retention_after, id)
  where profile_deleted_at is null and status in ('closed','expired');

comment on column public.moreai_browser_sessions.profile_retention_after is
  'OpenFuse profile becomes eligible for deletion after this timestamp; default policy is 30 days after session closure.';
comment on column public.moreai_browser_sessions.profile_deleted_at is
  'Timestamp acknowledged by the trusted worker after OpenFuse profile deletion or confirmed absence.';
