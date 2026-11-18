-- Extend the existing idempotent connection action ledger for Calendar event mutations.
-- Forward-only source migration; intentionally not applied to the connected Supabase project.
alter table public.moreai_connection_actions
  drop constraint if exists moreai_connection_actions_action_type_check;

alter table public.moreai_connection_actions
  add constraint moreai_connection_actions_action_type_check
  check (action_type in ('gmail.send','calendar.create','calendar.update','calendar.delete'));

create or replace function public.moreai_begin_connection_action(
 p_user_id uuid,p_connection_id uuid,p_action_type text,p_idempotency_key text,p_payload_sha256 text
) returns jsonb language plpgsql security definer set search_path=''
as $function$
declare v_action public.moreai_connection_actions%rowtype; v_inserted integer;
begin
 if p_action_type not in ('gmail.send','calendar.create','calendar.update','calendar.delete') or
    p_idempotency_key is null or length(p_idempotency_key) not between 12 and 128 or
    p_payload_sha256 !~ '^[0-9a-f]{64}$' then
  raise exception 'connection_action_payload_invalid' using errcode='22023';
 end if;
 if not exists(
   select 1 from public.moreai_connections
   where id=p_connection_id and user_id=p_user_id and provider='google' and status='connected'
 ) then
  raise exception 'connection_not_found' using errcode='42501';
 end if;
 insert into public.moreai_connection_actions(
   user_id,connection_id,provider,action_type,idempotency_key,payload_sha256,status
 ) values(
   p_user_id,p_connection_id,'google',p_action_type,p_idempotency_key,p_payload_sha256,'started'
 )
 on conflict(user_id,idempotency_key) do nothing;
 get diagnostics v_inserted = row_count;
 select * into v_action from public.moreai_connection_actions
  where user_id=p_user_id and idempotency_key=p_idempotency_key for update;
 if v_action.connection_id<>p_connection_id or
    v_action.action_type<>p_action_type or
    v_action.payload_sha256<>p_payload_sha256 then
  raise exception 'connection_action_idempotency_conflict' using errcode='22023';
 end if;
 if v_inserted=0 or v_action.status<>'started' then
  return jsonb_build_object(
   'action_id',v_action.id,'status',v_action.status,'replay',true,
   'provider_resource_id',v_action.provider_resource_id,'result_metadata',v_action.result_metadata
  );
 end if;
 return jsonb_build_object('action_id',v_action.id,'status',v_action.status,'replay',false);
end;
$function$;

revoke all on function public.moreai_begin_connection_action(uuid,uuid,text,text,text) from public,anon,authenticated;
grant execute on function public.moreai_begin_connection_action(uuid,uuid,text,text,text) to service_role;
