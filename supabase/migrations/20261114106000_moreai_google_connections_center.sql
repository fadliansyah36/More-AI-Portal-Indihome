-- Google Connections Center: durable OAuth state, encrypted credentials and audit.
create table if not exists public.moreai_oauth_states (
  state_hash text primary key check (state_hash ~ '^[0-9a-f]{64}$'),
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null check (provider in ('google')),
  scopes jsonb not null check (jsonb_typeof(scopes)='array'),
  pkce_verifier_ciphertext text not null,
  redirect_uri text not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);
create index if not exists moreai_oauth_states_expiry_idx on public.moreai_oauth_states(expires_at);
alter table public.moreai_oauth_states enable row level security;
revoke all on public.moreai_oauth_states from public,anon,authenticated;
grant select,insert,delete on public.moreai_oauth_states to service_role;
drop policy if exists moreai_oauth_states_server_only on public.moreai_oauth_states;
create policy moreai_oauth_states_server_only on public.moreai_oauth_states for all to anon,authenticated using(false) with check(false);

create table if not exists public.moreai_connections (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null check (provider in ('google')),
  external_account_id text not null,
  display_name text,
  scopes jsonb not null default '[]'::jsonb check (jsonb_typeof(scopes)='array'),
  status text not null default 'connected' check (status in ('connected','expired','revoked','error')),
  credential_ciphertext text not null,
  credential_key_version integer not null default 1,
  access_token_expires_at timestamptz,
  token_updated_at timestamptz not null default now(),
  last_error_code text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id,provider,external_account_id)
);
create index if not exists moreai_connections_owner_provider_idx on public.moreai_connections(user_id,provider,status);
alter table public.moreai_connections enable row level security;
revoke all on public.moreai_connections from public,anon,authenticated;
grant select,insert,update,delete on public.moreai_connections to service_role;
drop policy if exists moreai_connections_server_only on public.moreai_connections;
create policy moreai_connections_server_only on public.moreai_connections for all to anon,authenticated using(false) with check(false);

create table if not exists public.moreai_connection_audit (
  id uuid primary key default gen_random_uuid(),
  connection_id uuid references public.moreai_connections(id) on delete set null,
  user_id uuid not null references auth.users(id) on delete cascade,
  provider text not null,
  event_type text not null check(event_type in ('oauth_started','connected','refreshed','revoked','permission_changed','action_requested','action_completed','action_failed')),
  scopes jsonb not null default '[]'::jsonb,
  detail jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists moreai_connection_audit_owner_idx on public.moreai_connection_audit(user_id,created_at desc);
alter table public.moreai_connection_audit enable row level security;
revoke all on public.moreai_connection_audit from public,anon,authenticated;
grant select,insert on public.moreai_connection_audit to service_role;
drop policy if exists moreai_connection_audit_server_only on public.moreai_connection_audit;
create policy moreai_connection_audit_server_only on public.moreai_connection_audit for all to anon,authenticated using(false) with check(false);

create or replace function public.moreai_consume_google_oauth_state(p_state_hash text)
returns jsonb language plpgsql security definer set search_path=''
as $function$
declare v_state public.moreai_oauth_states%rowtype;
begin
  delete from public.moreai_oauth_states where state_hash=p_state_hash
    and provider='google' and expires_at>now()
    returning * into v_state;
  if not found then raise exception 'oauth_state_invalid_or_expired' using errcode='42501'; end if;
  return jsonb_build_object('user_id',v_state.user_id,'provider',v_state.provider,
    'scopes',v_state.scopes,'pkce_verifier_ciphertext',v_state.pkce_verifier_ciphertext,
    'redirect_uri',v_state.redirect_uri);
end;
$function$;
revoke all on function public.moreai_consume_google_oauth_state(text) from public,anon,authenticated;
grant execute on function public.moreai_consume_google_oauth_state(text) to service_role;

create or replace function public.moreai_store_google_connection(
  p_user_id uuid,p_external_account_id text,p_display_name text,p_scopes jsonb,
  p_credential_ciphertext text,p_expires_at timestamptz
) returns jsonb language plpgsql security definer set search_path=''
as $function$
declare v_connection public.moreai_connections%rowtype;
begin
  if p_user_id is null or coalesce(p_external_account_id,'')='' or
     jsonb_typeof(p_scopes)<>'array' or coalesce(p_credential_ciphertext,'')='' then
    raise exception 'google_connection_payload_invalid' using errcode='22023';
  end if;
  insert into public.moreai_connections(user_id,provider,external_account_id,display_name,scopes,status,
    credential_ciphertext,credential_key_version,access_token_expires_at,token_updated_at,last_error_code,updated_at)
  values(p_user_id,'google',p_external_account_id,left(p_display_name,240),p_scopes,'connected',
    p_credential_ciphertext,1,p_expires_at,now(),null,now())
  on conflict(user_id,provider,external_account_id) do update set
    display_name=excluded.display_name,scopes=excluded.scopes,status='connected',
    credential_ciphertext=excluded.credential_ciphertext,credential_key_version=1,
    access_token_expires_at=excluded.access_token_expires_at,token_updated_at=now(),
    last_error_code=null,updated_at=now()
  returning * into v_connection;
  insert into public.moreai_connection_audit(connection_id,user_id,provider,event_type,scopes,detail)
  values(v_connection.id,p_user_id,'google','connected',p_scopes,
    jsonb_build_object('account_id_hash',encode(digest(p_external_account_id,'sha256'),'hex')));
  return jsonb_build_object('id',v_connection.id,'provider',v_connection.provider,
    'display_name',v_connection.display_name,'scopes',v_connection.scopes,
    'status',v_connection.status,'access_token_expires_at',v_connection.access_token_expires_at);
end;
$function$;
revoke all on function public.moreai_store_google_connection(uuid,text,text,jsonb,text,timestamptz) from public,anon,authenticated;
grant execute on function public.moreai_store_google_connection(uuid,text,text,jsonb,text,timestamptz) to service_role;

create or replace function public.moreai_disconnect_connection(p_connection_id uuid,p_user_id uuid)
returns jsonb language plpgsql security definer set search_path=''
as $function$
declare v_connection public.moreai_connections%rowtype;
begin
  update public.moreai_connections set status='revoked',credential_ciphertext='',
    last_error_code=null,updated_at=now()
  where id=p_connection_id and user_id=p_user_id and provider='google'
  returning * into v_connection;
  if not found then raise exception 'connection_not_found' using errcode='42501'; end if;
  insert into public.moreai_connection_audit(connection_id,user_id,provider,event_type,scopes,detail)
  values(v_connection.id,p_user_id,'google','revoked',v_connection.scopes,'{}'::jsonb);
  return jsonb_build_object('id',v_connection.id,'status',v_connection.status);
end;
$function$;
revoke all on function public.moreai_disconnect_connection(uuid,uuid) from public,anon,authenticated;
grant execute on function public.moreai_disconnect_connection(uuid,uuid) to service_role;
