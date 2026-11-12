-- Lease-fenced soft-delete and rename for immutable workspace files.
-- Objects remain private in Storage; metadata history is retained for audit/recovery.
alter table public.agent_workspace_files
  add column if not exists deleted_at timestamptz;

create index if not exists agent_workspace_files_active_workspace_updated_idx
  on public.agent_workspace_files (workspace_id, updated_at desc)
  where deleted_at is null;

create or replace function public.moreai_workspace_delete_file(
  p_run_id uuid, p_worker_id text, p_user_id uuid, p_workspace_id uuid,
  p_path text, p_expected_version bigint
) returns jsonb
language plpgsql security invoker set search_path='' as $
declare
  r public.agent_runs%rowtype;
  f public.agent_workspace_files%rowtype;
begin
  if p_path is null or length(p_path) not between 1 and 512
     or position(chr(92) in p_path)>0
     or p_path ~ '(^/|//|(^|/)\.\.?(/|$))'
     or p_path !~ '^[A-Za-z0-9._ -]+(/[A-Za-z0-9._ -]+)*$'
     or p_expected_version is null or p_expected_version < 1 then
    raise exception 'workspace_delete_arguments_invalid' using errcode='22023';
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
    where workspace_id=p_workspace_id and path=p_path and deleted_at is null
    for update;
  if not found then raise exception 'workspace_file_not_found' using errcode='P0002'; end if;
  if f.version<>p_expected_version then
    raise exception 'workspace_version_conflict' using errcode='40001';
  end if;
  if f.pending_token is not null then
    raise exception 'workspace_write_in_progress' using errcode='40001';
  end if;
  if f.storage_path is null or f.sha256 is null or f.size_bytes is null then
    raise exception 'workspace_file_not_committed' using errcode='40001';
  end if;
  insert into public.agent_workspace_file_versions(
    workspace_id,user_id,path,version,storage_path,sha256,size_bytes,committed_at
  ) values (
    f.workspace_id,f.user_id,f.path,f.version,f.storage_path,f.sha256,f.size_bytes,f.updated_at
  ) on conflict(workspace_id,path,version) do nothing;
  update public.agent_workspace_files
    set deleted_at=now(),updated_at=now()
    where id=f.id and version=p_expected_version and pending_token is null
    returning * into f;
  if not found then raise exception 'workspace_delete_fence_lost' using errcode='40001'; end if;
  return jsonb_build_object(
    'workspace_id',p_workspace_id,'path',p_path,'version',f.version,
    'deleted',true,'deleted_at',f.deleted_at
  );
end;
$$;

create or replace function public.moreai_workspace_rename_file(
  p_run_id uuid, p_worker_id text, p_user_id uuid, p_workspace_id uuid,
  p_path text, p_new_path text, p_expected_version bigint
) returns jsonb
language plpgsql security invoker set search_path='' as $
declare
  r public.agent_runs%rowtype;
  f public.agent_workspace_files%rowtype;
begin
  if p_path is null or p_new_path is null
     or length(p_path) not between 1 and 512
     or length(p_new_path) not between 1 and 512
     or p_path=p_new_path
     or position(chr(92) in p_path)>0
     or p_path ~ '(^/|//|(^|/)\.\.?(/|$))'
     or position(chr(92) in p_new_path)>0
     or p_new_path ~ '(^/|//|(^|/)\.\.?(/|$))'
     or p_path !~ '^[A-Za-z0-9._ -]+(/[A-Za-z0-9._ -]+)*$'
     or p_new_path !~ '^[A-Za-z0-9._ -]+(/[A-Za-z0-9._ -]+)*$'
     or p_expected_version < 1 then
    raise exception 'workspace_rename_arguments_invalid' using errcode='22023';
  end if;
  select * into r from public.agent_runs where id=p_run_id for update;
  if not found or r.user_id<>p_user_id or r.workspace_id is distinct from p_workspace_id
     or r.status<>'running' or r.lease_owner is distinct from p_worker_id
     or r.lease_expires_at<=now() then
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
    where workspace_id=p_workspace_id and path=p_path and deleted_at is null
    for update;
  if not found then raise exception 'workspace_file_not_found' using errcode='P0002'; end if;
  if f.version<>p_expected_version then
    raise exception 'workspace_version_conflict' using errcode='40001';
  end if;
  if f.pending_token is not null or f.storage_path is null
     or f.sha256 is null or f.size_bytes is null then
    raise exception 'workspace_file_not_committed_or_write_in_progress' using errcode='40001';
  end if;
  if exists(select 1 from public.agent_workspace_files
      where workspace_id=p_workspace_id and path=p_new_path) then
    raise exception 'workspace_rename_target_exists' using errcode='23505';
  end if;
  update public.agent_workspace_files
    set path=p_new_path,version=version+1,updated_at=now()
    where id=f.id and version=p_expected_version and pending_token is null
    returning * into f;
  if not found then raise exception 'workspace_rename_fence_lost' using errcode='40001'; end if;
  -- The existing version-history trigger snapshots the previous path/version/object
  -- in the same transaction before this metadata rename is committed.
  return jsonb_build_object(
    'workspace_id',p_workspace_id,'old_path',p_path,'path',f.path,
    'version',f.version,'sha256',f.sha256,'size_bytes',f.size_bytes,
    'storage_path',f.storage_path,'renamed',true
  );
end;
$$;

revoke all on function public.moreai_workspace_delete_file(uuid,text,uuid,uuid,text,bigint) from public,anon,authenticated;
revoke all on function public.moreai_workspace_rename_file(uuid,text,uuid,uuid,text,text,bigint) from public,anon,authenticated;
grant execute on function public.moreai_workspace_delete_file(uuid,text,uuid,uuid,text,bigint) to service_role;
grant execute on function public.moreai_workspace_rename_file(uuid,text,uuid,uuid,text,text,bigint) to service_role;
