create or replace function public.moreai_workspace_claim_chat_idempotency(
 p_scope_key text,p_idempotency_key text,p_request_hash text,p_expires_at timestamptz
) returns jsonb language plpgsql security invoker set search_path=public,pg_temp as $$
declare v_row public.idempotency_keys%rowtype;
begin
 if coalesce(p_scope_key,'')='' or coalesce(p_idempotency_key,'')='' or length(p_idempotency_key)>200
  or coalesce(p_request_hash,'')='' or p_expires_at<=now() then
  raise exception using errcode='22023',message='CHAT_IDEMPOTENCY_INVALID';
 end if;
 insert into public.idempotency_keys(scope_key,idempotency_key,request_hash,status,expires_at)
 values(p_scope_key,p_idempotency_key,p_request_hash,'processing',p_expires_at)
 on conflict(scope_key,idempotency_key) do update
  set request_hash=excluded.request_hash,status='processing',response_status=null,response_body=null,
      expires_at=excluded.expires_at,updated_at=now()
  where public.idempotency_keys.expires_at<=now() or public.idempotency_keys.status='failed'
 returning * into v_row;
 if found then return jsonb_build_object('state','claimed'); end if;
 select * into v_row from public.idempotency_keys
  where scope_key=p_scope_key and idempotency_key=p_idempotency_key for update;
 if not found then raise exception using errcode='40001',message='CHAT_IDEMPOTENCY_RETRY'; end if;
 if v_row.request_hash<>p_request_hash then return jsonb_build_object('state','conflict'); end if;
 if v_row.status='completed' then
  return jsonb_build_object('state','completed','response_status',v_row.response_status,'response_body',v_row.response_body);
 end if;
 return jsonb_build_object('state','processing');
end; $$;

create or replace function public.moreai_workspace_finish_chat_idempotency(
 p_scope_key text,p_idempotency_key text,p_request_hash text,p_response_body jsonb,p_success boolean default true
) returns boolean language plpgsql security invoker set search_path=public,pg_temp as $$
declare v_updated integer;
begin
 update public.idempotency_keys
 set status=case when p_success then 'completed' else 'failed' end,
     response_status=case when p_success then 200 else null end,
     response_body=case when p_success then p_response_body else null end,
     updated_at=now()
 where scope_key=p_scope_key and idempotency_key=p_idempotency_key
   and request_hash=p_request_hash and status='processing';
 get diagnostics v_updated=row_count;
 return v_updated=1;
end; $$;

revoke all on function public.moreai_workspace_claim_chat_idempotency(text,text,text,timestamptz) from public,anon,authenticated;
grant execute on function public.moreai_workspace_claim_chat_idempotency(text,text,text,timestamptz) to service_role;
revoke all on function public.moreai_workspace_finish_chat_idempotency(text,text,text,jsonb,boolean) from public,anon,authenticated;
grant execute on function public.moreai_workspace_finish_chat_idempotency(text,text,text,jsonb,boolean) to service_role;