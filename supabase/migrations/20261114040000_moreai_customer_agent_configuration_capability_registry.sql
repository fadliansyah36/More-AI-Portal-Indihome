-- Phase 09: owner-scoped agent configuration and live worker capability registry.
create table if not exists public.moreai_customer_agent_configs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    runtime_key text not null check (runtime_key in ('manus', 'toolcall')),
    name text not null check (length(btrim(name)) between 2 and 80),
    description text not null default '' check (length(description) <= 500),
    system_prompt text not null default '' check (length(system_prompt) <= 12000),
    tool_keys text[] not null default '{}',
    enabled boolean not null default true,
    version integer not null default 1 check (version > 0),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create unique index if not exists moreai_customer_agent_configs_owner_name_uq
    on public.moreai_customer_agent_configs(user_id, lower(name));
create index if not exists moreai_customer_agent_configs_owner_updated_idx
    on public.moreai_customer_agent_configs(user_id, updated_at desc);
alter table public.moreai_customer_agent_configs enable row level security;
revoke all on public.moreai_customer_agent_configs from public, anon, authenticated;
grant select, insert, update, delete on public.moreai_customer_agent_configs to service_role;

create table if not exists public.moreai_worker_capability_snapshots (
    worker_id text primary key check (length(worker_id) between 8 and 128),
    runtime_keys text[] not null default '{}',
    capabilities jsonb not null default '{}'::jsonb,
    status text not null default 'healthy' check (status in ('healthy', 'degraded')),
    last_seen_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
alter table public.moreai_worker_capability_snapshots enable row level security;
revoke all on public.moreai_worker_capability_snapshots from public, anon, authenticated;
grant select, insert, update on public.moreai_worker_capability_snapshots to service_role;

create or replace function public.moreai_worker_publish_capabilities(
    p_worker_id text, p_runtime_keys text[], p_capabilities jsonb, p_status text default 'healthy'
) returns jsonb
language plpgsql security invoker set search_path = ''
as $function$
declare v_row public.moreai_worker_capability_snapshots%rowtype;
begin
    if p_worker_id is null or length(p_worker_id) < 8 or length(p_worker_id) > 128
       or p_runtime_keys is null or p_capabilities is null
       or jsonb_typeof(p_capabilities) <> 'object'
       or p_status not in ('healthy', 'degraded') then
        raise exception 'invalid worker capability heartbeat' using errcode = '22023';
    end if;
    insert into public.moreai_worker_capability_snapshots(
        worker_id, runtime_keys, capabilities, status, last_seen_at, updated_at
    ) values (p_worker_id, p_runtime_keys, p_capabilities, p_status, now(), now())
    on conflict (worker_id) do update set
        runtime_keys = excluded.runtime_keys, capabilities = excluded.capabilities,
        status = excluded.status, last_seen_at = now(), updated_at = now()
    returning * into v_row;
    return jsonb_build_object(
        'worker_id', v_row.worker_id, 'runtime_keys', to_jsonb(v_row.runtime_keys),
        'status', v_row.status, 'last_seen_at', v_row.last_seen_at
    );
end;
$function$;
revoke all on function public.moreai_worker_publish_capabilities(text, text[], jsonb, text) from public, anon, authenticated;
grant execute on function public.moreai_worker_publish_capabilities(text, text[], jsonb, text) to service_role;

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
                'tool_keys', to_jsonb(v_config.tool_keys), 'version', v_config.version
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
