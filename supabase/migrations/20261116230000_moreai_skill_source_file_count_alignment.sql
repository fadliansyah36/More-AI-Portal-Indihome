-- Align the trusted database ingestion RPC with the audited FastAPI package
-- limit. The previous RPC accepted at most 40 files while the pinned Scenario
-- source tree legitimately contains skill folders with up to 56 files.
-- Preserve every ownership, immutability, SHA, per-file byte and package byte
-- guard; this migration changes only the maximum number of file records.

create or replace function public.moreai_ingest_skill_source(
  p_skill_id uuid, p_owner_user_id uuid, p_files jsonb, p_validation_report jsonb
) returns jsonb
language plpgsql security definer set search_path=''
as $function$
declare
  v_package public.moreai_skill_packages%rowtype;
  v_count integer;
  v_bytes bigint;
begin
  if p_skill_id is null or p_owner_user_id is null
     or jsonb_typeof(p_files)<>'array' or jsonb_array_length(p_files)<1
     or jsonb_array_length(p_files)>64 or jsonb_typeof(p_validation_report)<>'object' then
    raise exception 'skill_source_ingestion_payload_invalid' using errcode='22023';
  end if;
  select * into v_package from public.moreai_skill_packages
   where id=p_skill_id and owner_user_id=p_owner_user_id for update;
  if not found then raise exception 'skill_not_found' using errcode='42501'; end if;
  if exists(select 1 from public.moreai_skill_source_files where skill_package_id=p_skill_id) then
    raise exception 'skill_source_already_ingested_immutable' using errcode='23505';
  end if;
  select count(*),coalesce(sum((x->>'byte_size')::bigint),0)
    into v_count,v_bytes from jsonb_array_elements(p_files) x;
  if v_count<>jsonb_array_length(p_files) or v_bytes>5242880 then
    raise exception 'skill_source_package_size_limit_exceeded' using errcode='22023';
  end if;
  if exists(
    select 1 from jsonb_array_elements(p_files) x
    where coalesce(x->>'relative_path','')='' or x->>'relative_path' ~ '(^/|(^|/)\.\.(/|$))'
       or coalesce(x->>'git_blob_sha','') !~ '^[0-9a-f]{40}$'
       or coalesce(x->>'content_sha256','') !~ '^[0-9a-f]{64}$'
       or coalesce((x->>'byte_size')::integer,-1)<0
       or (x->>'byte_size')::integer>524288
       or ((x->>'text_content') is null) = ((x->>'binary_content_base64') is null)
  ) then raise exception 'skill_source_file_record_invalid' using errcode='22023'; end if;
  if (select count(distinct x->>'relative_path') from jsonb_array_elements(p_files) x)<>v_count then
    raise exception 'skill_source_duplicate_path' using errcode='22023'; end if;
  insert into public.moreai_skill_source_files(
    skill_package_id,owner_user_id,relative_path,git_blob_sha,content_sha256,
    media_type,byte_size,text_content,binary_content_base64
  )
  select p_skill_id,p_owner_user_id,x->>'relative_path',x->>'git_blob_sha',x->>'content_sha256',
    x->>'media_type',(x->>'byte_size')::integer,x->>'text_content',x->>'binary_content_base64'
  from jsonb_array_elements(p_files) x;
  update public.moreai_skill_packages set
    validation_status='review_required',validation_report=p_validation_report,updated_at=now()
  where id=p_skill_id and owner_user_id=p_owner_user_id;
  insert into public.moreai_skill_registry_audit(
    skill_package_id,owner_user_id,event_type,event_detail
  ) values(
    p_skill_id,p_owner_user_id,'source_ingested',
    jsonb_build_object('file_count',v_count,'total_bytes',v_bytes,'source_commit',v_package.source_commit)
  );
  return jsonb_build_object('skill_id',p_skill_id,'file_count',v_count,'total_bytes',v_bytes,'integrity','verified');
end;
$function$;

revoke all on function public.moreai_ingest_skill_source(uuid,uuid,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.moreai_ingest_skill_source(uuid,uuid,jsonb,jsonb) to service_role;
