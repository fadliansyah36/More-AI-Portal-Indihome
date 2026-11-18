create table if not exists public.moreai_computer_action_receipts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  action_key text not null check (action_key ~ '^[0-9a-f]{64}$'),
  request_hash text not null check (request_hash ~ '^[0-9a-f]{64}$'),
  action_type text not null check (action_type in ('bash','python')),
  status text not null default 'executing' check (status in ('executing','succeeded','failed','unknown')),
  result jsonb null,
  error_code text null check (error_code is null or length(error_code) <= 100),
  requested_at timestamptz not null default now(),
  finished_at timestamptz null,
  result_expires_at timestamptz not null default (now() + interval '30 days'),
  constraint moreai_computer_action_receipts_run_action_key unique (run_id, action_key)
);
create index if not exists moreai_computer_action_receipts_user_requested_idx
  on public.moreai_computer_action_receipts (user_id, requested_at desc, id desc);
create index if not exists moreai_computer_action_receipts_result_expiry_idx
  on public.moreai_computer_action_receipts (result_expires_at)
  where result is not null;
alter table public.moreai_computer_action_receipts enable row level security;
revoke all on public.moreai_computer_action_receipts from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_computer_action_receipts to service_role;

create or replace function public.moreai_worker_purge_expired_computer_action_receipt_results()
returns integer
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare affected integer;
begin
  update public.moreai_computer_action_receipts set result = null
  where result is not null and result_expires_at <= now();
  get diagnostics affected = row_count;
  return affected;
end;
$$;
revoke all on function public.moreai_worker_purge_expired_computer_action_receipt_results() from public, anon, authenticated;
grant execute on function public.moreai_worker_purge_expired_computer_action_receipt_results() to service_role;
