-- Additive migration: atomically persist a user chat message and its durable agent run.
-- No table reset, destructive DDL, or RLS relaxation.
create or replace function public.moreai_enqueue_chat_run(
    p_user_id uuid,
    p_conversation_id uuid,
    p_content text,
    p_agent_key text,
    p_idempotency_key text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
    v_conversation public.conversations%rowtype;
    v_message public.conversation_messages%rowtype;
    v_run public.agent_runs%rowtype;
begin
    if p_user_id is null
       or p_conversation_id is null
       or p_content is null
       or length(btrim(p_content)) = 0
       or length(p_content) > 100000
       or p_agent_key is null
       or p_idempotency_key is null
       or length(p_idempotency_key) < 12
       or length(p_idempotency_key) > 128
       or p_agent_key not in ('manus', 'planning') then
        raise exception 'invalid chat enqueue request' using errcode = '22023';
    end if;

    select *
      into v_conversation
      from public.conversations
     where id = p_conversation_id
       and user_id = p_user_id
     for update;

    if not found then
        raise exception 'conversation not found' using errcode = '42501';
    end if;

    select *
      into v_run
      from public.agent_runs
     where user_id = p_user_id
       and idempotency_key = p_idempotency_key;

    if found then
        return pg_catalog.jsonb_build_object(
            'run', pg_catalog.to_jsonb(v_run),
            'message', null,
            'replayed', true
        );
    end if;

    insert into public.conversation_messages (
        conversation_id, user_id, role, content, metadata
    ) values (
        p_conversation_id, p_user_id, 'user', p_content, '{}'::jsonb
    )
    returning * into v_message;

    insert into public.agent_runs (
        user_id, workspace_id, conversation_id, status,
        idempotency_key, input, max_attempts
    ) values (
        p_user_id,
        v_conversation.workspace_id,
        p_conversation_id,
        'queued',
        p_idempotency_key,
        pg_catalog.jsonb_build_object(
            'prompt', p_content,
            'agent_key', p_agent_key,
            'conversation_id', p_conversation_id,
            'message_id', v_message.id
        ),
        3
    )
    returning * into v_run;

    update public.conversation_messages
       set run_id = v_run.id
     where id = v_message.id
       and user_id = p_user_id;
    v_message.run_id := v_run.id;

    return pg_catalog.jsonb_build_object(
        'run', pg_catalog.to_jsonb(v_run),
        'message', pg_catalog.to_jsonb(v_message),
        'replayed', false
    );
end;
$function$;

revoke all on function public.moreai_enqueue_chat_run(uuid, uuid, text, text, text) from public;
revoke all on function public.moreai_enqueue_chat_run(uuid, uuid, text, text, text) from anon;
revoke all on function public.moreai_enqueue_chat_run(uuid, uuid, text, text, text) from authenticated;
grant execute on function public.moreai_enqueue_chat_run(uuid, uuid, text, text, text) to service_role;
