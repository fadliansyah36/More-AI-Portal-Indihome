do $$
begin
  if not exists (
    select 1 from storage.buckets where id = 'moreai-artifacts'
  ) then
    raise exception 'required_private_artifact_bucket_missing';
  end if;
  update storage.buckets
     set public = false,
         file_size_limit = 150000000
   where id = 'moreai-artifacts';
end
$$;