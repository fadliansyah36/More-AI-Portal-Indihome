
-- MoreAI Phase 02: identity, tenancy, partner and network persistence foundation.
-- Business operations remain API-only; client roles receive no table DML grants.
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_path text,
  locale text not null default 'id-ID',
  timezone text not null default 'Asia/Jakarta',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.user_devices (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  platform text not null check (platform in ('web','ios','android')),
  device_key_hash text not null,
  push_token_reference text,
  last_seen_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  unique(user_id, device_key_hash)
);
create table public.workspaces (
  id uuid primary key default gen_random_uuid(),
  name text not null check (length(trim(name)) between 1 and 160),
  slug text not null unique check (slug ~ '^[a-z0-9][a-z0-9-]{1,78}[a-z0-9]$'),
  owner_user_id uuid not null references auth.users(id),
  status text not null default 'active' check (status in ('active','suspended','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.roles (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  scope text not null check (scope in ('platform','workspace','partner','location')),
  description text,
  system_role boolean not null default false,
  created_at timestamptz not null default now()
);
create table public.permissions (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  description text,
  created_at timestamptz not null default now()
);
create table public.role_permissions (
  role_id uuid not null references public.roles(id) on delete cascade,
  permission_id uuid not null references public.permissions(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key(role_id, permission_id)
);
create table public.workspace_members (
  id uuid primary key default gen_random_uuid(),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role_id uuid not null references public.roles(id),
  status text not null default 'invited' check (status in ('invited','active','suspended','removed')),
  invited_by uuid references auth.users(id),
  joined_at timestamptz,
  created_at timestamptz not null default now(),
  unique(workspace_id,user_id)
);
create table public.user_role_assignments (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  role_id uuid not null references public.roles(id),
  scope_type text not null check (scope_type in ('platform','workspace','partner','location')),
  scope_id uuid,
  assigned_by uuid references auth.users(id),
  expires_at timestamptz,
  created_at timestamptz not null default now(),
  check ((scope_type='platform' and scope_id is null) or (scope_type<>'platform' and scope_id is not null))
);
create table public.admin_audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid references auth.users(id),
  action text not null,
  resource_type text not null,
  resource_id text,
  scope_type text,
  scope_id uuid,
  correlation_id text,
  outcome text not null check (outcome in ('success','denied','failed')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table public.security_events (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid references auth.users(id),
  event_type text not null,
  severity text not null check (severity in ('info','warning','high','critical')),
  subject_type text,
  subject_hash text,
  correlation_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create table public.partner_organizations (
  id uuid primary key default gen_random_uuid(),
  legal_name text not null,
  display_name text not null,
  status text not null default 'pending' check (status in ('pending','active','suspended','rejected','closed')),
  created_by uuid references auth.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.partner_members (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.partner_organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role_key text not null check (role_key in ('partner_owner','partner_admin','location_manager','partner_staff','partner_analyst')),
  location_id uuid,
  status text not null default 'invited' check (status in ('invited','active','suspended','removed')),
  created_at timestamptz not null default now(),
  unique(partner_id,user_id,location_id)
);
create table public.partner_locations (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.partner_organizations(id) on delete cascade,
  name text not null,
  address jsonb not null default '{}'::jsonb,
  latitude numeric(9,6) check (latitude is null or latitude between -90 and 90),
  longitude numeric(9,6) check (longitude is null or longitude between -180 and 180),
  timezone text not null default 'Asia/Jakarta',
  status text not null default 'active' check (status in ('active','inactive','suspended')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.partner_members add constraint partner_members_location_fk
  foreign key(location_id) references public.partner_locations(id) on delete cascade;
create table public.network_providers (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  name text not null,
  provider_type text not null,
  status text not null default 'active' check (status in ('active','inactive')),
  created_at timestamptz not null default now()
);
create table public.provider_partnerships (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.partner_organizations(id),
  provider_id uuid not null references public.network_providers(id),
  external_reference text,
  status text not null default 'pending' check (status in ('pending','active','suspended','ended')),
  starts_at timestamptz,
  ends_at timestamptz,
  created_at timestamptz not null default now(),
  unique(partner_id,provider_id),
  check (ends_at is null or starts_at is null or ends_at > starts_at)
);
create table public.partner_networks (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.partner_organizations(id),
  location_id uuid not null references public.partner_locations(id),
  provider_id uuid references public.network_providers(id),
  name text not null,
  ssid_label text,
  gateway_type text not null,
  gateway_network_ref text,
  status text not null default 'pending' check (status in ('pending','active','inactive','suspended')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(location_id,name),
  unique(gateway_type,gateway_network_ref)
);
create table public.network_verification_configs (
  id uuid primary key default gen_random_uuid(),
  network_id uuid not null references public.partner_networks(id) on delete cascade,
  method_key text not null,
  config_public jsonb not null default '{}'::jsonb,
  secret_reference text,
  enabled boolean not null default false,
  policy jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(network_id,method_key)
);
create table public.network_verification_attempts (
  id uuid primary key default gen_random_uuid(),
  network_id uuid not null references public.partner_networks(id),
  user_id uuid references auth.users(id),
  method_key text not null,
  status text not null check (status in ('pending','verified','rejected','expired','error')),
  failure_code text,
  correlation_id text,
  created_at timestamptz not null default now(),
  completed_at timestamptz,
  check (completed_at is null or completed_at >= created_at)
);
create table public.network_verification_evidence (
  id uuid primary key default gen_random_uuid(),
  attempt_id uuid not null references public.network_verification_attempts(id) on delete cascade,
  evidence_type text not null,
  issuer text not null,
  subject_hash text not null,
  payload_hash text not null,
  signature_valid boolean not null default false,
  issued_at timestamptz,
  expires_at timestamptz,
  verified_at timestamptz,
  created_at timestamptz not null default now()
);
create table public.network_verification_sessions (
  id uuid primary key default gen_random_uuid(),
  attempt_id uuid not null references public.network_verification_attempts(id),
  user_id uuid not null references auth.users(id),
  network_id uuid not null references public.partner_networks(id),
  gateway_session_hash text not null unique,
  status text not null check (status in ('active','ended','expired','revoked')),
  verified_at timestamptz not null,
  expires_at timestamptz not null,
  ended_at timestamptz,
  created_at timestamptz not null default now(),
  check (expires_at > verified_at),
  check (ended_at is null or ended_at >= verified_at)
);
create table public.network_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id),
  network_id uuid not null references public.partner_networks(id),
  verification_session_id uuid not null references public.network_verification_sessions(id),
  status text not null check (status in ('active','ended','expired','revoked')),
  started_at timestamptz not null default now(),
  last_heartbeat_at timestamptz,
  expires_at timestamptz not null,
  ended_at timestamptz,
  end_reason text,
  check (expires_at > started_at),
  check (ended_at is null or ended_at >= started_at)
);
create table public.network_session_events (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.network_sessions(id) on delete cascade,
  event_type text not null,
  event_payload jsonb not null default '{}'::jsonb,
  correlation_id text,
  created_at timestamptz not null default now()
);
create table public.entitlement_policies (
  id uuid primary key default gen_random_uuid(),
  key text not null unique,
  name text not null,
  priority integer not null default 100,
  policy jsonb not null,
  active boolean not null default true,
  version integer not null default 1 check (version > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table public.user_entitlements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id),
  entitlement_key text not null,
  source_type text not null check (source_type in ('partner_network','subscription','purchase','admin_grant','promotion')),
  source_id uuid,
  status text not null check (status in ('active','expired','revoked','suspended')),
  starts_at timestamptz not null,
  expires_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  check (expires_at is null or expires_at > starts_at)
);
create index workspace_members_user_status_idx on public.workspace_members(user_id,status);
create index user_role_assignments_scope_idx on public.user_role_assignments(user_id,scope_type,scope_id,expires_at);
create index partner_members_user_status_idx on public.partner_members(user_id,status);
create index partner_locations_partner_status_idx on public.partner_locations(partner_id,status);
create index partner_networks_partner_status_idx on public.partner_networks(partner_id,status);
create index verification_attempts_user_created_idx on public.network_verification_attempts(user_id,created_at desc);
create index network_sessions_user_status_idx on public.network_sessions(user_id,status,expires_at);
create index entitlements_user_status_expiry_idx on public.user_entitlements(user_id,status,expires_at);
-- Every exposed application table is RLS protected. Business writes are API-only.
do $$
declare t record;
begin
  for t in select tablename from pg_tables where schemaname='public'
    and tablename in ('profiles','user_devices','workspaces','roles','permissions','role_permissions','workspace_members','user_role_assignments','admin_audit_logs','security_events','partner_organizations','partner_members','partner_locations','network_providers','provider_partnerships','partner_networks','network_verification_configs','network_verification_attempts','network_verification_evidence','network_verification_sessions','network_sessions','network_session_events','entitlement_policies','user_entitlements')
  loop
    execute format('alter table public.%I enable row level security',t.tablename);
    execute format('revoke all on table public.%I from anon, authenticated',t.tablename);
    execute format('grant all on table public.%I to service_role',t.tablename);
  end loop;
end $$;
create policy profiles_read_own on public.profiles for select to authenticated using (id = (select auth.uid()));
create policy workspaces_read_member on public.workspaces for select to authenticated using (
  exists (select 1 from public.workspace_members m where m.workspace_id = id and m.user_id = (select auth.uid()) and m.status = 'active')
  or owner_user_id = (select auth.uid())
);
create policy workspace_members_read_self on public.workspace_members for select to authenticated using (user_id = (select auth.uid()));
create policy partner_members_read_self on public.partner_members for select to authenticated using (user_id = (select auth.uid()) and status = 'active');
