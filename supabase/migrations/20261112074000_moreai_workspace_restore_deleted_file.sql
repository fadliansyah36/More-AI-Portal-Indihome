-- Restore a soft-deleted workspace file as a new immutable version.
create or replace function public.moreai_workspace_get_file(
  p_user_id uuid, p_workspace_id uuid, p_path text
) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare f public.agent_workspace_files%rowtype;
begin
  if not exists (
    select 1 from public.workspaces w
    where w.id=p_workspace_id and w.status='active'
      and (w.owner_user_id=p_user_id or exists(
        select 1 from public.workspace_members m
        where m.workspace_id=w.id and m.user_id=p_user_id and m.status='active'
      ))
  ) then
    raise exception 'workspace_membership_required' using errcode='42501';
  end if;
  select * into f from public.agent_workspace_files
    where workspace_id=p_workspace_id and path=p_path;
  if not found then
    return jsonb_build_object('version',0,'storage_path',null,'sha256',null,'size_bytes',0,'deleted_at',null);
  end if;
  if f.pending_token is not null then
    raise exception 'workspace_write_in_progress' using errcode='40001';
  end if;
  return jsonb_build_object(
    'version',f.version,'storage_path',f.storage_path,'sha256',f.sha256,
    'size_bytes',f.size_bytes,'deleted_at',f.deleted_at
  );
end;
$$;

create or replace function public.moreai_workspace_restore_deleted_file(
  p_run_id uuid, p_worker_id text, p_user_id uuid, p_workspace_id uuid,
  p_path text, p_expected_version bigint
) returns jsonb
language plpgsql security invoker set search_path='' as $$
declare
  r public.agent_runs%rowtype;
  f public.agent_workspace_files%rowtype;
begin
  if p_path is null or length(p_path) not between 1 and 512
     or position(chr(92) in p_path)>0
     or p_path ~ '(^/|//|(^|/)\.\.?(/|$))'
     or p_path !~ '^[A-Za-z0-9._ -]+(/[A-Za-z0-9._ -]+)*$'
     or p_expected_version is null or p_expected_version < 1 then
    raise exception 'workspace_restore_deleted_arguments_invalid' using errcode='22023';
  end if;
  select * into r from public.agent_runs where id=p_run_id for update;
  if not found or r.user_id<>p_user_id or r.workspace_id is distinct from p_workspace_id
     or r.status<>'running' or r.lease_owner is distinct from p_worker_id
     or r.lease_expires_at is null or r.lease_expires_at<=now() then
    raise exception 'workspace_run_scope_or_lease_invalid' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.workspaces w where w.id=p_workspace_id and w.status='active'
      and (w.owner_user_id=p_user_id or exists(
        select 1 from public.workspace_members m
        where m.workspace_id=w.id and m.user_id=p_user_id and m.status='active'
      ))
  ) then
    raise exception 'workspace_membership_required' using errcode='42501';
  end if;
  select * into f from public.agent_workspace_files
    where workspace_id=p_workspace_id and path=p_path and deleted_at is not null
    for update;
  if not found then raise exception 'workspace_deleted_file_not_found' using errcode='P0002'; end if;
  if f.version<>p_expected_version then
    raise exception 'workspace_version_conflict' using errcode='40001';
  end if;
  if f.pending_token is not null or f.storage_path is null
     or f.sha256 is null or f.size_bytes is null then
    raise exception 'workspace_file_not_committed_or_write_in_progress' using errcode='40001';
  end if;
  update public.agent_workspace_files
    set deleted_at=null,version=version+1,updated_at=now()
    where id=f.id and version=p_expected_version and deleted_at is not null and pending_token is null
    returning * into f;
  if not found then raise exception 'workspace_restore_fence_lost' using errcode='40001'; end if;
  return jsonb_build_object(
    'workspace_id',p_workspace_id,'path',f.path,'version',f.version,
    'restored',true,'storage_path',f.storage_path,'sha256',f.sha256,'size_bytes',f.size_bytes
  );
end;
$$;

revoke all on function public.moreai_workspace_get_file(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.moreai_workspace_get_file(uuid,uuid,text) to service_role;
revoke all on function public.moreai_workspace_restore_deleted_file(uuid,text,uuid,uuid,text,bigint) from public,anon,authenticated;
grant execute on function public.moreai_workspace_restore_deleted_file(uuid,text,uuid,uuid,text,bigint) to service_role;
