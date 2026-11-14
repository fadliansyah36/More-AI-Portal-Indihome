create table if not exists public.moreai_skill_source_files (
  id uuid primary key default gen_random_uuid(),
  skill_package_id uuid not null references public.moreai_skill_packages(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  relative_path text not null check (length(relative_path) between 1 and 512 and relative_path !~ '(^/|(^|/)\.\.(/|$))'),
  git_blob_sha text not null check (git_blob_sha ~ '^[0-9a-f]{40}$'),
  content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
  media_type text not null,
  byte_size integer not null check (byte_size between 0 and 524288),
  text_content text,
  binary_content_base64 text,
  created_at timestamptz not null default now(),
  unique(skill_package_id, relative_path),
  check ((text_content is null) <> (binary_content_base64 is null))
);
create index if not exists moreai_skill_source_files_owner_idx
  on public.moreai_skill_source_files(owner_user_id, skill_package_id);
alter table public.moreai_skill_source_files enable row level security;
revoke all on public.moreai_skill_source_files from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_skill_source_files to service_role;
drop policy if exists moreai_skill_source_files_server_only on public.moreai_skill_source_files;
create policy moreai_skill_source_files_server_only on public.moreai_skill_source_files
  for all to anon, authenticated using (false) with check (false);

create table if not exists public.moreai_skill_execution_audit (
  id uuid primary key default gen_random_uuid(),
  skill_package_id uuid not null references public.moreai_skill_packages(id) on delete restrict,
  skill_install_id uuid not null references public.moreai_skill_installs(id) on delete restrict,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  agent_run_id uuid not null,
  skill_version text not null,
  skill_content_sha256 text not null check (skill_content_sha256 ~ '^[0-9a-f]{64}$'),
  permission_snapshot jsonb not null default '[]'::jsonb check (jsonb_typeof(permission_snapshot) = 'array'),
  event_type text not null check (event_type in ('resolved','rejected','executed')),
  event_detail jsonb not null default '{}'::jsonb check (jsonb_typeof(event_detail) = 'object'),
  created_at timestamptz not null default now()
);
create index if not exists moreai_skill_execution_audit_run_idx
  on public.moreai_skill_execution_audit(agent_run_id, created_at);
alter table public.moreai_skill_execution_audit enable row level security;
revoke all on public.moreai_skill_execution_audit from public, anon, authenticated;
grant select, insert on public.moreai_skill_execution_audit to service_role;
drop policy if exists moreai_skill_execution_audit_server_only on public.moreai_skill_execution_audit;
create policy moreai_skill_execution_audit_server_only on public.moreai_skill_execution_audit
  for all to anon, authenticated using (false) with check (false);
