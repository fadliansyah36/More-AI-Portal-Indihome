-- Keyset pagination and exact total count for the saved Customer learning progress collection.
create index if not exists customer_learning_progress_user_completed_id_idx
  on public.customer_learning_progress (user_id, completed_at desc, id desc);

create index if not exists customer_learning_progress_user_module_completed_id_idx
  on public.customer_learning_progress (user_id, module_key, completed_at desc, id desc);

create or replace function public.moreai_customer_learning_progress_count(
  p_user_id uuid,
  p_module_key text default null
) returns bigint
language sql
stable
security invoker
set search_path = ''
as $function$
  select count(*)::bigint
  from public.customer_learning_progress
  where user_id = p_user_id
    and (p_module_key is null or module_key = p_module_key);
$function$;

revoke all on function public.moreai_customer_learning_progress_count(uuid, text) from public, anon, authenticated;
grant execute on function public.moreai_customer_learning_progress_count(uuid, text) to service_role;
