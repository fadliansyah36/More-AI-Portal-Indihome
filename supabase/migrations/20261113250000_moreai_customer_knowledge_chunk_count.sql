-- Exact owner-scoped chunk count for paged Knowledge Library document detail.
create or replace function public.moreai_customer_knowledge_chunk_count(
  p_user_id uuid,
  p_document_id uuid
) returns bigint
language plpgsql
stable
security invoker
set search_path = ''
as $function$
declare
  v_count bigint;
begin
  if p_user_id is null or p_document_id is null then
    raise exception 'knowledge_chunk_count_arguments_invalid' using errcode = '22023';
  end if;
  if not exists (
    select 1 from public.knowledge_documents d
    where d.id = p_document_id and d.owner_user_id = p_user_id
  ) then
    raise exception 'knowledge_document_not_found_or_not_owned' using errcode = '42501';
  end if;
  select count(*)::bigint into v_count
  from public.knowledge_chunks c
  where c.document_id = p_document_id and c.owner_user_id = p_user_id;
  return v_count;
end;
$function$;

revoke all on function public.moreai_customer_knowledge_chunk_count(uuid, uuid) from public, anon, authenticated;
grant execute on function public.moreai_customer_knowledge_chunk_count(uuid, uuid) to service_role;
