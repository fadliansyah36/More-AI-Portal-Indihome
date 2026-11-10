-- Additive migration: reserve an LLM request only when entitlement, quota and wallet
-- checks pass. All quota consumption, credit reservation and request linkage are atomic.
create or replace function public.moreai_llm_reserve_request(
    p_request_id uuid,
    p_user_id uuid,
    p_run_id uuid,
    p_wallet_id uuid,
    p_credit_amount numeric,
    p_estimated_cost numeric,
    p_reservation_key text,
    p_entitlement_key text,
    p_quota_metric_key text,
    p_quota_amount numeric,
    p_workspace_id uuid default null,
    p_partner_id uuid default null
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $function$
declare
    v_request public.llm_request_records%rowtype;
    v_entitlement public.user_entitlements%rowtype;
    v_policy public.quota_policies%rowtype;
    v_usage public.quota_usage%rowtype;
    v_window_start timestamptz;
    v_reservation jsonb;
    v_applied jsonb := '[]'::jsonb;
begin
    if p_request_id is null
       or p_user_id is null
       or p_wallet_id is null
       or p_credit_amount <= 0
       or p_estimated_cost < 0
       or p_quota_amount <= 0
       or p_reservation_key is null
       or p_entitlement_key is null
       or p_quota_metric_key is null then
        raise exception 'invalid llm reserve request' using errcode = '22023';
    end if;

    select *
      into v_request
      from public.llm_request_records
     where id = p_request_id
       and user_id = p_user_id
       and (run_id is not distinct from p_run_id)
       and status = 'processing'
     for update;

    if not found then
        raise exception 'llm request is not claimable' using errcode = '55000';
    end if;

    select *
      into v_entitlement
      from public.user_entitlements
     where user_id = p_user_id
       and entitlement_key = p_entitlement_key
       and status = 'active'
       and starts_at <= now()
       and (expires_at is null or expires_at > now())
     order by starts_at desc
     limit 1
     for share;

    if not found then
        raise exception 'required entitlement is not active' using errcode = '42501';
    end if;

    for v_policy in
        select *
          from public.quota_policies q
         where q.metric_key = p_quota_metric_key
           and q.enabled = true
           and (
                (q.scope_type = 'platform' and q.scope_id is null)
             or (q.scope_type = 'user' and q.scope_id = p_user_id)
             or (q.scope_type = 'workspace' and p_workspace_id is not null and q.scope_id = p_workspace_id)
             or (q.scope_type = 'partner' and p_partner_id is not null and q.scope_id = p_partner_id)
           )
         order by q.id
         for update
    loop
        v_window_start := pg_catalog.to_timestamp(
            pg_catalog.floor(extract(epoch from now()) / v_policy.window_seconds)
            * v_policy.window_seconds
        );

        -- Serialize creation/update for the same policy window, including platform scope_id NULL.
        perform pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtext(v_policy.id::text),
            pg_catalog.hashtext(v_window_start::text)
        );

        select *
          into v_usage
          from public.quota_usage
         where policy_id = v_policy.id
           and scope_type = v_policy.scope_type
           and scope_id is not distinct from v_policy.scope_id
           and metric_key = v_policy.metric_key
           and window_start = v_window_start
         for update;

        if not found then
            insert into public.quota_usage (
                policy_id, scope_type, scope_id, metric_key, window_start, used_value
            ) values (
                v_policy.id, v_policy.scope_type, v_policy.scope_id,
                v_policy.metric_key, v_window_start, 0
            )
            returning * into v_usage;
        end if;

        if v_usage.used_value + p_quota_amount > v_policy.limit_value then
            raise exception 'quota exceeded for metric %', p_quota_metric_key using errcode = '54000';
        end if;

        update public.quota_usage
           set used_value = used_value + p_quota_amount,
               updated_at = now()
         where id = v_usage.id;

        v_applied := v_applied || pg_catalog.jsonb_build_array(
            pg_catalog.jsonb_build_object(
                'policy_id', v_policy.id,
                'scope_type', v_policy.scope_type,
                'metric_key', v_policy.metric_key,
                'window_start', v_window_start,
                'limit_value', v_policy.limit_value,
                'used_value', v_usage.used_value + p_quota_amount
            )
        );
    end loop;

    if pg_catalog.jsonb_array_length(v_applied) = 0 then
        raise exception 'no applicable quota policy' using errcode = '55000';
    end if;

    v_reservation := public.moreai_credit_reserve(
        p_wallet_id,
        p_user_id,
        p_credit_amount,
        p_reservation_key,
        p_run_id,
        900
    );

    perform public.moreai_llm_set_reservation(
        p_request_id,
        (v_reservation ->> 'reservation_id')::uuid,
        p_estimated_cost
    );

    return pg_catalog.jsonb_build_object(
        'request_id', p_request_id,
        'reservation_id', v_reservation ->> 'reservation_id',
        'quota', v_applied,
        'status', 'reserved'
    );
end;
$function$;

revoke all on function public.moreai_llm_reserve_request(uuid, uuid, uuid, uuid, numeric, numeric, text, text, text, numeric, uuid, uuid) from public;
revoke all on function public.moreai_llm_reserve_request(uuid, uuid, uuid, uuid, numeric, numeric, text, text, text, numeric, uuid, uuid) from anon;
revoke all on function public.moreai_llm_reserve_request(uuid, uuid, uuid, uuid, numeric, numeric, text, text, text, numeric, uuid, uuid) from authenticated;
grant execute on function public.moreai_llm_reserve_request(uuid, uuid, uuid, uuid, numeric, numeric, text, text, text, numeric, uuid, uuid) to service_role;
