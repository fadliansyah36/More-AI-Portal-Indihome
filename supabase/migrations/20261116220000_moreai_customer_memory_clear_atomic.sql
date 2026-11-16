-- Atomic owner-scoped Personal Memory clear.
-- The API supplies the authenticated user ID after customer_principal authorization.
-- All changes below commit or roll back together. Chat messages and citations are preserved.

create or replace function public.moreai_customer_clear_memory_atomic(p_user_id uuid)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $function$
declare
  v_preferences_updated bigint := 0;
  v_memories_deleted bigint := 0;
  v_episodes_cleared bigint := 0;
begin
  if p_user_id is null then
    raise exception 'memory_clear_user_required' using errcode = '22023';
  end if;

  -- Serialize against the create RPC below. If a create already owns this row,
  -- it commits before this clear; otherwise later creates see disabled consent.
  perform 1
    from public.moreai_customer_memory_preferences
   where user_id = p_user_id
   for update;

  update public.moreai_customer_memory_preferences
     set enabled = false,
         disabled_at = now(),
         updated_at = now()
   where user_id = p_user_id;
  get diagnostics v_preferences_updated = row_count;

  delete from public.moreai_customer_memories
   where user_id = p_user_id;
  get diagnostics v_memories_deleted = row_count;

  -- Match the existing API cleanup semantics: remove only episodic-memory
  -- metadata, retaining the original conversation message and all citations.
  update public.conversation_messages
     set metadata = metadata - array[
       'memory_type',
       'memory_scope',
       'workspace_id',
       'episode',
       'episode_expires_at'
     ]::text[]
   where user_id = p_user_id
     and metadata ->> 'memory_type' = 'episodic';
  get diagnostics v_episodes_cleared = row_count;

  return jsonb_build_object(
    'completed', true,
    'consent_disabled', v_preferences_updated > 0,
    'memories_deleted', v_memories_deleted,
    'episodes_cleared', v_episodes_cleared
  );
end;
$function$;

revoke all on function public.moreai_customer_clear_memory_atomic(uuid)
  from public, anon, authenticated;
grant execute on function public.moreai_customer_clear_memory_atomic(uuid)
  to service_role;


-- Serialize explicit Personal Memory creation with the atomic clear operation.
create or replace function public.moreai_customer_create_personal_memory(
  p_user_id uuid,
  p_consent_version text,
  p_title text,
  p_content text,
  p_retention_days integer
)
returns setof public.moreai_customer_memories
language plpgsql
security invoker
set search_path = ''
as $function$
declare
  v_enabled boolean;
  v_consent_version text;
begin
  if p_user_id is null
     or p_consent_version is null
     or p_title is null
     or p_content is null
     or length(btrim(p_title)) not between 1 and 120
     or length(btrim(p_content)) not between 1 and 4000
     or p_retention_days not in (30, 90, 180, 365) then
    raise exception 'personal_memory_arguments_invalid' using errcode = '22023';
  end if;

  select enabled, consent_version
    into v_enabled, v_consent_version
    from public.moreai_customer_memory_preferences
   where user_id = p_user_id
   for update;

  if not found or not v_enabled or v_consent_version <> p_consent_version then
    raise exception 'personal_memory_consent_required' using errcode = '42501';
  end if;

  return query
  insert into public.moreai_customer_memories (
    user_id, title, content, source_type, scope, expires_at
  ) values (
    p_user_id,
    btrim(p_title),
    btrim(p_content),
    'user_created',
    'personal',
    now() + (p_retention_days * interval '1 day')
  )
  returning *;
end;
$function$;

revoke all on function public.moreai_customer_create_personal_memory(uuid, text, text, text, integer)
  from public, anon, authenticated;
grant execute on function public.moreai_customer_create_personal_memory(uuid, text, text, text, integer)
  to service_role;
