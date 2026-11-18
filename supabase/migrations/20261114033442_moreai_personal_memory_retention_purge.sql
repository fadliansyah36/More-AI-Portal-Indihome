-- Periodic retention purge for Personal Memory, independent of profile visits.
create or replace function public.moreai_worker_purge_expired_customer_memories()
returns bigint
language plpgsql
security invoker
set search_path = ''
as $function$
declare v_deleted bigint;
begin
  delete from public.moreai_customer_memories
   where expires_at <= now();
  get diagnostics v_deleted = row_count;
  return v_deleted;
end;
$function$;

revoke all on function public.moreai_worker_purge_expired_customer_memories() from public, anon, authenticated;
grant execute on function public.moreai_worker_purge_expired_customer_memories() to service_role;
