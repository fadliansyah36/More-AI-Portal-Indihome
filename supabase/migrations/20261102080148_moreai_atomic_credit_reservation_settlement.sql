-- Atomic credit reservation and settlement primitives. Service-role only.
create or replace function public.moreai_credit_reserve(
 p_wallet_id uuid, p_user_id uuid, p_amount numeric, p_idempotency_key text,
 p_run_id uuid default null, p_ttl_seconds integer default 900
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare w public.wallet_accounts%rowtype; r public.credit_reservations%rowtype; next_balance numeric(20,6);
begin
 if p_amount <= 0 or p_ttl_seconds < 1 or p_ttl_seconds > 86400 then raise exception 'invalid reservation amount or ttl'; end if;
 select * into r from public.credit_reservations where idempotency_key=p_idempotency_key for update;
 if found then
  if r.wallet_id<>p_wallet_id or r.user_id<>p_user_id or r.amount<>p_amount then raise exception 'idempotency conflict'; end if;
  return jsonb_build_object('reservation_id',r.id,'status',r.status,'amount',r.amount,'expires_at',r.expires_at);
 end if;
 select * into w from public.wallet_accounts where id=p_wallet_id for update;
 if not found or w.status<>'active' then raise exception 'wallet unavailable'; end if;
 if w.owner_type='user' and w.owner_id<>p_user_id then raise exception 'wallet ownership mismatch'; end if;
 if w.balance < p_amount then raise exception 'insufficient credits'; end if;
 next_balance := w.balance-p_amount;
 update public.wallet_accounts set balance=next_balance,updated_at=now() where id=w.id;
 insert into public.credit_reservations(wallet_id,user_id,run_id,amount,status,idempotency_key,expires_at)
 values(p_wallet_id,p_user_id,p_run_id,p_amount,'reserved',p_idempotency_key,now()+make_interval(secs=>p_ttl_seconds)) returning * into r;
 insert into public.credit_ledger(wallet_id,entry_type,amount,balance_after,reference_type,reference_id,idempotency_key,description,created_by)
 values(p_wallet_id,'reserve',-p_amount,next_balance,'reservation',r.id,'reserve:'||p_idempotency_key,'Credit reservation',p_user_id);
 return jsonb_build_object('reservation_id',r.id,'status',r.status,'amount',r.amount,'expires_at',r.expires_at,'balance',next_balance);
end $$;

create or replace function public.moreai_credit_settle(
 p_reservation_id uuid, p_actual_amount numeric, p_idempotency_key text
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r public.credit_reservations%rowtype; w public.wallet_accounts%rowtype;
 delta numeric(20,6); next_balance numeric(20,6);
begin
 if p_actual_amount < 0 then raise exception 'invalid settlement amount'; end if;
 select * into r from public.credit_reservations where id=p_reservation_id for update;
 if not found then raise exception 'reservation not found'; end if;
 if r.status='settled' then
  if r.settled_amount<>p_actual_amount then raise exception 'settlement idempotency conflict'; end if;
  return jsonb_build_object('reservation_id',r.id,'status',r.status,'settled_amount',r.settled_amount);
 end if;
 if r.status<>'reserved' then raise exception 'reservation is not active'; end if;
 select * into w from public.wallet_accounts where id=r.wallet_id for update;
 if not found then raise exception 'wallet not found'; end if;
 delta := r.amount-p_actual_amount;
 if delta < 0 then
  if w.balance < abs(delta) then raise exception 'insufficient balance for settlement overage'; end if;
  next_balance := w.balance-abs(delta);
  update public.wallet_accounts set balance=next_balance,updated_at=now() where id=w.id;
  insert into public.credit_ledger(wallet_id,entry_type,amount,balance_after,reference_type,reference_id,idempotency_key,description,created_by)
  values(w.id,'consume',delta,next_balance,'reservation',r.id,'settle-extra:'||p_idempotency_key,'Settlement overage',r.user_id);
 elsif delta > 0 then
  next_balance := w.balance+delta;
  update public.wallet_accounts set balance=next_balance,updated_at=now() where id=w.id;
  insert into public.credit_ledger(wallet_id,entry_type,amount,balance_after,reference_type,reference_id,idempotency_key,description,created_by)
  values(w.id,'release',delta,next_balance,'reservation',r.id,'settle-release:'||p_idempotency_key,'Unused reservation released',r.user_id);
 else next_balance := w.balance;
 end if;
 update public.credit_reservations set status='settled',settled_amount=p_actual_amount,settled_at=now() where id=r.id;
 insert into public.outbox_events(aggregate_type,aggregate_id,event_type,payload)
 values('credit_reservation',r.id,'credit.settled',jsonb_build_object('reservation_id',r.id,'wallet_id',w.id,'user_id',r.user_id,'amount',p_actual_amount));
 return jsonb_build_object('reservation_id',r.id,'status','settled','settled_amount',p_actual_amount,'balance',next_balance);
end $$;

create or replace function public.moreai_credit_release(
 p_reservation_id uuid, p_idempotency_key text
) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare r public.credit_reservations%rowtype; w public.wallet_accounts%rowtype; next_balance numeric(20,6);
begin
 select * into r from public.credit_reservations where id=p_reservation_id for update;
 if not found then raise exception 'reservation not found'; end if;
 if r.status='released' then return jsonb_build_object('reservation_id',r.id,'status',r.status); end if;
 if r.status<>'reserved' then raise exception 'reservation is not active'; end if;
 select * into w from public.wallet_accounts where id=r.wallet_id for update;
 next_balance := w.balance+r.amount;
 update public.wallet_accounts set balance=next_balance,updated_at=now() where id=w.id;
 update public.credit_reservations set status='released',settled_amount=0,settled_at=now() where id=r.id;
 insert into public.credit_ledger(wallet_id,entry_type,amount,balance_after,reference_type,reference_id,idempotency_key,description,created_by)
 values(w.id,'release',r.amount,next_balance,'reservation',r.id,'release:'||p_idempotency_key,'Reservation released',r.user_id);
 insert into public.outbox_events(aggregate_type,aggregate_id,event_type,payload)
 values('credit_reservation',r.id,'credit.released',jsonb_build_object('reservation_id',r.id,'wallet_id',w.id,'user_id',r.user_id,'amount',r.amount));
 return jsonb_build_object('reservation_id',r.id,'status','released','balance',next_balance);
end $$;

revoke all on function public.moreai_credit_reserve(uuid,uuid,numeric,text,uuid,integer) from public,anon,authenticated;
revoke all on function public.moreai_credit_settle(uuid,numeric,text) from public,anon,authenticated;
revoke all on function public.moreai_credit_release(uuid,text) from public,anon,authenticated;
grant execute on function public.moreai_credit_reserve(uuid,uuid,numeric,text,uuid,integer) to service_role;
grant execute on function public.moreai_credit_settle(uuid,numeric,text) to service_role;
grant execute on function public.moreai_credit_release(uuid,text) to service_role;
