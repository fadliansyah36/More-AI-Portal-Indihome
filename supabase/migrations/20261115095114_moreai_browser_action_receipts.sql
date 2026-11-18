-- Durable, owner-scoped receipts for OpenFuse browser actions.
-- Raw URLs, query strings, browser state and secrets are intentionally not persisted.
create table if not exists public.moreai_browser_action_receipts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id uuid null references public.moreai_browser_sessions(id) on delete set null,
  action_key text not null check (action_key ~ '^[0-9a-f]{64}$'),
  request_hash text not null check (request_hash ~ '^[0-9a-f]{64}$'),
  action_type text not null check (action_type in ('navigate','extract')),
  target_host text not null check (length(target_host) between 1 and 253),
  status text not null default 'executing' check (status in ('executing','succeeded','failed','unknown')),
  result jsonb null,
  error_code text null check (error_code is null or length(error_code) <= 100),
  requested_at timestamptz not null default now(),
  finished_at timestamptz null,
  constraint moreai_browser_action_receipts_run_action_key unique (run_id, action_key)
);

create index if not exists moreai_browser_action_receipts_user_requested_idx
  on public.moreai_browser_action_receipts (user_id, requested_at desc, id desc);
create index if not exists moreai_browser_action_receipts_session_requested_idx
  on public.moreai_browser_action_receipts (session_id, requested_at desc, id desc)
  where session_id is not null;

alter table public.moreai_browser_action_receipts enable row level security;
revoke all on public.moreai_browser_action_receipts from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_browser_action_receipts to service_role;

comment on table public.moreai_browser_action_receipts is
  'Server-only idempotent OpenFuse browser action receipts. Customer reads are projected through owner-scoped FastAPI.';
