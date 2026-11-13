-- Phase 09: database-side keyset pagination for the union of owned and shared Customer workspaces.
-- The FastAPI Customer boundary supplies the authenticated user id; only service_role may execute this RPC.

create or replace function public.moreai_customer_workspaces_page(
  p_user_id uuid,
  p_limit integer default 50,
  p_cursor_updated_at timestamptz default null,
  p_cursor_id uuid default null
)
returns table (
  id uuid,
  name text,
  slug text,
  owner_user_id uuid,
  status text,
  created_at timestamptz,
  updated_at timestamptz
)
language plpgsql
stable
security invoker
set search_path = ''
as $function$
declare
  v_limit integer := least(greatest(coalesce(p_limit, 50), 1), 100);
begin
  if p_user_id is null then
    raise exception 'customer_user_id_required' using errcode = '22023';
  end if;

  if (p_cursor_updated_at is null) <> (p_cursor_id is null) then
    raise exception 'pagination_cursor_invalid' using errcode = '22023';
  end if;

  return query
  with accessible_workspace_ids as (
    select w.id
    from public.workspaces as w
    where w.owner_user_id = p_user_id
      and w.status = 'active'

    union

    select w.id
    from public.workspace_members as wm
    join public.workspaces as w on w.id = wm.workspace_id
    where wm.user_id = p_user_id
      and wm.status = 'active'
      and w.status = 'active'
  )
  select
    w.id,
    w.name,
    w.slug,
    w.owner_user_id,
    w.status,
    w.created_at,
    w.updated_at
  from public.workspaces as w
  join accessible_workspace_ids as accessible on accessible.id = w.id
  where p_cursor_updated_at is null
     or (w.updated_at, w.id) < (p_cursor_updated_at, p_cursor_id)
  order by w.updated_at desc, w.id desc
  limit (v_limit + 1);
end;
$function$;

revoke all on function public.moreai_customer_workspaces_page(uuid, integer, timestamptz, uuid) from public;
revoke all on function public.moreai_customer_workspaces_page(uuid, integer, timestamptz, uuid) from anon;
revoke all on function public.moreai_customer_workspaces_page(uuid, integer, timestamptz, uuid) from authenticated;
grant execute on function public.moreai_customer_workspaces_page(uuid, integer, timestamptz, uuid) to service_role;
