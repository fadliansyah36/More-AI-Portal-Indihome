-- Atomically commit all workspace changes from one isolated execution.
-- Storage objects are uploaded first to immutable version paths; this RPC commits
-- the complete metadata set in one PostgreSQL transaction or commits none.
create table if not exists public.agent_workspace_execution_commits (
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  operation_key text not null check (operation_key ~ '^[0-9a-f]{64}$'),
  user_id uuid not null references auth.users(id) on delete cascade,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  result jsonb not null,
  committed_at timestamptz not null default now(),
  primary key (run_id, operation_key)
);

alter table public.agent_workspace_execution_commits enable row level security;
drop policy if exists agent_workspace_execution_commits_server_only on public.agent_workspace_execution_commits;
create policy agent_workspace_execution_commits_server_only
  on public.agent_workspace_execution_commits for all to anon, authenticated
  using (false) with check (false);
revoke all on public.agent_workspace_execution_commits from public, anon, authenticated;
grant all on public.agent_workspace_execution_commits to service_role;

create or replace function public.moreai_workspace_commit_execution_snapshot(
  p_run_id uuid,
  p_worker_id text,
  p_user_id uuid,
  p_workspace_id uuid,
  p_bucket text,
  p_operation_key text,
  p_changes jsonb,
  p_deletes jsonb
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  r public.agent_runs%rowtype;
  f public.agent_workspace_files%rowtype;
  item jsonb;
  v_path text;
  v_storage_path text;
  v_expected bigint;
  v_next bigint;
  v_size bigint;
  v_sha text;
  v_saved jsonb := '[]'::jsonb;
  v_deleted jsonb := '[]'::jsonb;
  v_result jsonb;
  v_count integer;
  v_distinct integer;
begin
  if p_run_id is null or p_user_id is null or p_workspace_id is null
     or p_worker_id is null or length(p_worker_id) not between 8 and 128
     or p_bucket is null or length(p_bucket) not between 1 and 100
     or p_operation_key is null or p_operation_key !~ '^[0-9a-f]{64}$'
     or jsonb_typeof(p_changes) <> 'array'
     or jsonb_typeof(p_deletes) <> 'array'
     or jsonb_array_length(p_changes) > 200
     or jsonb_array_length(p_deletes) > 200
     or jsonb_array_length(p_changes) + jsonb_array_length(p_deletes) > 200 then
    raise exception 'workspace_execution_commit_arguments_invalid' using errcode='22023';
  end if;

  select * into r from public.agent_runs where id=p_run_id for update;
  if not found or r.user_id<>p_user_id or r.workspace_id is distinct from p_workspace_id then
    raise exception 'workspace_run_scope_invalid' using errcode='42501';
  end if;

  -- A retry after a lost HTTP response returns the already committed result.
  select result into v_result
    from public.agent_workspace_execution_commits
    where run_id=p_run_id and operation_key=p_operation_key
      and user_id=p_user_id and workspace_id=p_workspace_id;
  if found then
    return v_result;
  end if;

  if r.status<>'running' or r.lease_owner is distinct from p_worker_id
     or r.lease_expires_at is null or r.lease_expires_at<=now() then
    raise exception 'workspace_run_scope_or_lease_invalid' using errcode='42501';
  end if;
  if not exists (
    select 1 from public.workspaces w
    where w.id=p_workspace_id and w.status='active'
      and (w.owner_user_id=p_user_id or exists (
        select 1 from public.workspace_members m
        where m.workspace_id=w.id and m.user_id=p_user_id and m.status='active'
      ))
  ) then
    raise exception 'workspace_membership_required' using errcode='42501';
  end if;
  if not exists(select 1 from storage.buckets b where b.id=p_bucket and b.public=false) then
    raise exception 'workspace_bucket_must_be_private' using errcode='42501';
  end if;

  select count(*), count(distinct x.path)
    into v_count, v_distinct
    from (
      select value->>'path' as path from jsonb_array_elements(p_changes)
      union all
      select value->>'path' as path from jsonb_array_elements(p_deletes)
    ) x;
  if v_count <> v_distinct then
    raise exception 'workspace_execution_duplicate_path' using errcode='22023';
  end if;

  -- Deterministic path ordering reduces lock-order inversions between runs.
  for item in
    select value from jsonb_array_elements(p_changes)
    order by value->>'path'
  loop
    v_path := item->>'path';
    if v_path is null or length(v_path) not between 1 and 512
       or position(chr(92) in v_path)>0
       or v_path ~ '(^/|//|(^|/)\.\.?(/|$))'
       or v_path !~ '^[A-Za-z0-9._ -]+(/[A-Za-z0-9._ -]+)*$'
       or coalesce(item->>'expected_version','') !~ '^(0|[1-9][0-9]{0,18})$'
       or coalesce(item->>'size_bytes','') !~ '^(0|[1-9][0-9]{0,6})$'
       or coalesce(item->>'sha256','') !~ '^[0-9a-f]{64}$' then
      raise exception 'workspace_execution_change_invalid' using errcode='22023';
    end if;
    v_expected := (item->>'expected_version')::bigint;
    v_size := (item->>'size_bytes')::bigint;
    v_sha := item->>'sha256';
    if v_expected >= 9223372036854775807 or v_size > 2000000 then
      raise exception 'workspace_execution_change_limit_exceeded' using errcode='22023';
    end if;
    v_next := v_expected + 1;
    v_storage_path := p_user_id::text||'/workspaces/'||p_workspace_id::text
      ||'/versions/'||v_next::text||'/'||v_path;
    if item->>'storage_path' is distinct from v_storage_path then
      raise exception 'workspace_execution_storage_path_invalid' using errcode='22023';
    end if;
    if not exists(select 1 from storage.objects o where o.bucket_id=p_bucket and o.name=v_storage_path) then
      raise exception 'workspace_execution_object_missing' using errcode='P0002';
    end if;

    select * into f from public.agent_workspace_files
      where workspace_id=p_workspace_id and path=v_path for update;
    if not found then
      if v_expected<>0 then
        raise exception 'workspace_version_conflict' using errcode='40001';
      end if;
      insert into public.agent_workspace_files(
        workspace_id,user_id,path,version,storage_path,sha256,size_bytes,updated_at
      ) values (
        p_workspace_id,p_user_id,v_path,1,v_storage_path,v_sha,v_size,now()
      );
    else
      if f.user_id<>p_user_id or f.deleted_at is not null then
        raise exception 'workspace_execution_path_not_active' using errcode='40001';
      end if;
      if f.version<>v_expected or f.pending_token is not null then
        raise exception 'workspace_version_conflict' using errcode='40001';
      end if;
      update public.agent_workspace_files
        set version=v_next,storage_path=v_storage_path,sha256=v_sha,
            size_bytes=v_size,updated_at=now()
        where id=f.id and version=v_expected and pending_token is null;
      if not found then
        raise exception 'workspace_execution_write_fence_lost' using errcode='40001';
      end if;
    end if;
    v_saved := v_saved || jsonb_build_array(jsonb_build_object(
      'path',v_path,'version',v_next,'sha256',v_sha,'size_bytes',v_size
    ));
  end loop;

  for item in
    select value from jsonb_array_elements(p_deletes)
    order by value->>'path'
  loop
    v_path := item->>'path';
    if v_path is null or length(v_path) not between 1 and 512
       or position(chr(92) in v_path)>0
       or v_path ~ '(^/|//|(^|/)\.\.?(/|$))'
       or v_path !~ '^[A-Za-z0-9._ -]+(/[A-Za-z0-9._ -]+)*$'
       or coalesce(item->>'expected_version','') !~ '^[1-9][0-9]{0,18}$' then
      raise exception 'workspace_execution_delete_invalid' using errcode='22023';
    end if;
    v_expected := (item->>'expected_version')::bigint;
    select * into f from public.agent_workspace_files
      where workspace_id=p_workspace_id and path=v_path for update;
    if not found or f.user_id<>p_user_id or f.deleted_at is not null
       or f.version<>v_expected or f.pending_token is not null
       or f.storage_path is null or f.sha256 is null or f.size_bytes is null then
      raise exception 'workspace_execution_delete_conflict' using errcode='40001';
    end if;
    insert into public.agent_workspace_file_versions(
      workspace_id,user_id,path,version,storage_path,sha256,size_bytes,committed_at
    ) values (
      f.workspace_id,f.user_id,f.path,f.version,f.storage_path,f.sha256,f.size_bytes,f.updated_at
    ) on conflict(workspace_id,path,version) do nothing;
    update public.agent_workspace_files
      set deleted_at=now(),updated_at=now()
      where id=f.id and version=v_expected and deleted_at is null and pending_token is null;
    if not found then
      raise exception 'workspace_execution_delete_fence_lost' using errcode='40001';
    end if;
    v_deleted := v_deleted || jsonb_build_array(jsonb_build_object(
      'path',v_path,'version',v_expected,'deleted',true
    ));
  end loop;

  v_result := jsonb_build_object(
    'saved',v_saved,'deleted',v_deleted,
    'saved_count',jsonb_array_length(v_saved),
    'deleted_count',jsonb_array_length(v_deleted),
    'atomic',true
  );
  insert into public.agent_workspace_execution_commits(
    run_id,operation_key,user_id,workspace_id,result
  ) values (p_run_id,p_operation_key,p_user_id,p_workspace_id,v_result);
  return v_result;
end;
$$;

revoke all on function public.moreai_workspace_commit_execution_snapshot(uuid,text,uuid,uuid,text,text,jsonb,jsonb)
  from public, anon, authenticated;
grant execute on function public.moreai_workspace_commit_execution_snapshot(uuid,text,uuid,uuid,text,text,jsonb,jsonb)
  to service_role;
