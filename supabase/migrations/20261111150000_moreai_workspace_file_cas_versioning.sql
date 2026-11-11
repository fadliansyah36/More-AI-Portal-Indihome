create table if not exists public.agent_workspace_files (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 path text not null check(length(path) between 1 and 512),
 version bigint not null default 0 check(version>=0),
 pending_version bigint,
 pending_token uuid,
 pending_run_id uuid references public.agent_runs(id) on delete set null,
 storage_path text,
 sha256 text check(sha256 is null or sha256 ~ '^[0-9a-f]{64}$'),
 size_bytes bigint check(size_bytes is null or size_bytes between 0 and 2000000),
 updated_at timestamptz not null default now(),
 unique(workspace_id,path),
 check ((pending_version is null and pending_token is null and pending_run_id is null)
     or (pending_version=version+1 and pending_token is not null and pending_run_id is not null))
);
alter table public.agent_workspace_files enable row level security;
drop policy if exists agent_workspace_files_server_only on public.agent_workspace_files;
create policy agent_workspace_files_server_only on public.agent_workspace_files for all to anon,authenticated using(false) with check(false);
revoke all on public.agent_workspace_files from public,anon,authenticated;
grant all on public.agent_workspace_files to service_role;

create or replace function public.moreai_workspace_begin_write(
 p_run_id uuid,p_worker_id text,p_user_id uuid,p_workspace_id uuid,p_path text,p_expected_version bigint
) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; f public.agent_workspace_files%rowtype; v_token uuid; v_version bigint;
begin
 if p_path is null or length(p_path) not between 1 and 512 or p_expected_version<0 then raise exception 'workspace_write_arguments_invalid' using errcode='22023'; end if;
 select * into r from public.agent_runs where id=p_run_id for update;
 if not found or r.user_id<>p_user_id or r.workspace_id is distinct from p_workspace_id
  or r.status<>'running' or r.lease_owner is distinct from p_worker_id or r.lease_expires_at<=now()
 then raise exception 'workspace_run_scope_or_lease_invalid' using errcode='42501'; end if;
 if not exists(select 1 from public.workspaces w where w.id=p_workspace_id and w.status='active'
  and (w.owner_user_id=p_user_id or exists(select 1 from public.workspace_members m where m.workspace_id=w.id and m.user_id=p_user_id and m.status='active')))
 then raise exception 'workspace_membership_required' using errcode='42501'; end if;
 select * into f from public.agent_workspace_files where workspace_id=p_workspace_id and path=p_path for update;
 if not found then
  if p_expected_version<>0 then raise exception 'workspace_version_conflict' using errcode='40001'; end if;
  insert into public.agent_workspace_files(workspace_id,user_id,path) values(p_workspace_id,p_user_id,p_path) returning * into f;
 end if;
 if f.user_id<>p_user_id or f.version<>p_expected_version then raise exception 'workspace_version_conflict' using errcode='40001'; end if;
 if f.pending_token is not null then raise exception 'workspace_write_in_progress' using errcode='40001'; end if;
 v_token:=gen_random_uuid(); v_version:=f.version+1;
 update public.agent_workspace_files set pending_version=v_version,pending_token=v_token,pending_run_id=p_run_id,updated_at=now()
 where id=f.id returning * into f;
 return jsonb_build_object('version',v_version,'token',v_token,'current_version',f.version,'storage_path',
  p_user_id::text||'/workspaces/'||p_workspace_id::text||'/versions/'||v_version::text||'/'||replace(p_path,' ','%20'));
end; $$;

create or replace function public.moreai_workspace_commit_write(
 p_run_id uuid,p_worker_id text,p_user_id uuid,p_workspace_id uuid,p_path text,p_token uuid,
 p_version bigint,p_storage_path text,p_sha256 text,p_size_bytes bigint
) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype; f public.agent_workspace_files%rowtype;
begin
 select * into r from public.agent_runs where id=p_run_id for update;
 if not found or r.user_id<>p_user_id or r.workspace_id is distinct from p_workspace_id
  or r.status<>'running' or r.lease_owner is distinct from p_worker_id or r.lease_expires_at<=now()
 then raise exception 'workspace_run_scope_or_lease_invalid' using errcode='42501'; end if;
 if p_sha256 !~ '^[0-9a-f]{64}$' or p_size_bytes not between 0 and 2000000 then raise exception 'workspace_file_metadata_invalid' using errcode='22023'; end if;
 update public.agent_workspace_files set version=p_version,pending_version=null,pending_token=null,pending_run_id=null,
  storage_path=p_storage_path,sha256=p_sha256,size_bytes=p_size_bytes,updated_at=now()
 where workspace_id=p_workspace_id and user_id=p_user_id and path=p_path
  and pending_token=p_token and pending_version=p_version and pending_run_id=p_run_id
 returning * into f;
 if not found then raise exception 'workspace_write_fence_lost' using errcode='40001'; end if;
 return jsonb_build_object('path',f.path,'version',f.version,'sha256',f.sha256,'size_bytes',f.size_bytes);
end; $$;

create or replace function public.moreai_workspace_abort_write(p_run_id uuid,p_worker_id text,p_user_id uuid,p_workspace_id uuid,p_path text,p_token uuid)
returns boolean language plpgsql security definer set search_path='' as $$
declare r public.agent_runs%rowtype;
begin
 select * into r from public.agent_runs where id=p_run_id;
 if not found or r.user_id<>p_user_id or r.workspace_id is distinct from p_workspace_id
  or r.status<>'running' or r.lease_owner is distinct from p_worker_id or r.lease_expires_at<=now()
 then return false; end if;
 update public.agent_workspace_files set pending_version=null,pending_token=null,pending_run_id=null,updated_at=now()
 where workspace_id=p_workspace_id and user_id=p_user_id and path=p_path and pending_token=p_token and pending_run_id=p_run_id;
 return found;
end; $$;

create or replace function public.moreai_workspace_get_file(p_user_id uuid,p_workspace_id uuid,p_path text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare f public.agent_workspace_files%rowtype;
begin
 if not exists(select 1 from public.workspaces w where w.id=p_workspace_id and w.status='active'
  and (w.owner_user_id=p_user_id or exists(select 1 from public.workspace_members m where m.workspace_id=w.id and m.user_id=p_user_id and m.status='active')))
 then raise exception 'workspace_membership_required' using errcode='42501'; end if;
 select * into f from public.agent_workspace_files where workspace_id=p_workspace_id and user_id=p_user_id and path=p_path;
 if not found then return jsonb_build_object('version',0,'storage_path',null,'sha256',null,'size_bytes',0); end if;
 if f.pending_token is not null then raise exception 'workspace_write_in_progress' using errcode='40001'; end if;
 return jsonb_build_object('version',f.version,'storage_path',f.storage_path,'sha256',f.sha256,'size_bytes',f.size_bytes);
end; $$;

revoke all on function public.moreai_workspace_begin_write(uuid,text,uuid,uuid,text,bigint) from public,anon,authenticated;
grant execute on function public.moreai_workspace_begin_write(uuid,text,uuid,uuid,text,bigint) to service_role;
revoke all on function public.moreai_workspace_commit_write(uuid,text,uuid,uuid,text,uuid,bigint,text,text,bigint) from public,anon,authenticated;
grant execute on function public.moreai_workspace_commit_write(uuid,text,uuid,uuid,text,uuid,bigint,text,text,bigint) to service_role;
revoke all on function public.moreai_workspace_abort_write(uuid,text,uuid,uuid,text,uuid) from public,anon,authenticated;
grant execute on function public.moreai_workspace_abort_write(uuid,text,uuid,uuid,text,uuid) to service_role;
revoke all on function public.moreai_workspace_get_file(uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.moreai_workspace_get_file(uuid,uuid,text) to service_role;