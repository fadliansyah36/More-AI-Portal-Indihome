-- Explicit, user-controlled Personal Memory. Conversation history remains a separate store.
create table if not exists public.moreai_customer_memory_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  enabled boolean not null default false,
  consent_version text not null,
  consented_at timestamptz,
  disabled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint moreai_customer_memory_consent_version_nonempty check (length(consent_version) between 1 and 40)
);

create table if not exists public.moreai_customer_memories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  content text not null,
  source_type text not null default 'user_created',
  scope text not null default 'personal',
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint moreai_customer_memory_title_length check (length(btrim(title)) between 1 and 120),
  constraint moreai_customer_memory_content_length check (length(btrim(content)) between 1 and 4000),
  constraint moreai_customer_memory_source_check check (source_type = 'user_created'),
  constraint moreai_customer_memory_scope_check check (scope = 'personal'),
  constraint moreai_customer_memory_expiry_check check (expires_at > created_at and expires_at <= created_at + interval '366 days')
);

create index if not exists moreai_customer_memories_owner_expiry_idx
  on public.moreai_customer_memories (user_id, expires_at asc, updated_at desc);

alter table public.moreai_customer_memory_preferences enable row level security;
alter table public.moreai_customer_memories enable row level security;

drop policy if exists moreai_customer_memory_preferences_owner_all on public.moreai_customer_memory_preferences;
create policy moreai_customer_memory_preferences_owner_all
  on public.moreai_customer_memory_preferences for all to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

drop policy if exists moreai_customer_memories_owner_all on public.moreai_customer_memories;
create policy moreai_customer_memories_owner_all
  on public.moreai_customer_memories for all to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

grant select, insert, update, delete on public.moreai_customer_memory_preferences to authenticated;
grant select, insert, update, delete on public.moreai_customer_memories to authenticated;
grant all on public.moreai_customer_memory_preferences to service_role;
grant all on public.moreai_customer_memories to service_role;

create or replace function public.moreai_customer_set_memory_consent(
  p_user_id uuid, p_enabled boolean, p_consent_version text
) returns public.moreai_customer_memory_preferences
language plpgsql
security invoker
set search_path = ''
as $function$
declare v_row public.moreai_customer_memory_preferences%rowtype;
begin
  if p_user_id is null or p_enabled is null or p_consent_version is null
     or length(p_consent_version) not between 1 and 40 then
    raise exception 'memory_consent_arguments_invalid' using errcode = '22023';
  end if;
  insert into public.moreai_customer_memory_preferences (
    user_id, enabled, consent_version, consented_at, disabled_at, updated_at
  ) values (
    p_user_id, p_enabled, p_consent_version,
    case when p_enabled then now() else null end,
    case when p_enabled then null else now() end,
    now()
  )
  on conflict (user_id) do update set
    enabled = excluded.enabled,
    consent_version = excluded.consent_version,
    consented_at = case when excluded.enabled then now()
                        else public.moreai_customer_memory_preferences.consented_at end,
    disabled_at = case when excluded.enabled then null else now() end,
    updated_at = now()
  returning * into v_row;
  return v_row;
end;
$function$;

revoke all on function public.moreai_customer_set_memory_consent(uuid, boolean, text) from public, anon, authenticated;
grant execute on function public.moreai_customer_set_memory_consent(uuid, boolean, text) to service_role;
