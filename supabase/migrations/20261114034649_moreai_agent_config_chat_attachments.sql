-- Add owner-scoped saved Agent configuration to the durable attachment-aware chat enqueue.
create or replace function public.moreai_enqueue_chat_run_with_config(
    p_user_id uuid,
    p_conversation_id uuid,
    p_content text,
    p_agent_key text,
    p_idempotency_key text,
    p_agent_config_id uuid,
    p_attachment_ids uuid[] default '{}'::uuid[]
) returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
    v_conversation public.conversations%rowtype;
    v_message public.conversation_messages%rowtype;
    v_run public.agent_runs%rowtype;
    v_config public.moreai_customer_agent_configs%rowtype;
    v_attachment_ids uuid[];
    v_attachment_count integer;
begin
    if p_user_id is null or p_conversation_id is null
       or p_content is null or length(btrim(p_content)) = 0 or length(p_content) > 100000
       or p_agent_key is null or p_agent_key not in ('manus','toolcall')
       or p_idempotency_key is null or length(p_idempotency_key) not between 12 and 128
       or p_agent_config_id is null or coalesce(cardinality(p_attachment_ids),0) > 10 then
        raise exception 'invalid_configured_chat_enqueue_request' using errcode = '22023';
    end if;
    select * into v_config from public.moreai_customer_agent_configs
     where id = p_agent_config_id and user_id = p_user_id and enabled = true for share;
    if not found or v_config.runtime_key <> p_agent_key then
        raise exception 'agent_configuration_not_found_or_runtime_mismatch' using errcode = '42501';
    end if;
    select coalesce(array_agg(x order by x), '{}'::uuid[])
      into v_attachment_ids
      from (select distinct unnest(coalesce(p_attachment_ids, '{}'::uuid[])) as x) q;
    if cardinality(v_attachment_ids) <> coalesce(cardinality(p_attachment_ids),0) then
        raise exception 'duplicate_chat_attachment_id' using errcode = '22023';
    end if;
    select * into v_conversation from public.conversations
     where id = p_conversation_id and user_id = p_user_id and status = 'active' for update;
    if not found then raise exception 'conversation_not_found_or_inactive' using errcode = '42501'; end if;
    if cardinality(v_attachment_ids) > 0 then
        select count(*) into v_attachment_count from public.artifacts a
         where a.id = any(v_attachment_ids)
           and a.user_id = p_user_id
           and a.metadata->>'purpose' = 'chat_attachment'
           and a.metadata->>'conversation_id' = p_conversation_id::text
           and a.size_bytes between 1 and 2000000
           and a.mime_type in ('text/plain','text/markdown','text/csv','application/json',
             'application/pdf','image/jpeg','image/png','image/webp');
        if v_attachment_count <> cardinality(v_attachment_ids) then
            raise exception 'chat_attachment_not_owned_or_not_available' using errcode = '42501';
        end if;
    end if;
    select * into v_run from public.agent_runs
     where user_id = p_user_id and idempotency_key = p_idempotency_key;
    if found then
        if v_run.input->>'prompt' is distinct from p_content
           or v_run.input->>'agent_key' is distinct from p_agent_key
           or v_run.input->'agent_config'->>'id' is distinct from p_agent_config_id::text
           or coalesce(v_run.input->'attachment_ids','[]'::jsonb) is distinct from to_jsonb(v_attachment_ids) then
            raise exception 'chat_idempotency_key_payload_conflict' using errcode = '22023';
        end if;
        return jsonb_build_object('run',to_jsonb(v_run),'message',null,'replayed',true);
    end if;
    insert into public.conversation_messages(conversation_id,user_id,role,content,metadata)
    values(p_conversation_id,p_user_id,'user',p_content,'{}'::jsonb) returning * into v_message;
    insert into public.agent_runs(user_id,workspace_id,conversation_id,status,idempotency_key,input,max_attempts)
    values(
        p_user_id,v_conversation.workspace_id,p_conversation_id,'queued',p_idempotency_key,
        jsonb_build_object(
            'prompt',p_content,'agent_key',p_agent_key,'conversation_id',p_conversation_id,
            'message_id',v_message.id,'attachment_ids',to_jsonb(v_attachment_ids),
            'agent_config',jsonb_build_object(
                'id',v_config.id,'runtime_key',v_config.runtime_key,'name',v_config.name,
                'system_prompt',v_config.system_prompt,'tool_keys',to_jsonb(v_config.tool_keys),
                'version',v_config.version
            )
        ),3
    ) returning * into v_run;
    update public.conversation_messages set run_id = v_run.id
     where id = v_message.id and user_id = p_user_id;
    v_message.run_id := v_run.id;
    if cardinality(v_attachment_ids) > 0 then
        insert into public.conversation_message_attachments(user_id,conversation_id,message_id,run_id,artifact_id)
        select p_user_id,p_conversation_id,v_message.id,v_run.id,x from unnest(v_attachment_ids) as x;
    end if;
    return jsonb_build_object('run',to_jsonb(v_run),'message',to_jsonb(v_message),'replayed',false);
end;
$function$;
revoke all on function public.moreai_enqueue_chat_run_with_config(uuid,uuid,text,text,text,uuid,uuid[])
  from public, anon, authenticated;
grant execute on function public.moreai_enqueue_chat_run_with_config(uuid,uuid,text,text,text,uuid,uuid[])
  to service_role;
