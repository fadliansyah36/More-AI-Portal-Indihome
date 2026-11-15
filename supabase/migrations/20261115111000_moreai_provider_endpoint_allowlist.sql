-- Only enable upstreams that are implemented by the current OpenAI-compatible adapter.
-- The worker uses /chat/completions and bearer authentication for these two endpoints.
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
  if p_actor_user_id is null or p_provider_id is null or p_base_url is null
    or p_base_url !~* '^https://[a-z0-9.-]+(:[0-9]{1,5})?(/[a-z0-9._~!$&''()*+,;=:@%/-]*)?$'
    or p_secret_env_name is null
    or p_secret_env_name !~ '^MOREAI_PROVIDER_[A-Z0-9_]{1,100}$' then
    raise exception using errcode='22023', message='LLM_PROVIDER_CONFIG_INVALID';
  end if;

  v_host := lower(split_part(split_part(p_base_url,'://',2),'/',1));
  v_host := split_part(v_host,':',1);
  if v_host in ('localhost','localhost.localdomain')
    or v_host ~ '^(127\.|10\.|192\.168\.|169\.254\.|0\.)'
    or v_host ~ '^172\.(1[6-9]|2[0-9]|3[01])\.' then
    raise exception using errcode='22023', message='LLM_PROVIDER_HOST_NOT_ALLOWED';
  end if;

  if not exists (
    select 1 from public.user_role_assignments ura
    join public.roles r on r.id=ura.role_id
    join public.role_permissions rp on rp.role_id=r.id
    join public.permissions p on p.id=rp.permission_id
    where ura.user_id=p_actor_user_id and ura.scope_type='platform'
      and ura.scope_id is null and (ura.expires_at is null or ura.expires_at>now())
      and r.scope='platform' and p.key='platform.models.manage'
  ) then
    raise exception using errcode='42501', message='ADMIN_PERMISSION_DENIED';
  end if;

  select * into v_provider from public.llm_providers where id=p_provider_id for update;
  if not found then
    raise exception using errcode='P0002', message='LLM_PROVIDER_NOT_FOUND';
  end if;

  if (v_provider.key='openai' and v_host<>'api.openai.com')
    or (v_provider.key='google' and v_host<>'generativelanguage.googleapis.com')
    or v_provider.key not in ('openai','google') then
    raise exception using errcode='22023', message='LLM_PROVIDER_ENDPOINT_NOT_SUPPORTED_BY_ADAPTER';
  end if;

  update public.llm_providers
  set config=jsonb_build_object('base_url',rtrim(p_base_url,'/'),'secret_env_name',p_secret_env_name),
      updated_at=now()
  where id=p_provider_id returning * into v_provider;

  insert into public.admin_audit_logs(
    actor_user_id,action,resource_type,resource_id,scope_type,correlation_id,outcome,metadata
  ) values (
    p_actor_user_id,'llm.provider.configure','llm_provider',v_provider.id::text,'platform',
    coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text),'success',
    jsonb_build_object('provider_key',v_provider.key,'base_url',rtrim(p_base_url,'/'),
      'secret_env_name',p_secret_env_name)
  );

  return jsonb_build_object('id',v_provider.id,'key',v_provider.key,
    'configured',true,'enabled',v_provider.enabled);
end;
$function$;