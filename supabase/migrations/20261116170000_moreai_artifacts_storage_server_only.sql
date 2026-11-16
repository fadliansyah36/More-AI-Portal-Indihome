-- Keep customer artifact objects accessible only through the trusted FastAPI service.
-- Supabase Storage grants CRUD to client roles globally; this bucket-specific RLS
-- denial makes the intended server-only boundary explicit without changing other buckets.
do $$
begin
  if not exists (
    select 1 from storage.buckets
    where id = 'moreai-artifacts' and public = false
  ) then
    raise exception 'moreai_artifacts_bucket_missing_or_public';
  end if;
end
$$;

drop policy if exists moreai_artifacts_storage_server_only on storage.objects;
create policy moreai_artifacts_storage_server_only
  on storage.objects
  for all
  to anon, authenticated
  using (bucket_id = 'moreai-artifacts' and false)
  with check (bucket_id = 'moreai-artifacts' and false);

comment on policy moreai_artifacts_storage_server_only on storage.objects is
  'Deny direct anon/authenticated client access; customer artifact access is mediated by FastAPI using server-only credentials.';
