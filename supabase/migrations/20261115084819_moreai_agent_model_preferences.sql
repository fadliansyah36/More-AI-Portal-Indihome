-- Phase 09: owner-configured model preference constrained by active Model Router policy.
alter table public.moreai_customer_agent_configs
  add column if not exists preferred_model_id uuid
  references public.llm_models(id) on delete set null;

create index if not exists moreai_customer_agent_configs_preferred_model_idx
  on public.moreai_customer_agent_configs(preferred_model_id)
  where preferred_model_id is not null;

create or replace function public.moreai_enqueue_chat_run_with_config(
    p_user_id uuid, p_conversation_id uuid, p_content text, p_agent_key text,
    p_idempotency_key text, p_agent_config_id uuid
) returns jsonb
language plpgsql security definer set search_path = ''
as $function$
declare
    v_conversation public.conversations%rowtype;
    v_message public.conversation_messages%rowtype;
    v_run public.agent_runs%rowtype;
    v_config public.moreai_customer_agent_configs%rowtype;
begin
    if p_user_id is null or p_conversation_id is null
       or p_content is null or length(btrim(p_content)) = 0 or length(p_content) > 100000
       or p_agent_key not in ('manus', 'toolcall')
       or p_idempotency_key is null or length(p_idempotency_key) < 12 or length(p_idempotency_key) > 128
       or p_agent_config_id is null then
        raise exception 'invalid configured chat enqueue request' using errcode = '22023';
    end if;
    select * into v_config from public.moreai_customer_agent_configs
     where id = p_agent_config_id and user_id = p_user_id and enabled = true for share;
    if not found or v_config.runtime_key <> p_agent_key then
        raise exception 'agent configuration not found or runtime mismatch' using errcode = '42501';
    end if;
    if v_config.preferred_model_id is not null and not exists (
        select 1 from public.llm_models m
        join public.llm_providers p on p.id = m.provider_id
        where m.id = v_config.preferred_model_id and m.enabled = true and p.enabled = true
    ) then
        raise exception 'configured_model_is_not_enabled' using errcode = '22023';
    end if;
    select * into v_conversation from public.conversations
     where id = p_conversation_id and user_id = p_user_id for update;
    if not found then raise exception 'conversation not found' using errcode = '42501'; end if;
    select * into v_run from public.agent_runs
     where user_id = p_user_id and idempotency_key = p_idempotency_key;
    if found then
        return jsonb_build_object('run', to_jsonb(v_run), 'message', null, 'replayed', true);
    end if;
    insert into public.conversation_messages(conversation_id, user_id, role, content, metadata)
    values (p_conversation_id, p_user_id, 'user', p_content, '{}'::jsonb)
    returning * into v_message;
    insert into public.agent_runs(
        user_id, workspace_id, conversation_id, status, idempotency_key, input, max_attempts
    ) values (
        p_user_id, v_conversation.workspace_id, p_conversation_id, 'queued',
        p_idempotency_key,
        jsonb_build_object(
            'prompt', p_content, 'agent_key', p_agent_key,
            'agent_config', jsonb_build_object(
                'id', v_config.id, 'runtime_key', v_config.runtime_key,
                'name', v_config.name, 'system_prompt', v_config.system_prompt,
                'tool_keys', to_jsonb(v_config.tool_keys),
                'preferred_model_id', v_config.preferred_model_id,
                'version', v_config.version
            ),
            'conversation_id', p_conversation_id, 'message_id', v_message.id
        ),
        3
    ) returning * into v_run;
    update public.conversation_messages set run_id = v_run.id
     where id = v_message.id and user_id = p_user_id;
    v_message.run_id := v_run.id;
    return jsonb_build_object('run', to_jsonb(v_run), 'message', to_jsonb(v_message), 'replayed', false);
end;
$function$;
revoke all on function public.moreai_enqueue_chat_run_with_config(uuid, uuid, text, text, text, uuid) from public, anon, authenticated;
grant execute on function public.moreai_enqueue_chat_run_with_config(uuid, uuid, text, text, text, uuid) to service_role;
