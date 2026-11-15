alter table public.moreai_browser_action_receipts
  add column if not exists result_expires_at timestamptz not null default (now() + interval '30 days');
create index if not exists moreai_browser_action_receipts_result_expiry_idx
  on public.moreai_browser_action_receipts (result_expires_at)
  where result is not null;

create or replace function public.moreai_worker_purge_expired_browser_action_receipt_results()
returns integer
language plpgsql
security definer
set search_path = pg_catalog, public
as $$
declare
  affected integer;
begin
  update public.moreai_browser_action_receipts
  set result = null
  where result is not null
    and result_expires_at <= now();
  get diagnostics affected = row_count;
  return affected;
end;
$$;

revoke all on function public.moreai_worker_purge_expired_browser_action_receipt_results() from public, anon, authenticated;
grant execute on function public.moreai_worker_purge_expired_browser_action_receipt_results() to service_role;
