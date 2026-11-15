-- Phase 09A: align the platform routing contract with OpenManus runtime task types.
-- Preserve the existing mutation signature and all authorization/audit gates.
create or replace function public.moreai_admin_mutate_llm_route(
  p_actor_user_id uuid,
  p_policy_id uuid,
  p_task_type text,
  p_model_id uuid,
  p_fallback_model_id uuid,
  p_priority integer,
  p_enabled boolean,
  p_correlation_id text default null
)
returns jsonb
language plpgsql
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_policy public.llm_routing_policies%rowtype;
  v_action text;
begin
  if p_actor_user_id is null
    or p_task_type not in ('general', 'chat', 'planning')
    or p_model_id is null
    or p_priority < 0 then
    raise exception using errcode='22023', message='LLM_ROUTE_INVALID';
  end if;

  if not exists (
    select 1
    from public.user_role_assignments ura
    join public.roles r on r.id=ura.role_id
    join public.role_permissions rp on rp.role_id=r.id
    join public.permissions p on p.id=rp.permission_id
    where ura.user_id=p_actor_user_id
      and ura.scope_type='platform'
      and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at>now())
      and r.scope='platform'
      and p.key='platform.models.manage'
  ) then
    raise exception using errcode='42501', message='ADMIN_PERMISSION_DENIED';
  end if;

  if p_enabled and not exists (
    select 1 from public.llm_models m
    join public.llm_providers pr on pr.id=m.provider_id
    where m.id=p_model_id and m.enabled=true and pr.enabled=true
  ) then
    raise exception using errcode='55000', message='LLM_PRIMARY_MODEL_NOT_READY';
  end if;

  if p_enabled and p_fallback_model_id is not null and not exists (
    select 1 from public.llm_models m
    join public.llm_providers pr on pr.id=m.provider_id
    where m.id=p_fallback_model_id and m.enabled=true and pr.enabled=true
  ) then
    raise exception using errcode='55000', message='LLM_FALLBACK_MODEL_NOT_READY';
  end if;

  if p_policy_id is null then
    insert into public.llm_routing_policies(
      scope_type, scope_id, task_type, model_id, priority, fallback_model_id, enabled
    ) values ('platform', null, p_task_type, p_model_id, p_priority, p_fallback_model_id, p_enabled)
    returning * into v_policy;
    v_action := 'llm.routing.create';
  else
    select * into v_policy
    from public.llm_routing_policies
    where id=p_policy_id and scope_type='platform' and scope_id is null
    for update;
    if not found then
      raise exception using errcode='P0002', message='LLM_ROUTE_NOT_FOUND';
    end if;
    update public.llm_routing_policies
    set task_type=p_task_type, model_id=p_model_id, priority=p_priority,
        fallback_model_id=p_fallback_model_id, enabled=p_enabled
    where id=p_policy_id
    returning * into v_policy;
    v_action := 'llm.routing.update';
  end if;

  insert into public.admin_audit_logs(
    actor_user_id, action, resource_type, resource_id, scope_type,
    correlation_id, outcome, metadata
  ) values (
    p_actor_user_id, v_action, 'llm_routing_policy', v_policy.id::text, 'platform',
    coalesce(nullif(p_correlation_id,''), gen_random_uuid()::text), 'success',
    jsonb_build_object(
      'task_type',v_policy.task_type,'model_id',v_policy.model_id,
      'fallback_model_id',v_policy.fallback_model_id,
      'priority',v_policy.priority,'enabled',v_policy.enabled
    )
  );

  return jsonb_build_object(
    'id',v_policy.id,'task_type',v_policy.task_type,'model_id',v_policy.model_id,
    'fallback_model_id',v_policy.fallback_model_id,'priority',v_policy.priority,
    'enabled',v_policy.enabled
  );
end;
$function$;

-- Provider endpoint configuration stores only a public HTTPS URL and a secret
-- environment-variable name. The credential value remains in the worker host.
create or replace function public.moreai_admin_configure_llm_provider(
  p_actor_user_id uuid,
  p_provider_id uuid,
  p_base_url text,
  p_secret_env_name text,
  p_correlation_id text default null
)
returns jsonb
language plpgsql
security definer
set search_path to 'public', 'pg_temp'
as $function$
declare
  v_provider public.llm_providers%rowtype;
  v_host text;
begin
  if p_actor_user_id is null or p_provider_id is null
    or p_base_url is null
    or p_base_url !~* '^https://[a-z0-9.-]+(:[0-9]{1,5})?(/[a-z0-9._~!$&''()*+,;=:@%/-]*)?$'
    or p_secret_env_name is null
    or p_secret_env_name !~ '^MOREAI_PROVIDER_[A-Z0-9_]{1,100}$' then
    raise exception using errcode='22023', message='LLM_PROVIDER_CONFIG_INVALID';
  end if;

  v_host := lower(split_part(split_part(p_base_url, '://', 2), '/', 1));
  v_host := split_part(v_host, ':', 1);
  if v_host !~ '\.' or v_host in ('localhost','localhost.localdomain')
    or v_host ~ '^(127\.|10\.|192\.168\.|169\.254\.|0\.)'
    or v_host ~ '^172\.(1[6-9]|2[0-9]|3[01])\.' then
    raise exception using errcode='22023', message='LLM_PROVIDER_HOST_NOT_ALLOWED';
  end if;

  if not exists (
    select 1
    from public.user_role_assignments ura
    join public.roles r on r.id=ura.role_id
    join public.role_permissions rp on rp.role_id=r.id
    join public.permissions p on p.id=rp.permission_id
    where ura.user_id=p_actor_user_id
      and ura.scope_type='platform' and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at>now())
      and r.scope='platform' and p.key='platform.models.manage'
  ) then
    raise exception using errcode='42501', message='ADMIN_PERMISSION_DENIED';
  end if;

  select * into v_provider
  from public.llm_providers
  where id=p_provider_id
  for update;
  if not found then
    raise exception using errcode='P0002', message='LLM_PROVIDER_NOT_FOUND';
  end if;

  update public.llm_providers
  set config = jsonb_build_object(
        'base_url', rtrim(p_base_url, '/'),
        'secret_env_name', p_secret_env_name
      ),
      updated_at=now()
  where id=p_provider_id
  returning * into v_provider;

  insert into public.admin_audit_logs(
    actor_user_id, action, resource_type, resource_id, scope_type,
    correlation_id, outcome, metadata
  ) values (
    p_actor_user_id, 'llm.provider.configure', 'llm_provider',
    v_provider.id::text, 'platform',
    coalesce(nullif(p_correlation_id,''), gen_random_uuid()::text),
    'success',
    jsonb_build_object(
      'provider_key',v_provider.key,
      'base_url',rtrim(p_base_url,'/'),
      'secret_env_name',p_secret_env_name
    )
  );

  return jsonb_build_object(
    'id',v_provider.id,'key',v_provider.key,
    'configured',true,'enabled',v_provider.enabled
  );
end;
$function$;

revoke all on function public.moreai_admin_configure_llm_provider(uuid,uuid,text,text,text) from public, anon, authenticated;
grant execute on function public.moreai_admin_configure_llm_provider(uuid,uuid,text,text,text) to service_role;
