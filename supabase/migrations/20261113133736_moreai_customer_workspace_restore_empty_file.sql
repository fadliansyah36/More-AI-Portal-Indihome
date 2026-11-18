-- Permit valid zero-byte files produced by the OpenManus workspace runtime to be restored.
create or replace function public.moreai_customer_workspace_restore_file(
  p_user_id uuid,p_workspace_id uuid,p_file_id uuid,p_expected_version bigint,
  p_storage_path text,p_sha256 text,p_size_bytes bigint,p_bucket text
) returns jsonb language plpgsql security invoker set search_path = ''
as $function$
declare v_file public.agent_workspace_files%rowtype; v_expected_storage_path text;
begin
  if p_user_id is null or p_workspace_id is null or p_file_id is null
     or p_expected_version is null or p_expected_version < 1
     or p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$'
     or p_size_bytes is null or p_size_bytes not between 0 and 2000000
     or p_bucket is null or length(p_bucket) not between 1 and 100 then
    raise exception 'workspace_file_restore_arguments_invalid' using errcode='22023';
  end if;
  if not exists(select 1 from public.workspaces w where w.id=p_workspace_id and w.status='active'
    and (w.owner_user_id=p_user_id or exists(select 1 from public.workspace_members m
      where m.workspace_id=w.id and m.user_id=p_user_id and m.status='active'))) then
    raise exception 'workspace_membership_required' using errcode='42501';
  end if;
  select * into v_file from public.agent_workspace_files
    where id=p_file_id and workspace_id=p_workspace_id for update;
  if not found then raise exception 'workspace_file_not_found' using errcode='P0002'; end if;
  if v_file.version<>p_expected_version then raise exception 'workspace_version_conflict' using errcode='40001'; end if;
  if v_file.deleted_at is null then raise exception 'workspace_file_not_deleted' using errcode='22023'; end if;
  if v_file.pending_token is not null or v_file.storage_path is null or v_file.sha256 is null or v_file.size_bytes is null then
    raise exception 'workspace_file_not_committed_or_write_in_progress' using errcode='40001';
  end if;
  if p_sha256 is distinct from v_file.sha256 or p_size_bytes is distinct from v_file.size_bytes then
    raise exception 'workspace_restore_integrity_mismatch' using errcode='22000';
  end if;
  v_expected_storage_path:=v_file.user_id::text||'/workspaces/'||p_workspace_id::text
    ||'/versions/'||(p_expected_version+1)::text||'/'||v_file.path;
  if p_storage_path is distinct from v_expected_storage_path then
    raise exception 'workspace_restore_storage_path_invalid' using errcode='22023';
  end if;
  if not exists(select 1 from storage.buckets b where b.id=p_bucket and b.public=false)
     or not exists(select 1 from storage.objects o where o.bucket_id=p_bucket and o.name=p_storage_path) then
    raise exception 'workspace_restore_object_missing_or_bucket_not_private' using errcode='P0002';
  end if;
  update public.agent_workspace_files set deleted_at=null,version=version+1,
    storage_path=p_storage_path,sha256=p_sha256,size_bytes=p_size_bytes,updated_at=now()
    where id=p_file_id and workspace_id=p_workspace_id and version=p_expected_version
      and deleted_at is not null and pending_token is null returning * into v_file;
  if not found then raise exception 'workspace_file_restore_fence_lost' using errcode='40001'; end if;
  return jsonb_build_object('id',v_file.id,'workspace_id',v_file.workspace_id,'path',v_file.path,
    'version',v_file.version,'deleted_at',v_file.deleted_at,'status','restored',
    'storage_path',v_file.storage_path,'sha256',v_file.sha256,'size_bytes',v_file.size_bytes);
end;
$function$;
revoke all on function public.moreai_customer_workspace_restore_file(uuid,uuid,uuid,bigint,text,text,bigint,text) from public,anon,authenticated;
grant execute on function public.moreai_customer_workspace_restore_file(uuid,uuid,uuid,bigint,text,text,bigint,text) to service_role;
