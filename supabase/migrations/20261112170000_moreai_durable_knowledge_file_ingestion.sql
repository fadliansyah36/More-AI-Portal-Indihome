-- Durable private file ingestion for tenant-scoped Knowledge Library.
-- Forward-only: preserves existing document/chunk rows and never exposes Storage to clients.
alter table public.knowledge_documents
  add column if not exists ingestion_attempt integer not null default 0,
  add column if not exists ingestion_lease_until timestamptz,
  add column if not exists ingestion_error_code text,
  add column if not exists page_count integer;

create index if not exists knowledge_documents_ingestion_claim_idx
  on public.knowledge_documents(status, ingestion_lease_until, created_at)
  where source_type = 'file' and status = 'processing';

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'moreai-knowledge-private',
  'moreai-knowledge-private',
  false,
  26214400,
  array['application/pdf','image/jpeg','image/png','image/webp']
)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists moreai_knowledge_storage_server_only on storage.objects;
create policy moreai_knowledge_storage_server_only
  on storage.objects for all to anon, authenticated
  using (bucket_id = 'moreai-knowledge-private' and false)
  with check (bucket_id = 'moreai-knowledge-private' and false);

create or replace function public.moreai_worker_claim_knowledge_ingestion(
  p_lease_seconds integer default 180
)
returns setof public.knowledge_documents
language plpgsql
security invoker
set search_path = ''
as $$
begin
  return query
  with candidate as (
    select d.id
    from public.knowledge_documents d
    where d.source_type = 'file'
      and d.status = 'processing'
      and coalesce(d.metadata->>'ingestion_state','') in ('queued','processing')
      and (nullif(d.metadata->>'retry_after','') is null or (d.metadata->>'retry_after')::timestamptz <= now())
      and (d.ingestion_lease_until is null or d.ingestion_lease_until < now())
    order by d.created_at asc
    for update skip locked
    limit 1
  )
  update public.knowledge_documents d
  set ingestion_attempt = d.ingestion_attempt + 1,
      ingestion_lease_until = now() + make_interval(secs => greatest(30, least(coalesce(p_lease_seconds,180), 900))),
      metadata = jsonb_set(
        jsonb_set(coalesce(d.metadata,'{}'::jsonb), '{ingestion_state}', '"processing"'::jsonb, true),
        '{last_attempt_at}', to_jsonb(now()), true
      ),
      updated_at = now()
  from candidate c
  where d.id = c.id
  returning d.*;
end;
$$;

create or replace function public.moreai_worker_finish_knowledge_ingestion(
  p_document_id uuid,
  p_owner_user_id uuid,
  p_success boolean,
  p_error_code text default null,
  p_page_count integer default null
)
returns boolean
language plpgsql
security invoker
set search_path = ''
as $$
begin
  update public.knowledge_documents
  set status = case when p_success then 'ready' when ingestion_attempt >= 3 then 'failed' else 'processing' end,
      ingestion_error_code = case when p_success then null else left(coalesce(p_error_code,'ingestion_failed'),80) end,
      ingestion_lease_until = null,
      page_count = case when p_success then greatest(coalesce(p_page_count,0),0) else page_count end,
      metadata = jsonb_set(
        jsonb_set(coalesce(metadata,'{}'::jsonb), '{ingestion_state}', to_jsonb(case when p_success then 'ready' when ingestion_attempt >= 3 then 'failed' else 'queued' end), true),
        '{processed_at}', to_jsonb(now()), true
      ) || case when not p_success and ingestion_attempt < 3 then
        jsonb_build_object('retry_after', to_jsonb(now() + make_interval(secs => least(300, 15 * power(2, ingestion_attempt))))) 
      else '{}'::jsonb end,
      updated_at = now()
  where id = p_document_id
    and owner_user_id = p_owner_user_id
    and source_type = 'file'
    and status = 'processing'
    and ingestion_lease_until > now();
  return found;
end;
$$;

revoke all on function public.moreai_worker_claim_knowledge_ingestion(integer) from public, anon, authenticated;
revoke all on function public.moreai_worker_finish_knowledge_ingestion(uuid,uuid,boolean,text,integer) from public, anon, authenticated;
grant execute on function public.moreai_worker_claim_knowledge_ingestion(integer) to service_role;
grant execute on function public.moreai_worker_finish_knowledge_ingestion(uuid,uuid,boolean,text,integer) to service_role;
