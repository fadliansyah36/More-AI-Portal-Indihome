alter table public.moreai_skill_installs
  add column if not exists granted_permissions jsonb not null default '[]'::jsonb
  check (jsonb_typeof(granted_permissions) = 'array');
