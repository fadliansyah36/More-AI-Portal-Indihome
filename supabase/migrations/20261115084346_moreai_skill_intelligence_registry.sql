-- MoreAI Skill Intelligence Platform: immutable provenance and explicit trust gates.
create table if not exists public.moreai_skill_packages (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  slug text not null check (slug ~ '^[a-z0-9][a-z0-9._-]{1,119}$'),
  name text not null check (length(btrim(name)) between 2 and 160),
  description text not null default '' check (length(description) <= 2000),
  source_repository text not null check (length(source_repository) between 3 and 255),
  source_ref text not null check (length(source_ref) between 1 and 160),
  source_commit text not null check (source_commit ~ '^[0-9a-f]{40}$'),
  source_path text not null check (length(source_path) between 1 and 512),
  source_blob_sha text not null check (source_blob_sha ~ '^[0-9a-f]{40}$'),
  content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
  version text not null check (length(version) between 1 and 80),
  license_id text not null check (length(license_id) between 1 and 80),
  license_url text,
  license_evidence text,
  license_status text not null default 'unverified' check (license_status in ('unverified','review_required','approved','rejected')),
  manifest jsonb not null default '{}'::jsonb check (jsonb_typeof(manifest) = 'object'),
  requested_permissions jsonb not null default '[]'::jsonb check (jsonb_typeof(requested_permissions) = 'array'),
  validation_status text not null default 'pending' check (validation_status in ('pending','validated','rejected','review_required')),
  validation_report jsonb not null default '{}'::jsonb check (jsonb_typeof(validation_report) = 'object'),
  publication_status text not null default 'private' check (publication_status in ('private','pending_review','published','deprecated')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(owner_user_id, source_repository, source_commit, source_path)
);
create index if not exists moreai_skill_packages_owner_updated_idx
  on public.moreai_skill_packages(owner_user_id, updated_at desc, id desc);
create index if not exists moreai_skill_packages_public_catalog_idx
  on public.moreai_skill_packages(publication_status, name) where publication_status = 'published';

create table if not exists public.moreai_skill_installs (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  skill_package_id uuid not null references public.moreai_skill_packages(id) on delete restrict,
  status text not null default 'installed' check (status in ('installed','disabled','removed')),
  execution_enabled boolean not null default false,
  permission_request jsonb not null default '[]'::jsonb check (jsonb_typeof(permission_request) = 'array'),
  permission_status text not null default 'not_requested' check (permission_status in ('not_requested','pending_review','approved','rejected','revoked')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(owner_user_id, skill_package_id)
);
create index if not exists moreai_skill_installs_owner_idx
  on public.moreai_skill_installs(owner_user_id, updated_at desc);

alter table public.moreai_skill_packages enable row level security;
alter table public.moreai_skill_installs enable row level security;
revoke all on public.moreai_skill_packages, public.moreai_skill_installs from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_skill_packages, public.moreai_skill_installs to service_role;
drop policy if exists moreai_skill_packages_server_only on public.moreai_skill_packages;
create policy moreai_skill_packages_server_only on public.moreai_skill_packages
  for all to anon, authenticated using (false) with check (false);
drop policy if exists moreai_skill_installs_server_only on public.moreai_skill_installs;
create policy moreai_skill_installs_server_only on public.moreai_skill_installs
  for all to anon, authenticated using (false) with check (false);
