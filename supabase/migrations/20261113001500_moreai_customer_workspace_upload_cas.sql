-- Customer-owned workspace upload contract.
-- Storage objects are immutable and version-addressed. The RPC commits metadata with CAS
-- and the existing version-history trigger archives the previous committed version.
create table if not exists public.customer_workspace_upload_idempotency (
  user_id uuid not null references auth.users(id) on delete cascade,
  idempotency_key text not null check (length(idempotency_key) between 12 and 128),
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  path text not null check (length(path) between 1 and 512),
  expected_version bigint not null check (expected_version >= 0),
  storage_path text not null,
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  size_bytes bigint not null check (size_bytes between 1 and 2000000),
  result jsonb,
  committed_at timestamptz,
  created_at timestamptz not null default now(),
  primary key (user_id, idempotency_key)
);

create index if not exists customer_workspace_upload_idempotency_workspace_idx
  on public.customer_workspace_upload_idempotency (workspace_id, user_id, created_at desc);

alter table public.customer_workspace_upload_idempotency enable row level security;
drop policy if exists customer_workspace_upload_idempotency_server_only
  on public.customer_workspace_upload_idempotency;
create policy customer_workspace_upload_idempotency_server_only
  on public.customer_workspace_upload_idempotency for all to anon, authenticated
  using (false) with check (false);
revoke all on public.customer_workspace_upload_idempotency from public, anon, authenticated;
grant all on public.customer_workspace_upload_idempotency to service_role;

create or replace function public.moreai_customer_workspace_commit_upload(
  p_user_id uuid,
  p_workspace_id uuid,
  p_path text,
  p_expected_version bigint,
  p_idempotency_key text,
  p_storage_path text,
  p_sha256 text,
  p_size_bytes bigint
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
  v_workspace public.workspaces%rowtype;
  v_file public.agent_workspace_files%rowtype;
  v_intent public.customer_workspace_upload_idempotency%rowtype;
  v_next_version bigint;
  v_expected_storage_path text;
  v_result jsonb;
begin
  if p_user_id is null or p_workspace_id is null
     or p_path is null or length(p_path) not between 1 and 512
     or p_expected_version is null or p_expected_version < 0
     or p_idempotency_key is null or length(p_idempotency_key) not between 12 and 128
     or p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$'
     or p_size_bytes is null or p_size_bytes not between 1 and 2000000 then
    raise exception 'workspace_upload_arguments_invalid' using errcode = '22023';
  end if;

  select * into v_workspace
    from public.workspaces
   where id = p_workspace_id and status = 'active'
     and (owner_user_id = p_user_id or exists (
       select 1 from public.workspace_members m
        where m.workspace_id = p_workspace_id
          and m.user_id = p_user_id and m.status = 'active'
     ));
  if not found then
    raise exception 'workspace_membership_required' using errcode = '42501';
  end if;

  v_next_version := p_expected_version + 1;
  v_expected_storage_path := p_user_id::text || '/workspaces/' ||
    p_workspace_id::text || '/versions/' || v_next_version::text || '/' || p_path;
  if p_storage_path is distinct from v_expected_storage_path then
    raise exception 'workspace_upload_storage_path_invalid' using errcode = '22023';
  end if;

  insert into public.customer_workspace_upload_idempotency (
    user_id, idempotency_key, workspace_id, path, expected_version,
    storage_path, sha256, size_bytes
  ) values (
    p_user_id, p_idempotency_key, p_workspace_id, p_path, p_expected_version,
    p_storage_path, p_sha256, p_size_bytes
  ) on conflict (user_id, idempotency_key) do nothing;

  select * into v_intent
    from public.customer_workspace_upload_idempotency
   where user_id = p_user_id and idempotency_key = p_idempotency_key
   for update;

  if v_intent.workspace_id <> p_workspace_id
     or v_intent.path <> p_path
     or v_intent.expected_version <> p_expected_version
     or v_intent.storage_path <> p_storage_path
     or v_intent.sha256 <> p_sha256
     or v_intent.size_bytes <> p_size_bytes then
    raise exception 'workspace_upload_idempotency_key_reused' using errcode = '22023';
  end if;

  if v_intent.committed_at is not null then
    return coalesce(v_intent.result, '{}'::jsonb) || jsonb_build_object('replayed', true);
  end if;

  insert into public.agent_workspace_files (workspace_id, user_id, path, version)
  values (p_workspace_id, p_user_id, p_path, 0)
  on conflict (workspace_id, path) do nothing;

  update public.agent_workspace_files
     set version = v_next_version,
         storage_path = p_storage_path,
         sha256 = p_sha256,
         size_bytes = p_size_bytes,
         updated_at = now()
   where workspace_id = p_workspace_id
     and path = p_path
     and version = p_expected_version
     and pending_token is null
     and pending_version is null
     and pending_run_id is null
  returning * into v_file;

  if not found then
    raise exception 'workspace_version_conflict_or_write_in_progress' using errcode = '40001';
  end if;

  v_result := jsonb_build_object(
    'workspace_id', p_workspace_id,
    'file_id', v_file.id,
    'path', v_file.path,
    'version', v_file.version,
    'storage_path', v_file.storage_path,
    'sha256', v_file.sha256,
    'size_bytes', v_file.size_bytes,
    'updated_at', v_file.updated_at,
    'replayed', false
  );

  update public.customer_workspace_upload_idempotency
     set result = v_result, committed_at = now()
   where user_id = p_user_id and idempotency_key = p_idempotency_key;

  return v_result;
end;
$function$;

revoke all on function public.moreai_customer_workspace_commit_upload(uuid, uuid, text, bigint, text, text, text, bigint)
  from public, anon, authenticated;
grant execute on function public.moreai_customer_workspace_commit_upload(uuid, uuid, text, bigint, text, text, text, bigint)
  to service_role;
