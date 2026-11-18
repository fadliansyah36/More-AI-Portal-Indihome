create table if not exists public.moreai_connection_actions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  connection_id uuid not null references public.moreai_connections(id) on delete restrict,
  provider text not null check(provider='google'),
  action_type text not null check(action_type in ('gmail.send','calendar.create')),
  idempotency_key text not null check(length(idempotency_key) between 12 and 128),
  payload_sha256 text not null check(payload_sha256 ~ '^[0-9a-f]{64}$'),
  status text not null default 'started' check(status in ('started','completed','unknown','failed')),
  provider_resource_id text,
  result_metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id,idempotency_key)
);
create index if not exists moreai_connection_actions_connection_idx
 on public.moreai_connection_actions(connection_id,created_at desc);
alter table public.moreai_connection_actions enable row level security;
revoke all on public.moreai_connection_actions from public,anon,authenticated;
grant select,insert,update on public.moreai_connection_actions to service_role;
drop policy if exists moreai_connection_actions_server_only on public.moreai_connection_actions;
create policy moreai_connection_actions_server_only on public.moreai_connection_actions for all to anon,authenticated using(false) with check(false);

create or replace function public.moreai_begin_connection_action(
 p_user_id uuid,p_connection_id uuid,p_action_type text,p_idempotency_key text,p_payload_sha256 text
) returns jsonb language plpgsql security definer set search_path=''
as $function$
declare v_action public.moreai_connection_actions%rowtype; v_inserted integer;
begin
 if p_action_type not in ('gmail.send','calendar.create') or
    p_idempotency_key is null or length(p_idempotency_key) not between 12 and 128 or
    p_payload_sha256 !~ '^[0-9a-f]{64}$' then
  raise exception 'connection_action_payload_invalid' using errcode='22023';
 end if;
 if not exists(select 1 from public.moreai_connections where id=p_connection_id and user_id=p_user_id and provider='google' and status='connected') then
  raise exception 'connection_not_found' using errcode='42501';
 end if;
 insert into public.moreai_connection_actions(user_id,connection_id,provider,action_type,idempotency_key,payload_sha256,status)
 values(p_user_id,p_connection_id,'google',p_action_type,p_idempotency_key,p_payload_sha256,'started')
 on conflict(user_id,idempotency_key) do nothing;
 get diagnostics v_inserted = row_count;
 select * into v_action from public.moreai_connection_actions
  where user_id=p_user_id and idempotency_key=p_idempotency_key for update;
 if v_action.connection_id<>p_connection_id or v_action.action_type<>p_action_type or v_action.payload_sha256<>p_payload_sha256 then
  raise exception 'connection_action_idempotency_conflict' using errcode='22023';
 end if;
 if v_inserted=0 or v_action.status<>'started' then
  return jsonb_build_object('action_id',v_action.id,'status',v_action.status,'replay',true,
   'provider_resource_id',v_action.provider_resource_id,'result_metadata',v_action.result_metadata);
 end if;
 return jsonb_build_object('action_id',v_action.id,'status',v_action.status,'replay',false);
end;
$function$;
revoke all on function public.moreai_begin_connection_action(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.moreai_begin_connection_action(uuid,uuid,text,text,text) to service_role;

create or replace function public.moreai_finish_connection_action(
 p_action_id uuid,p_user_id uuid,p_status text,p_provider_resource_id text,p_result_metadata jsonb
) returns jsonb language plpgsql security definer set search_path=''
as $function$
declare v_action public.moreai_connection_actions%rowtype;
begin
 if p_status not in ('completed','unknown','failed') or jsonb_typeof(p_result_metadata)<>'object' then
  raise exception 'connection_action_result_invalid' using errcode='22023';
 end if;
 update public.moreai_connection_actions set status=p_status,
  provider_resource_id=left(p_provider_resource_id,512),result_metadata=p_result_metadata,updated_at=now()
 where id=p_action_id and user_id=p_user_id and status='started'
 returning * into v_action;
 if not found then raise exception 'connection_action_not_pending' using errcode='40001'; end if;
 insert into public.moreai_connection_audit(connection_id,user_id,provider,event_type,scopes,detail)
 values(v_action.connection_id,p_user_id,'google',
  case when p_status='completed' then 'action_completed' when p_status='failed' then 'action_failed' else 'action_requested' end,
  '[]'::jsonb,jsonb_build_object('action_id',v_action.id,'action_type',v_action.action_type,'status',p_status));
 return jsonb_build_object('action_id',v_action.id,'status',v_action.status,'provider_resource_id',v_action.provider_resource_id);
end;
$function$;
revoke all on function public.moreai_finish_connection_action(uuid,uuid,text,text,jsonb) from public,anon,authenticated;
grant execute on function public.moreai_finish_connection_action(uuid,uuid,text,text,jsonb) to service_role;
