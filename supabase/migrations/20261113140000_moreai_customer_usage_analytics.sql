-- Phase 09: server-side historical usage aggregation for the Customer Analytics view.
-- Forward-only, additive, and scoped to a user ID supplied only by the trusted FastAPI boundary.

create or replace function public.moreai_customer_usage_analytics(
  p_user_id uuid,
  p_since timestamptz,
  p_until timestamptz
)
returns jsonb
language sql
stable
security invoker
set search_path = ''
as $function$
  with scoped as (
    select
      model_key,
      provider_key,
      status,
      input_tokens,
      output_tokens,
      coalesce(actual_cost, estimated_cost, 0) as cost,
      latency_ms,
      created_at
    from public.llm_usage
    where user_id = p_user_id
      and created_at >= p_since
      and created_at < p_until
  ),
  summary as (
    select
      count(*)::bigint as total_requests,
      coalesce(sum(input_tokens + output_tokens), 0)::bigint as total_tokens,
      count(*) filter (where status in ('succeeded', 'completed'))::bigint as successful_requests,
      count(*) filter (where status in ('failed', 'error'))::bigint as failed_requests,
      coalesce(sum(cost), 0)::numeric as total_cost,
      coalesce(round(avg(latency_ms)) filter (where latency_ms is not null), 0)::bigint as average_latency_ms
    from scoped
  ),
  model_rows as (
    select
      model_key,
      provider_key,
      count(*)::bigint as requests,
      coalesce(sum(input_tokens + output_tokens), 0)::bigint as tokens,
      count(*) filter (where status in ('succeeded', 'completed'))::bigint as successful_requests,
      coalesce(sum(cost), 0)::numeric as cost
    from scoped
    group by model_key, provider_key
  ),
  day_rows as (
    select
      date_trunc('day', created_at) as day,
      count(*)::bigint as requests,
      coalesce(sum(input_tokens + output_tokens), 0)::bigint as tokens,
      coalesce(sum(cost), 0)::numeric as cost
    from scoped
    group by date_trunc('day', created_at)
  )
  select jsonb_build_object(
    'summary', (select to_jsonb(summary) from summary),
    'by_model', coalesce((
      select jsonb_agg(to_jsonb(model_rows) order by requests desc, model_key asc)
      from model_rows
    ), '[]'::jsonb),
    'by_day', coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'day', day::date,
          'requests', requests,
          'tokens', tokens,
          'cost', cost
        ) order by day asc
      )
      from day_rows
    ), '[]'::jsonb),
    'period', jsonb_build_object('since', p_since, 'until', p_until)
  );
$function$;

revoke all on function public.moreai_customer_usage_analytics(uuid, timestamptz, timestamptz) from public;
revoke all on function public.moreai_customer_usage_analytics(uuid, timestamptz, timestamptz) from anon;
revoke all on function public.moreai_customer_usage_analytics(uuid, timestamptz, timestamptz) from authenticated;
grant execute on function public.moreai_customer_usage_analytics(uuid, timestamptz, timestamptz) to service_role;
