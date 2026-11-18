create or replace function public.moreai_admin_mutate_llm_provider(
  p_actor_user_id uuid, p_provider_id uuid, p_key text, p_display_name text,
  p_enabled boolean, p_credentials_ready boolean, p_correlation_id text default null
) returns jsonb
language plpgsql security definer set search_path=public,pg_temp as $$
declare v_provider public.llm_providers%rowtype; v_action text;
begin
  if p_actor_user_id is null or p_key not in ('google','openai','anthropic')
    or length(trim(coalesce(p_display_name,'')))<2 or length(trim(coalesce(p_display_name,'')))>120 then
    raise exception using errcode='22023',message='LLM_PROVIDER_INVALID';
  end if;
  if not exists(
    select 1 from public.user_role_assignments ura
    join public.roles r on r.id=ura.role_id
    join public.role_permissions rp on rp.role_id=r.id
    join public.permissions p on p.id=rp.permission_id
    where ura.user_id=p_actor_user_id and ura.scope_type='platform' and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at>now()) and r.scope='platform'
      and p.key='platform.models.manage'
  ) then raise exception using errcode='42501',message='ADMIN_PERMISSION_DENIED'; end if;
  if p_enabled and not coalesce(p_credentials_ready,false) then
    raise exception using errcode='55000',message='PROVIDER_CREDENTIALS_NOT_CONFIGURED';
  end if;
  if p_provider_id is null then
    insert into public.llm_providers(key,display_name,enabled,config)
    values(p_key,trim(p_display_name),p_enabled,'{}'::jsonb) returning * into v_provider;
    v_action:='llm.provider.create';
  else
    select * into v_provider from public.llm_providers where id=p_provider_id for update;
    if not found then raise exception using errcode='P0002',message='LLM_PROVIDER_NOT_FOUND'; end if;
    if v_provider.key<>p_key then raise exception using errcode='22023',message='LLM_PROVIDER_KEY_IMMUTABLE'; end if;
    update public.llm_providers set display_name=trim(p_display_name),enabled=p_enabled,updated_at=now()
      where id=p_provider_id returning * into v_provider;
    v_action:='llm.provider.update';
  end if;
  insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,correlation_id,outcome,metadata)
  values(p_actor_user_id,v_action,'llm_provider',v_provider.id::text,'platform',
    coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text),'success',
    jsonb_build_object('key',v_provider.key,'display_name',v_provider.display_name,'enabled',v_provider.enabled,'credentials_ready',coalesce(p_credentials_ready,false)));
  return jsonb_build_object('id',v_provider.id,'key',v_provider.key,'display_name',v_provider.display_name,'enabled',v_provider.enabled);
end; $$;

create or replace function public.moreai_admin_mutate_llm_model(
  p_actor_user_id uuid, p_model_id uuid, p_provider_id uuid, p_key text, p_display_name text,
  p_input_cost_per_million numeric, p_output_cost_per_million numeric,
  p_max_input_tokens integer, p_max_output_tokens integer, p_capabilities text[],
  p_enabled boolean, p_correlation_id text default null
) returns jsonb
language plpgsql security definer set search_path=public,pg_temp as $$
declare v_model public.llm_models%rowtype; v_provider public.llm_providers%rowtype; v_action text;
begin
  if p_actor_user_id is null or p_provider_id is null or length(trim(coalesce(p_key,'')))<1
    or length(trim(coalesce(p_key,'')))>160 or length(trim(coalesce(p_display_name,'')))<2
    or length(trim(coalesce(p_display_name,'')))>160
    or p_input_cost_per_million<0 or p_output_cost_per_million<0
    or (p_max_input_tokens is not null and p_max_input_tokens<1)
    or (p_max_output_tokens is not null and p_max_output_tokens<1) then
    raise exception using errcode='22023',message='LLM_MODEL_INVALID';
  end if;
  if not exists(
    select 1 from public.user_role_assignments ura join public.roles r on r.id=ura.role_id
    join public.role_permissions rp on rp.role_id=r.id join public.permissions p on p.id=rp.permission_id
    where ura.user_id=p_actor_user_id and ura.scope_type='platform' and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at>now()) and r.scope='platform' and p.key='platform.models.manage'
  ) then raise exception using errcode='42501',message='ADMIN_PERMISSION_DENIED'; end if;
  select * into v_provider from public.llm_providers where id=p_provider_id for share;
  if not found then raise exception using errcode='P0002',message='LLM_PROVIDER_NOT_FOUND'; end if;
  if p_enabled and not v_provider.enabled then raise exception using errcode='55000',message='LLM_PROVIDER_DISABLED'; end if;
  if p_model_id is null then
    insert into public.llm_models(provider_id,key,display_name,input_cost_per_million,output_cost_per_million,
      max_input_tokens,max_output_tokens,capabilities,enabled)
    values(p_provider_id,trim(p_key),trim(p_display_name),p_input_cost_per_million,p_output_cost_per_million,
      p_max_input_tokens,p_max_output_tokens,coalesce(p_capabilities,'{}'::text[]),p_enabled)
    returning * into v_model;
    v_action:='llm.model.create';
  else
    select * into v_model from public.llm_models where id=p_model_id for update;
    if not found then raise exception using errcode='P0002',message='LLM_MODEL_NOT_FOUND'; end if;
    update public.llm_models set provider_id=p_provider_id,key=trim(p_key),display_name=trim(p_display_name),
      input_cost_per_million=p_input_cost_per_million,output_cost_per_million=p_output_cost_per_million,
      max_input_tokens=p_max_input_tokens,max_output_tokens=p_max_output_tokens,
      capabilities=coalesce(p_capabilities,'{}'::text[]),enabled=p_enabled,updated_at=now()
      where id=p_model_id returning * into v_model;
    v_action:='llm.model.update';
  end if;
  insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,correlation_id,outcome,metadata)
  values(p_actor_user_id,v_action,'llm_model',v_model.id::text,'platform',
    coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text),'success',
    jsonb_build_object('provider_id',v_model.provider_id,'key',v_model.key,'display_name',v_model.display_name,
      'enabled',v_model.enabled,'input_cost_per_million',v_model.input_cost_per_million,
      'output_cost_per_million',v_model.output_cost_per_million,'capabilities',v_model.capabilities));
  return jsonb_build_object('id',v_model.id,'provider_id',v_model.provider_id,'key',v_model.key,
    'display_name',v_model.display_name,'enabled',v_model.enabled,'input_cost_per_million',v_model.input_cost_per_million,
    'output_cost_per_million',v_model.output_cost_per_million,'max_input_tokens',v_model.max_input_tokens,
    'max_output_tokens',v_model.max_output_tokens,'capabilities',v_model.capabilities);
end; $$;

create or replace function public.moreai_admin_mutate_llm_route(
  p_actor_user_id uuid, p_policy_id uuid, p_task_type text, p_model_id uuid,
  p_fallback_model_id uuid, p_priority integer, p_enabled boolean, p_correlation_id text default null
) returns jsonb
language plpgsql security definer set search_path=public,pg_temp as $$
declare v_policy public.llm_routing_policies%rowtype; v_action text;
begin
  if p_actor_user_id is null or p_task_type<>'general' or p_model_id is null or p_priority<0 then
    raise exception using errcode='22023',message='LLM_ROUTE_INVALID';
  end if;
  if not exists(
    select 1 from public.user_role_assignments ura join public.roles r on r.id=ura.role_id
    join public.role_permissions rp on rp.role_id=r.id join public.permissions p on p.id=rp.permission_id
    where ura.user_id=p_actor_user_id and ura.scope_type='platform' and ura.scope_id is null
      and (ura.expires_at is null or ura.expires_at>now()) and r.scope='platform' and p.key='platform.models.manage'
  ) then raise exception using errcode='42501',message='ADMIN_PERMISSION_DENIED'; end if;
  if p_enabled and not exists(
    select 1 from public.llm_models m join public.llm_providers pr on pr.id=m.provider_id
    where m.id=p_model_id and m.enabled=true and pr.enabled=true
  ) then raise exception using errcode='55000',message='LLM_PRIMARY_MODEL_NOT_READY'; end if;
  if p_enabled and p_fallback_model_id is not null and not exists(
    select 1 from public.llm_models m join public.llm_providers pr on pr.id=m.provider_id
    where m.id=p_fallback_model_id and m.enabled=true and pr.enabled=true
  ) then raise exception using errcode='55000',message='LLM_FALLBACK_MODEL_NOT_READY'; end if;
  if p_policy_id is null then
    insert into public.llm_routing_policies(scope_type,scope_id,task_type,model_id,priority,fallback_model_id,enabled)
    values('platform',null,p_task_type,p_model_id,p_priority,p_fallback_model_id,p_enabled) returning * into v_policy;
    v_action:='llm.routing.create';
  else
    select * into v_policy from public.llm_routing_policies where id=p_policy_id and scope_type='platform' and scope_id is null for update;
    if not found then raise exception using errcode='P0002',message='LLM_ROUTE_NOT_FOUND'; end if;
    update public.llm_routing_policies set task_type=p_task_type,model_id=p_model_id,priority=p_priority,
      fallback_model_id=p_fallback_model_id,enabled=p_enabled where id=p_policy_id returning * into v_policy;
    v_action:='llm.routing.update';
  end if;
  insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,correlation_id,outcome,metadata)
  values(p_actor_user_id,v_action,'llm_routing_policy',v_policy.id::text,'platform',
    coalesce(nullif(p_correlation_id,''),gen_random_uuid()::text),'success',
    jsonb_build_object('task_type',v_policy.task_type,'model_id',v_policy.model_id,
      'fallback_model_id',v_policy.fallback_model_id,'priority',v_policy.priority,'enabled',v_policy.enabled));
  return jsonb_build_object('id',v_policy.id,'task_type',v_policy.task_type,'model_id',v_policy.model_id,
    'fallback_model_id',v_policy.fallback_model_id,'priority',v_policy.priority,'enabled',v_policy.enabled);
end; $$;

revoke all on function public.moreai_admin_mutate_llm_provider(uuid,uuid,text,text,boolean,boolean,text) from public,anon,authenticated;
grant execute on function public.moreai_admin_mutate_llm_provider(uuid,uuid,text,text,boolean,boolean,text) to service_role;
revoke all on function public.moreai_admin_mutate_llm_model(uuid,uuid,uuid,text,text,numeric,numeric,integer,integer,text[],boolean,text) from public,anon,authenticated;
grant execute on function public.moreai_admin_mutate_llm_model(uuid,uuid,uuid,text,text,numeric,numeric,integer,integer,text[],boolean,text) to service_role;
revoke all on function public.moreai_admin_mutate_llm_route(uuid,uuid,text,uuid,uuid,integer,boolean,text) from public,anon,authenticated;
grant execute on function public.moreai_admin_mutate_llm_route(uuid,uuid,text,uuid,uuid,integer,boolean,text) to service_role;