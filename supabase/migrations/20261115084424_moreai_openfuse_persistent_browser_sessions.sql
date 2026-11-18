-- Persistent OpenFuse browser session metadata and encrypted Playwright state.
create table if not exists public.moreai_browser_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  last_run_id uuid references public.agent_runs(id) on delete set null,
  origin_host text not null check (origin_host ~ '^[A-Za-z0-9.-]{1,253}$'),
  status text not null default 'active' check (status in ('active','closed','expired')),
  encrypted_state text,
  created_at timestamptz not null default now(),
  last_used_at timestamptz not null default now(),
  expires_at timestamptz not null,
  closed_at timestamptz,
  constraint moreai_browser_session_expiry_valid check (expires_at > created_at)
);
create index if not exists moreai_browser_sessions_owner_active_idx
  on public.moreai_browser_sessions(user_id,last_used_at desc) where status='active';
alter table public.moreai_browser_sessions enable row level security;
revoke all on public.moreai_browser_sessions from anon, authenticated;
grant select,insert,update,delete on public.moreai_browser_sessions to service_role;

create table if not exists public.moreai_browser_session_events (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.moreai_browser_sessions(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  event_type text not null check (event_type in ('created','restored','state_saved','closed','expired')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists moreai_browser_session_events_owner_idx
  on public.moreai_browser_session_events(user_id,created_at desc);
alter table public.moreai_browser_session_events enable row level security;
revoke all on public.moreai_browser_session_events from anon, authenticated;
grant select,insert on public.moreai_browser_session_events to service_role;
