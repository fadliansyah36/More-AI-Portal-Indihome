-- Preserve the last committed object as an immutable version when a Customer soft-deletes it.
create or replace function public.moreai_customer_workspace_delete_file(
  p_user_id uuid,
  p_workspace_id uuid,
  p_file_id uuid,
  p_expected_version bigint
) returns jsonb
language plpgsql
security invoker
set search_path = ''
as $function$
declare
  v_file public.agent_workspace_files%rowtype;
begin
  if p_user_id is null or p_workspace_id is null or p_file_id is null
     or p_expected_version is null or p_expected_version < 0 then
    raise exception 'workspace_file_delete_arguments_invalid' using errcode = '22023';
  end if;
  if not exists (
    select 1 from public.workspaces w where w.id = p_workspace_id and w.status = 'active'
      and (w.owner_user_id = p_user_id or exists (
        select 1 from public.workspace_members m where m.workspace_id = w.id
          and m.user_id = p_user_id and m.status = 'active'
      ))
  ) then raise exception 'workspace_membership_required' using errcode = '42501'; end if;

  select * into v_file from public.agent_workspace_files
    where id = p_file_id and workspace_id = p_workspace_id for update;
  if not found then raise exception 'workspace_file_not_found' using errcode = 'P0002'; end if;
  if v_file.version <> p_expected_version then raise exception 'workspace_version_conflict' using errcode = '40001'; end if;
  if v_file.pending_token is not null then raise exception 'workspace_write_in_progress' using errcode = '40001'; end if;

  if v_file.deleted_at is null then
    if v_file.version > 0 and v_file.storage_path is not null
       and v_file.sha256 is not null and v_file.size_bytes is not null then
      insert into public.agent_workspace_file_versions(
        workspace_id,user_id,path,version,storage_path,sha256,size_bytes,committed_at
      ) values (
        v_file.workspace_id,v_file.user_id,v_file.path,v_file.version,
        v_file.storage_path,v_file.sha256,v_file.size_bytes,v_file.updated_at
      ) on conflict (workspace_id,path,version) do nothing;
    end if;
    update public.agent_workspace_files set deleted_at = now(), updated_at = now()
      where id = p_file_id and workspace_id = p_workspace_id
        and version = p_expected_version and pending_token is null
      returning * into v_file;
    if not found then raise exception 'workspace_file_delete_fence_lost' using errcode = '40001'; end if;
  end if;

  return jsonb_build_object('id',v_file.id,'workspace_id',v_file.workspace_id,'path',v_file.path,
    'version',v_file.version,'deleted_at',v_file.deleted_at,'status','deleted');
end;
$function$;

revoke all on function public.moreai_customer_workspace_delete_file(uuid,uuid,uuid,bigint) from public, anon, authenticated;
grant execute on function public.moreai_customer_workspace_delete_file(uuid,uuid,uuid,bigint) to service_role;
