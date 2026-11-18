create table if not exists public.llm_request_records (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null,
 run_id uuid references public.agent_runs(id) on delete set null,
 idempotency_key text not null,
 request_hash text not null,
 status text not null default 'processing' check(status in ('processing','provider_succeeded','succeeded','failed','unknown')),
 reservation_id uuid references public.credit_reservations(id),
 provider_key text,
 model_key text,
 response_text text,
 input_tokens integer not null default 0,
 output_tokens integer not null default 0,
 estimated_cost numeric not null default 0,
 actual_cost numeric,
 latency_ms integer,
 error_code text,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(user_id,idempotency_key)
);
create index if not exists llm_request_reconcile_idx on public.llm_request_records(status,updated_at) where status='provider_succeeded';
alter table public.llm_request_records enable row level security;
revoke all on public.llm_request_records from anon,authenticated;
grant select,insert,update,delete on public.llm_request_records to service_role;
alter table public.llm_usage add column if not exists reservation_id uuid references public.credit_reservations(id);
alter table public.llm_usage add column if not exists provider_response_id text;

create or replace function public.moreai_llm_claim_request(p_user_id uuid,p_run_id uuid,p_idempotency_key text,p_request_hash text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.llm_request_records%rowtype; created boolean:=false;
begin
 if p_idempotency_key is null or length(p_idempotency_key)<8 or length(p_idempotency_key)>200 or p_request_hash is null or length(p_request_hash)<>64 then raise exception 'invalid llm idempotency claim'; end if;
 insert into public.llm_request_records(user_id,run_id,idempotency_key,request_hash)
 values(p_user_id,p_run_id,p_idempotency_key,p_request_hash)
 on conflict(user_id,idempotency_key) do nothing returning * into r;
 if found then created:=true;
 else
  select * into r from public.llm_request_records where user_id=p_user_id and idempotency_key=p_idempotency_key for update;
  if r.request_hash<>p_request_hash then raise exception 'idempotency key reused with different request'; end if;
 end if;
 return jsonb_build_object('created',created,'id',r.id,'status',r.status,'reservation_id',r.reservation_id,'response_text',r.response_text,'provider_key',r.provider_key,'model_key',r.model_key,'input_tokens',r.input_tokens,'output_tokens',r.output_tokens,'actual_cost',r.actual_cost,'error_code',r.error_code);
end $$;

create or replace function public.moreai_llm_set_reservation(p_request_id uuid,p_reservation_id uuid,p_estimated_cost numeric)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.llm_request_records%rowtype;
begin
 update public.llm_request_records set reservation_id=coalesce(reservation_id,p_reservation_id),estimated_cost=p_estimated_cost,updated_at=now()
 where id=p_request_id and status='processing' returning * into r;
 if not found then select * into r from public.llm_request_records where id=p_request_id; end if;
 if r.reservation_id is distinct from p_reservation_id then raise exception 'reservation mismatch'; end if;
 return jsonb_build_object('id',r.id,'reservation_id',r.reservation_id,'status',r.status);
end $$;

create or replace function public.moreai_llm_mark_provider_result(
 p_request_id uuid,p_provider_key text,p_model_key text,p_response_text text,
 p_input_tokens integer,p_output_tokens integer,p_actual_cost numeric,p_latency_ms integer,p_provider_response_id text default null
) returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.llm_request_records%rowtype;
begin
 if p_input_tokens<0 or p_output_tokens<0 or p_actual_cost<0 or p_latency_ms<0 then raise exception 'invalid provider usage'; end if;
 update public.llm_request_records set status='provider_succeeded',provider_key=p_provider_key,model_key=p_model_key,
 response_text=p_response_text,input_tokens=p_input_tokens,output_tokens=p_output_tokens,
 actual_cost=p_actual_cost,latency_ms=p_latency_ms,updated_at=now()
 where id=p_request_id and status in ('processing','provider_succeeded') returning * into r;
 if not found then select * into r from public.llm_request_records where id=p_request_id; end if;
 if r.status not in ('provider_succeeded','succeeded') then raise exception 'request cannot accept provider result'; end if;
 return jsonb_build_object('id',r.id,'status',r.status);
end $$;

create or replace function public.moreai_llm_finalize_request(p_request_id uuid,p_actual_credits numeric,p_settlement_key text,p_provider_response_id text default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.llm_request_records%rowtype; u public.llm_usage%rowtype;
begin
 select * into r from public.llm_request_records where id=p_request_id for update;
 if not found then raise exception 'llm request not found'; end if;
 if r.status='succeeded' then return jsonb_build_object('id',r.id,'status','succeeded','response_text',r.response_text); end if;
 if r.status<>'provider_succeeded' or r.reservation_id is null then raise exception 'llm request is not ready for settlement'; end if;
 perform public.moreai_credit_settle(r.reservation_id,p_actual_credits,p_settlement_key);
 insert into public.llm_usage(user_id,run_id,provider_key,model_key,request_id,input_tokens,output_tokens,estimated_cost,actual_cost,status,idempotency_key,latency_ms,reservation_id,provider_response_id)
 values(r.user_id,r.run_id,r.provider_key,r.model_key,r.id::text,r.input_tokens,r.output_tokens,r.estimated_cost,r.actual_cost,'succeeded',r.idempotency_key,r.latency_ms,r.reservation_id,p_provider_response_id)
 on conflict(user_id,idempotency_key) do nothing;
 update public.llm_request_records set status='succeeded',updated_at=now() where id=r.id;
 return jsonb_build_object('id',r.id,'status','succeeded','response_text',r.response_text);
end $$;

create or replace function public.moreai_llm_fail_request(p_request_id uuid,p_error_code text,p_release boolean default true,p_release_key text default null)
returns jsonb language plpgsql security definer set search_path='' as $$
declare r public.llm_request_records%rowtype;
begin
 select * into r from public.llm_request_records where id=p_request_id for update;
 if not found then raise exception 'llm request not found'; end if;
 if r.status in ('succeeded','failed') then return jsonb_build_object('id',r.id,'status',r.status); end if;
 if p_release and r.reservation_id is not null then
  perform public.moreai_credit_release(r.reservation_id,coalesce(p_release_key,'llm-release:'||r.id::text));
  update public.llm_request_records set status='failed',error_code=p_error_code,updated_at=now() where id=r.id;
 else
  update public.llm_request_records set status='unknown',error_code=p_error_code,updated_at=now() where id=r.id;
 end if;
 return jsonb_build_object('id',r.id,'status',case when p_release then 'failed' else 'unknown' end);
end $$;

revoke all on function public.moreai_llm_claim_request(uuid,uuid,text,text) from public,anon,authenticated;
revoke all on function public.moreai_llm_set_reservation(uuid,uuid,numeric) from public,anon,authenticated;
revoke all on function public.moreai_llm_mark_provider_result(uuid,text,text,text,integer,integer,numeric,integer,text) from public,anon,authenticated;
revoke all on function public.moreai_llm_finalize_request(uuid,numeric,text,text) from public,anon,authenticated;
revoke all on function public.moreai_llm_fail_request(uuid,text,boolean,text) from public,anon,authenticated;
grant execute on function public.moreai_llm_claim_request(uuid,uuid,text,text) to service_role;
grant execute on function public.moreai_llm_set_reservation(uuid,uuid,numeric) to service_role;
grant execute on function public.moreai_llm_mark_provider_result(uuid,text,text,text,integer,integer,numeric,integer,text) to service_role;
grant execute on function public.moreai_llm_finalize_request(uuid,numeric,text,text) to service_role;
grant execute on function public.moreai_llm_fail_request(uuid,text,boolean,text) to service_role;