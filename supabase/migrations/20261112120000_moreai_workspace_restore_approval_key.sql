-- Align the persisted approval allowlist with the canonical OpenManus runtime tool keys.
-- Additive/forward-only: preserve existing aliases and all approval/RLS behavior.
alter table public.agent_tool_approvals
  drop constraint if exists agent_tool_approvals_tool_key_check;

alter table public.agent_tool_approvals
  add constraint agent_tool_approvals_tool_key_check
  check (tool_key in (
    'bash','python_execute','browser_use','planning_step',
    'browser','file_read','file_write','file_edit','workspace_restore_version'
  ));

create or replace function public.moreai_request_tool_approval(
  p_run_id uuid, p_user_id uuid, p_tool_key text, p_arguments_hash text,
  p_summary text, p_expires_in_seconds integer default 900
) returns uuid
language plpgsql security definer set search_path = public, pg_temp
as $$
declare v_id uuid;
begin
  if p_tool_key not in (
       'bash','python_execute','browser_use','planning_step',
       'browser','file_read','file_write','file_edit'
     )
     or p_arguments_hash !~ '^[0-9a-f]{64}$'
     or p_expires_in_seconds < 60 or p_expires_in_seconds > 3600
     or char_length(p_summary) not between 1 and 1000 then
    raise exception 'invalid_tool_approval_request' using errcode = '22023';
  end if;
  if not exists (
    select 1 from public.agent_runs r
    where r.id=p_run_id and r.user_id=p_user_id
  ) then
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

revoke all on function public.moreai_request_tool_approval(uuid,uuid,text,text,text,integer)
  from public, anon, authenticated;
grant execute on function public.moreai_request_tool_approval(uuid,uuid,text,text,text,integer)
  to service_role;
