create table if not exists public.network_verification_method_catalog (
  method_key text primary key check (method_key in ('gps','mikrotik_hotspot','radius','gateway','isp_api')),
  display_name text not null,
  adapter_key text not null unique,
  enabled boolean not null default false,
  adapter_ready boolean not null default false,
  requires_secret boolean not null default false,
  setup_requirements jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
insert into public.network_verification_method_catalog
  (method_key, display_name, adapter_key, enabled, adapter_ready, requires_secret, setup_requirements)
values
  ('gps','GPS / Geolocation','gps',true,false,false,'{"permission":"location","requirements":["browser_geolocation","server_side_radius_validation"]}'),
  ('mikrotik_hotspot','MikroTik Hotspot','mikrotik_hotspot',true,false,true,'{"requirements":["routeros_api_or_signed_callback","gateway_secret_reference","nonce_replay_protection"]}'),
  ('radius','RADIUS','radius',true,false,true,'{"requirements":["radius_server","shared_secret_reference","accounting_or_auth_evidence"]}'),
  ('gateway','Other Gateway / Controller','gateway',true,false,true,'{"requirements":["supported_gateway_adapter","signed_session_context"]}'),
  ('isp_api','ISP API','isp_api',true,false,true,'{"requirements":["provider_contract","provider_credentials_reference","signed_callback_or_api_auth"]}')
on conflict (method_key) do nothing;
alter table public.partner_networks add column if not exists active_verification_method text;
alter table public.partner_networks add constraint partner_networks_active_verification_method_check
check (active_verification_method is null or active_verification_method in ('gps','mikrotik_hotspot','radius','gateway','isp_api'));
create unique index if not exists network_verification_configs_one_enabled_per_network
on public.network_verification_configs(network_id) where enabled = true;
alter table public.network_verification_method_catalog enable row level security;
revoke all on public.network_verification_method_catalog from anon, authenticated;
grant select, insert, update on public.network_verification_method_catalog to service_role;
grant select, insert, update on public.partner_networks to service_role;
grant select, insert, update on public.network_verification_configs to service_role;
create index if not exists partner_networks_active_verification_method_idx
on public.partner_networks(active_verification_method);
create or replace function public.set_network_verification_method(
  p_network_id uuid, p_method_key text, p_config_public jsonb default '{}'::jsonb
) returns jsonb language plpgsql security invoker set search_path = public, pg_temp as $$
declare v_method public.network_verification_method_catalog%rowtype; v_config public.network_verification_configs%rowtype;
begin
 select * into v_method from public.network_verification_method_catalog where method_key=p_method_key and enabled=true;
 if not found then raise exception using errcode='22023',message='VERIFICATION_METHOD_NOT_AVAILABLE'; end if;
 update public.partner_networks set active_verification_method=p_method_key,updated_at=now() where id=p_network_id;
 if not found then raise exception using errcode='P0002',message='NETWORK_NOT_FOUND'; end if;
 update public.network_verification_configs set enabled=false,updated_at=now() where network_id=p_network_id and method_key<>p_method_key and enabled=true;
 insert into public.network_verification_configs(network_id,method_key,config_public,enabled,policy)
 values(p_network_id,p_method_key,coalesce(p_config_public,'{}'::jsonb),false,'{}'::jsonb)
 on conflict(network_id,method_key) do update set config_public=excluded.config_public,enabled=false,updated_at=now()
 returning * into v_config;
 return jsonb_build_object('network_id',p_network_id,'active_method',p_method_key,'selected',true,'activated',false,'adapter_ready',v_method.adapter_ready);
end; $$;
revoke all on function public.set_network_verification_method(uuid,text,jsonb) from public,anon,authenticated;
grant execute on function public.set_network_verification_method(uuid,text,jsonb) to service_role;
create or replace function public.enforce_selected_verification_adapter()
returns trigger language plpgsql security invoker set search_path=public,pg_temp as $$
declare v_selected_method text; v_adapter_ready boolean;
begin
 if new.enabled then
  select active_verification_method into v_selected_method from public.partner_networks where id=new.network_id;
  if v_selected_method is distinct from new.method_key then raise exception using errcode='23514',message='ONLY_SELECTED_VERIFICATION_METHOD_CAN_BE_ENABLED'; end if;
  select adapter_ready into v_adapter_ready from public.network_verification_method_catalog where method_key=new.method_key and enabled=true;
  if coalesce(v_adapter_ready,false) is not true then raise exception using errcode='23514',message='VERIFICATION_ADAPTER_NOT_READY'; end if;
 end if;
 return new;
end; $$;
revoke all on function public.enforce_selected_verification_adapter() from public,anon,authenticated;
drop trigger if exists enforce_selected_verification_adapter on public.network_verification_configs;
create trigger enforce_selected_verification_adapter before insert or update of network_id,method_key,enabled on public.network_verification_configs for each row execute function public.enforce_selected_verification_adapter();
create table if not exists public.network_gateway_nonces (
 id uuid primary key default gen_random_uuid(),
 network_id uuid not null references public.partner_networks(id) on delete cascade,
 nonce_hash text not null check(length(nonce_hash)=64),
 expires_at timestamptz not null,
 consumed_at timestamptz not null default now(),
 created_at timestamptz not null default now(),
 unique(network_id,nonce_hash)
);
create index if not exists network_gateway_nonces_expiry_idx on public.network_gateway_nonces(expires_at);
alter table public.network_gateway_nonces enable row level security;
revoke all on public.network_gateway_nonces from public,anon,authenticated;
grant select,insert,delete on public.network_gateway_nonces to service_role;
create or replace function public.consume_network_gateway_nonce(p_network_id uuid,p_nonce_hash text,p_expires_at timestamptz)
returns boolean language plpgsql security invoker set search_path=public,pg_temp as $$
declare v_inserted uuid;
begin
 if p_expires_at<=now() or p_expires_at>now()+interval '5 minutes' then return false; end if;
 delete from public.network_gateway_nonces where expires_at<now()-interval '1 hour';
 insert into public.network_gateway_nonces(network_id,nonce_hash,expires_at) values(p_network_id,p_nonce_hash,p_expires_at)
 on conflict(network_id,nonce_hash) do nothing returning id into v_inserted;
 return v_inserted is not null;
end; $$;
revoke all on function public.consume_network_gateway_nonce(uuid,text,timestamptz) from public,anon,authenticated;
grant execute on function public.consume_network_gateway_nonce(uuid,text,timestamptz) to service_role;