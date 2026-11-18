create or replace function public.moreai_workspace_finish_chat_idempotency(
 p_scope_key text,p_idempotency_key text,p_request_hash text,p_response_body jsonb,p_success boolean default true
) returns boolean language plpgsql security invoker set search_path=public,pg_temp as $$
declare v_updated integer;
begin
 update public.idempotency_keys
 set status=case when p_success then 'completed' else 'failed' end,
     response_status=case when p_success then 200 else null end,
     response_body=case when p_success then p_response_body else null end,
     expires_at=case when p_success then now()+interval '24 hours' else now() end,
     updated_at=now()
 where scope_key=p_scope_key and idempotency_key=p_idempotency_key
   and request_hash=p_request_hash and status='processing';
 get diagnostics v_updated=row_count;
 return v_updated=1;
end; $$;