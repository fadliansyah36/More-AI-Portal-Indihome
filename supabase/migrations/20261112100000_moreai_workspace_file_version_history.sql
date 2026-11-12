-- Preserve immutable metadata for every committed workspace file version.
-- Object bytes remain in the private workspace Storage bucket; this table is metadata only.
create table if not exists public.agent_workspace_file_versions (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  path text not null check (length(path) between 1 and 512),
  version bigint not null check (version > 0),
  storage_path text not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  size_bytes bigint not null check (size_bytes between 0 and 2000000),
  committed_at timestamptz not null,
  recorded_at timestamptz not null default now(),
  unique (workspace_id, path, version)
);

create index if not exists agent_workspace_file_versions_owner_path_idx
  on public.agent_workspace_file_versions (user_id, workspace_id, path, version desc);

alter table public.agent_workspace_file_versions enable row level security;
drop policy if exists agent_workspace_file_versions_server_only on public.agent_workspace_file_versions;
create policy agent_workspace_file_versions_server_only
  on public.agent_workspace_file_versions for all to anon, authenticated
  using (false) with check (false);
revoke all on public.agent_workspace_file_versions from public, anon, authenticated;
grant all on public.agent_workspace_file_versions to service_role;

create or replace function public.moreai_record_workspace_file_version()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.version > old.version
     and old.version > 0
     and old.storage_path is not null
     and old.sha256 is not null
     and old.size_bytes is not null then
    insert into public.agent_workspace_file_versions (
      workspace_id, user_id, path, version, storage_path, sha256, size_bytes, committed_at
    ) values (
      old.workspace_id, old.user_id, old.path, old.version,
      old.storage_path, old.sha256, old.size_bytes, old.updated_at
    ) on conflict (workspace_id, path, version) do nothing;
  end if;
  return new;
end;
$$;

drop trigger if exists agent_workspace_file_versions_archive on public.agent_workspace_files;
create trigger agent_workspace_file_versions_archive
  before update of version on public.agent_workspace_files
  for each row execute function public.moreai_record_workspace_file_version();

revoke all on function public.moreai_record_workspace_file_version() from public, anon, authenticated;
