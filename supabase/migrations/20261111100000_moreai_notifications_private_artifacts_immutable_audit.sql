-- MoreAI Phase 05: notification persistence, immutable audit, private artifacts bucket.
-- Forward-only and idempotent. Existing business tables and audit history are preserved.

create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  notification_type text not null check (char_length(notification_type) between 1 and 80),
  title text not null check (char_length(title) between 1 and 180),
  body text not null default '' check (char_length(body) <= 4000),
  resource_type text,
  resource_id text,
  action_url text,
  dedupe_key text,
  metadata jsonb not null default '{}'::jsonb,
  read_at timestamptz,
  created_at timestamptz not null default now(),
  constraint notifications_dedupe_key_valid check (dedupe_key is null or char_length(dedupe_key) between 1 and 200)
);
create unique index if not exists notifications_user_dedupe_uidx
  on public.notifications(user_id, dedupe_key) where dedupe_key is not null;
create index if not exists notifications_user_created_idx
  on public.notifications(user_id, created_at desc);
create index if not exists notifications_unread_idx
  on public.notifications(user_id, created_at desc) where read_at is null;

create table if not exists public.notification_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  in_app_enabled boolean not null default true,
  email_enabled boolean not null default false,
  category_settings jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);
alter table public.notifications enable row level security;
alter table public.notification_preferences enable row level security;
drop policy if exists notifications_server_only on public.notifications;
create policy notifications_server_only on public.notifications for all to anon, authenticated using (false) with check (false);
drop policy if exists notification_preferences_server_only on public.notification_preferences;
create policy notification_preferences_server_only on public.notification_preferences for all to anon, authenticated using (false) with check (false);
revoke all on public.notifications, public.notification_preferences from anon, authenticated;
grant all on public.notifications, public.notification_preferences to service_role;

-- Private bucket. Storage objects already have RLS enabled and no client policies;
-- service-role API/worker paths are the only supported access boundary.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'moreai-artifacts',
  'moreai-artifacts',
  false,
  2097152,
  array['text/plain','text/markdown','application/json','text/csv','application/pdf','image/png','image/jpeg','image/webp']
)
on conflict (id) do update
set public = false,
    file_size_limit = least(coalesce(storage.buckets.file_size_limit, 2097152), 2097152),
    allowed_mime_types = excluded.allowed_mime_types;

-- Existing admin audit history is retained. Entries become append-only at the DB layer.
create or replace function public.moreai_reject_admin_audit_mutation()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
begin
  raise exception 'admin_audit_logs_are_immutable' using errcode = '55000';
end;
$$;
drop trigger if exists admin_audit_logs_immutable_row on public.admin_audit_logs;
create trigger admin_audit_logs_immutable_row
before update or delete on public.admin_audit_logs
for each row execute function public.moreai_reject_admin_audit_mutation();
drop trigger if exists admin_audit_logs_immutable_truncate on public.admin_audit_logs;
create trigger admin_audit_logs_immutable_truncate
before truncate on public.admin_audit_logs
for each statement execute function public.moreai_reject_admin_audit_mutation();
revoke update, delete, truncate on public.admin_audit_logs from anon, authenticated, service_role;
grant select, insert on public.admin_audit_logs to service_role;
revoke all on function public.moreai_reject_admin_audit_mutation() from public, anon, authenticated;
