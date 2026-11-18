-- Durable, owner-scoped approval lifecycle for isolated OpenManus tools.
-- Service-role only: all decisions are mediated by FastAPI and worker RPCs.
create table if not exists public.agent_tool_approvals (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.agent_runs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  tool_key text not null check (tool_key in ('bash','python_execute','browser','file_read','file_write','file_edit')),
  arguments_hash text not null check (arguments_hash ~ '^[0-9a-f]{64}$'),
  summary text not null check (char_length(summary) between 1 and 1000),
  status text not null default 'pending' check (status in ('pending','approved','denied','expired','consumed')),
  requested_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '15 minutes'),
  decided_at timestamptz,
  decided_by uuid references auth.users(id) on delete set null,
  consumed_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  constraint agent_tool_approvals_expiry_valid check (expires_at > requested_at)
);

create index if not exists agent_tool_approvals_user_status_idx
  on public.agent_tool_approvals(user_id, status, requested_at desc);
create index if not exists agent_tool_approvals_run_idx
  on public.agent_tool_approvals(run_id, tool_key, requested_at desc);
create unique index if not exists agent_tool_approvals_one_pending_idx
  on public.agent_tool_approvals(run_id, tool_key, arguments_hash)
  where status = 'pending';

alter table public.agent_tool_approvals enable row level security;
revoke all on public.agent_tool_approvals from anon, authenticated;
grant all on public.agent_tool_approvals to service_role;

create or replace function public.moreai_request_tool_approval(
  p_run_id uuid, p_user_id uuid, p_tool_key text, p_arguments_hash text,
  p_summary text, p_expires_in_seconds integer default 900
) returns uuid
language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_id uuid;
begin
  if p_tool_key not in ('bash','python_execute','browser','file_read','file_write','file_edit')
     or p_arguments_hash !~ '^[0-9a-f]{64}$'
     or p_expires_in_seconds < 60 or p_expires_in_seconds > 3600
     or char_length(p_summary) not between 1 and 1000 then
    raise exception 'invalid_tool_approval_request' using errcode = '22023';
  end if;
  if not exists (select 1 from public.agent_runs r where r.id=p_run_id and r.user_id=p_user_id) then
    raise exception 'approval_run_owner_mismatch' using errcode = '42501';
  end if;
  update public.agent_tool_approvals
     set status='expired'
   where run_id=p_run_id and tool_key=p_tool_key and arguments_hash=p_arguments_hash
     and status in ('pending','approved') and expires_at <= now();
  select id into v_id from public.agent_tool_approvals
   where run_id=p_run_id and tool_key=p_tool_key and arguments_hash=p_arguments_hash
     and status in ('pending','approved') and expires_at > now()
   order by requested_at desc
   limit 1;
  if v_id is not null then return v_id; end if;
  insert into public.agent_tool_approvals(run_id,user_id,tool_key,arguments_hash,summary,expires_at)
  values(p_run_id,p_user_id,p_tool_key,p_arguments_hash,p_summary,now()+make_interval(secs=>p_expires_in_seconds))
  returning id into v_id;
  return v_id;
end;
$$;

create or replace function public.moreai_decide_tool_approval(
  p_approval_id uuid, p_user_id uuid, p_decision text
) returns jsonb
language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_row public.agent_tool_approvals;
begin
  if p_decision not in ('approved','denied') then
    raise exception 'invalid_approval_decision' using errcode='22023';
  end if;
  update public.agent_tool_approvals
     set status=case when expires_at <= now() then 'expired' else p_decision end,
         decided_at=now(), decided_by=p_user_id
   where id=p_approval_id and user_id=p_user_id and status='pending'
   returning * into v_row;
  if not found then
    select * into v_row from public.agent_tool_approvals where id=p_approval_id and user_id=p_user_id;
    if not found then raise exception 'approval_not_found' using errcode='P0002'; end if;
    raise exception 'approval_not_pending' using errcode='55000';
  end if;
  return jsonb_build_object('id',v_row.id,'run_id',v_row.run_id,'tool_key',v_row.tool_key,
    'status',v_row.status,'decided_at',v_row.decided_at,'expires_at',v_row.expires_at);
end;
$$;

create or replace function public.moreai_consume_tool_approval(
  p_run_id uuid, p_user_id uuid, p_tool_key text, p_arguments_hash text
) returns boolean
language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_id uuid;
begin
  update public.agent_tool_approvals
     set status='consumed', consumed_at=now()
   where id = (
     select id from public.agent_tool_approvals
      where run_id=p_run_id and user_id=p_user_id and tool_key=p_tool_key
        and arguments_hash=p_arguments_hash and status='approved' and expires_at > now()
      order by decided_at desc limit 1 for update skip locked
   )
   returning id into v_id;
  return v_id is not null;
end;
$$;

revoke all on function public.moreai_request_tool_approval(uuid,uuid,text,text,text,integer) from public, anon, authenticated;
revoke all on function public.moreai_decide_tool_approval(uuid,uuid,text) from public, anon, authenticated;
revoke all on function public.moreai_consume_tool_approval(uuid,uuid,text,text) from public, anon, authenticated;
grant execute on function public.moreai_request_tool_approval(uuid,uuid,text,text,text,integer) to service_role;
grant execute on function public.moreai_decide_tool_approval(uuid,uuid,text) to service_role;
grant execute on function public.moreai_consume_tool_approval(uuid,uuid,text,text) to service_role;
