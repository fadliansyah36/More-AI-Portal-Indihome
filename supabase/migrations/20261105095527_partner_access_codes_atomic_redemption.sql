-- MoreAI Phase 02: partner QR/access-code persistence and atomic redemption.
create table if not exists public.partner_access_codes (
  id uuid primary key default gen_random_uuid(),
  partner_id uuid not null references public.partner_organizations(id) on delete restrict,
  location_id uuid references public.partner_locations(id) on delete restrict,
  network_id uuid references public.partner_networks(id) on delete restrict,
  campaign_id uuid references public.partner_campaigns(id) on delete restrict,
  reward_id uuid references public.campaign_rewards(id) on delete restrict,
  code_hash text not null unique check (code_hash ~ '^[0-9a-f]{64}$'),
  status text not null default 'active' check (status in ('active','revoked','exhausted','expired')),
  expires_at timestamptz not null,
  max_redemptions integer not null default 1 check (max_redemptions between 1 and 100000),
  redemption_count integer not null default 0 check (redemption_count >= 0 and redemption_count <= max_redemptions),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  revoked_at timestamptz,
  constraint partner_access_code_scope_check check (network_id is null or location_id is not null),
  constraint partner_access_code_expiry_check check (expires_at > created_at)
);
create index if not exists partner_access_codes_partner_created_idx on public.partner_access_codes(partner_id, created_at desc);
create index if not exists partner_access_codes_active_expiry_idx on public.partner_access_codes(expires_at) where status = 'active';
create table if not exists public.partner_access_code_redemptions (
  id uuid primary key default gen_random_uuid(),
  access_code_id uuid not null references public.partner_access_codes(id) on delete restrict,
  user_id uuid not null references auth.users(id) on delete restrict,
  network_id uuid not null references public.partner_networks(id) on delete restrict,
  verification_session_id uuid not null references public.network_verification_sessions(id) on delete restrict,
  idempotency_key text not null check (length(idempotency_key) between 8 and 160),
  redeemed_at timestamptz not null default now(),
  unique(user_id, idempotency_key)
);
create index if not exists partner_access_code_redemptions_code_idx on public.partner_access_code_redemptions(access_code_id, redeemed_at desc);
alter table public.partner_access_codes enable row level security;
alter table public.partner_access_code_redemptions enable row level security;
revoke all on public.partner_access_codes, public.partner_access_code_redemptions from anon, authenticated;
grant select, insert, update on public.partner_access_codes to service_role;
grant select, insert on public.partner_access_code_redemptions to service_role;
create or replace function public.moreai_redeem_partner_access_code(p_code_hash text,p_user_id uuid,p_network_id uuid,p_verification_session_id uuid,p_idempotency_key text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare v_code public.partner_access_codes%rowtype; v_verification public.network_verification_sessions%rowtype; v_redemption public.partner_access_code_redemptions%rowtype; v_now timestamptz := now();
begin
 if p_code_hash !~ '^[0-9a-f]{64}$' or length(p_idempotency_key) not between 8 and 160 then raise exception using errcode='22023',message='ACCESS_CODE_INVALID'; end if;
 select * into v_verification from public.network_verification_sessions where id=p_verification_session_id and user_id=p_user_id and network_id=p_network_id and status='verified' and expires_at>v_now and ended_at is null;
 if not found then raise exception using errcode='42501',message='NETWORK_VERIFICATION_REQUIRED'; end if;
 select * into v_code from public.partner_access_codes where code_hash=p_code_hash for update;
 if not found or v_code.status<>'active' then raise exception using errcode='P0002',message='ACCESS_CODE_NOT_AVAILABLE'; end if;
 if v_code.expires_at<=v_now then update public.partner_access_codes set status='expired' where id=v_code.id; raise exception using errcode='P0002',message='ACCESS_CODE_EXPIRED'; end if;
 if v_code.redemption_count>=v_code.max_redemptions then update public.partner_access_codes set status='exhausted' where id=v_code.id; raise exception using errcode='P0002',message='ACCESS_CODE_EXHAUSTED'; end if;
 if v_code.network_id is not null and v_code.network_id<>p_network_id then raise exception using errcode='42501',message='ACCESS_CODE_NETWORK_MISMATCH'; end if;
 if v_code.location_id is not null and not exists(select 1 from public.partner_networks n where n.id=p_network_id and n.location_id=v_code.location_id and n.partner_id=v_code.partner_id) then raise exception using errcode='42501',message='ACCESS_CODE_SCOPE_MISMATCH'; end if;
 select * into v_redemption from public.partner_access_code_redemptions where user_id=p_user_id and idempotency_key=p_idempotency_key;
 if found then if v_redemption.access_code_id<>v_code.id then raise exception using errcode='23505',message='IDEMPOTENCY_KEY_CONFLICT'; end if; return jsonb_build_object('redemption_id',v_redemption.id,'replayed',true,'redeemed_at',v_redemption.redeemed_at); end if;
 insert into public.partner_access_code_redemptions(access_code_id,user_id,network_id,verification_session_id,idempotency_key) values(v_code.id,p_user_id,p_network_id,p_verification_session_id,p_idempotency_key) returning * into v_redemption;
 update public.partner_access_codes set redemption_count=redemption_count+1,status=case when redemption_count+1>=max_redemptions then 'exhausted' else 'active' end where id=v_code.id;
 if v_code.reward_id is not null then update public.campaign_rewards set quantity_claimed=quantity_claimed+1 where id=v_code.reward_id and (quantity_limit is null or quantity_claimed<quantity_limit); if not found then raise exception using errcode='P0001',message='REWARD_QUOTA_EXHAUSTED'; end if; end if;
 insert into public.admin_audit_logs(actor_user_id,action,resource_type,resource_id,scope_type,scope_id,outcome,metadata) values(p_user_id,'partner.access_code.redeemed','partner_access_code',v_code.id,'partner',v_code.partner_id,'success',jsonb_build_object('network_id',p_network_id,'redemption_id',v_redemption.id));
 return jsonb_build_object('redemption_id',v_redemption.id,'replayed',false,'redeemed_at',v_redemption.redeemed_at,'reward_id',v_code.reward_id,'partner_entitlement_activated',false,'message','Access code redeemed; entitlement activation remains separate.');
end; $$;
revoke all on function public.moreai_redeem_partner_access_code(text,uuid,uuid,uuid,text) from public,anon,authenticated;
grant execute on function public.moreai_redeem_partner_access_code(text,uuid,uuid,uuid,text) to service_role;