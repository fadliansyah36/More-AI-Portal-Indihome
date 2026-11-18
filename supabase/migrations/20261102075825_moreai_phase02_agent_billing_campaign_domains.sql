-- Phase 02 durable agent, conversation, usage, credit, quota and campaign domains.
-- All business access is mediated by FastAPI; client roles receive no table grants.
create table if not exists public.conversations (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 workspace_id uuid references public.workspaces(id) on delete cascade,
 title text,
 status text not null default 'active' check(status in ('active','archived','deleted')),
 metadata jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create table if not exists public.conversation_messages (
 id uuid primary key default gen_random_uuid(),
 conversation_id uuid not null references public.conversations(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 role text not null check(role in ('system','user','assistant','tool')),
 content text not null,
 model_key text,
 run_id uuid,
 token_input integer not null default 0 check(token_input >= 0),
 token_output integer not null default 0 check(token_output >= 0),
 metadata jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now()
);
create table if not exists public.agent_definitions (
 id uuid primary key default gen_random_uuid(),
 key text not null unique,
 name text not null,
 description text,
 version integer not null default 1 check(version > 0),
 enabled boolean not null default false,
 config jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create table if not exists public.agent_runs (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 workspace_id uuid references public.workspaces(id) on delete cascade,
 conversation_id uuid references public.conversations(id) on delete set null,
 agent_definition_id uuid references public.agent_definitions(id),
 status text not null default 'queued' check(status in ('queued','running','waiting_approval','succeeded','failed','cancelled','expired')),
 idempotency_key text not null,
 input jsonb not null default '{}'::jsonb,
 output jsonb,
 error jsonb,
 attempt integer not null default 0 check(attempt >= 0),
 max_attempts integer not null default 3 check(max_attempts between 1 and 20),
 available_at timestamptz not null default now(),
 started_at timestamptz,
 finished_at timestamptz,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(user_id,idempotency_key)
);
create table if not exists public.agent_run_steps (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references public.agent_runs(id) on delete cascade,
 sequence integer not null check(sequence > 0),
 step_key text not null,
 status text not null check(status in ('pending','running','waiting_approval','succeeded','failed','skipped','cancelled')),
 input jsonb not null default '{}'::jsonb,
 output jsonb,
 error jsonb,
 started_at timestamptz,
 finished_at timestamptz,
 created_at timestamptz not null default now(),
 unique(run_id,sequence)
);
create table if not exists public.agent_run_events (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references public.agent_runs(id) on delete cascade,
 event_type text not null,
 sequence bigint not null,
 payload jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 unique(run_id,sequence)
);
create table if not exists public.agent_run_checkpoints (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references public.agent_runs(id) on delete cascade,
 checkpoint_key text not null,
 state jsonb not null,
 created_at timestamptz not null default now(),
 unique(run_id,checkpoint_key)
);
create table if not exists public.tool_executions (
 id uuid primary key default gen_random_uuid(),
 run_id uuid not null references public.agent_runs(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 tool_key text not null,
 status text not null check(status in ('queued','running','waiting_approval','succeeded','failed','denied','cancelled')),
 input jsonb not null default '{}'::jsonb,
 output jsonb,
 error jsonb,
 approval_required boolean not null default false,
 started_at timestamptz,
 finished_at timestamptz,
 created_at timestamptz not null default now()
);
create table if not exists public.llm_providers (
 id uuid primary key default gen_random_uuid(),
 key text not null unique,
 display_name text not null,
 enabled boolean not null default false,
 config jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create table if not exists public.llm_models (
 id uuid primary key default gen_random_uuid(),
 provider_id uuid not null references public.llm_providers(id),
 key text not null unique,
 display_name text not null,
 input_cost_per_million numeric(18,8) not null default 0 check(input_cost_per_million >= 0),
 output_cost_per_million numeric(18,8) not null default 0 check(output_cost_per_million >= 0),
 max_input_tokens integer,
 max_output_tokens integer,
 capabilities text[] not null default '{}',
 enabled boolean not null default false,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create table if not exists public.llm_routing_policies (
 id uuid primary key default gen_random_uuid(),
 scope_type text not null check(scope_type in ('platform','workspace','partner','user')),
 scope_id uuid,
 task_type text not null default 'general',
 model_id uuid not null references public.llm_models(id),
 priority integer not null default 100,
 fallback_model_id uuid references public.llm_models(id),
 enabled boolean not null default true,
 created_at timestamptz not null default now(),
 check((scope_type='platform' and scope_id is null) or (scope_type<>'platform' and scope_id is not null))
);
create table if not exists public.llm_usage (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 workspace_id uuid references public.workspaces(id) on delete set null,
 run_id uuid references public.agent_runs(id) on delete set null,
 message_id uuid references public.conversation_messages(id) on delete set null,
 provider_key text not null,
 model_key text not null,
 request_id text,
 input_tokens integer not null default 0 check(input_tokens >= 0),
 output_tokens integer not null default 0 check(output_tokens >= 0),
 estimated_cost numeric(20,10) not null default 0 check(estimated_cost >= 0),
 actual_cost numeric(20,10) check(actual_cost is null or actual_cost >= 0),
 status text not null check(status in ('reserved','succeeded','failed','refunded')),
 idempotency_key text not null,
 latency_ms integer check(latency_ms is null or latency_ms >= 0),
 created_at timestamptz not null default now(),
 unique(user_id,idempotency_key)
);
create table if not exists public.wallet_accounts (
 id uuid primary key default gen_random_uuid(),
 owner_type text not null check(owner_type in ('user','workspace','partner')),
 owner_id uuid not null,
 currency text not null default 'CREDIT',
 balance numeric(20,6) not null default 0 check(balance >= 0),
 status text not null default 'active' check(status in ('active','frozen','closed')),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(owner_type,owner_id,currency)
);
create table if not exists public.credit_ledger (
 id uuid primary key default gen_random_uuid(),
 wallet_id uuid not null references public.wallet_accounts(id),
 entry_type text not null check(entry_type in ('grant','purchase','reserve','consume','release','refund','adjustment','expiry')),
 amount numeric(20,6) not null check(amount <> 0),
 balance_after numeric(20,6) not null check(balance_after >= 0),
 reference_type text,
 reference_id uuid,
 idempotency_key text not null unique,
 description text,
 metadata jsonb not null default '{}'::jsonb,
 created_by uuid references auth.users(id),
 created_at timestamptz not null default now()
);
create table if not exists public.credit_reservations (
 id uuid primary key default gen_random_uuid(),
 wallet_id uuid not null references public.wallet_accounts(id),
 user_id uuid not null references auth.users(id),
 run_id uuid references public.agent_runs(id) on delete set null,
 amount numeric(20,6) not null check(amount > 0),
 settled_amount numeric(20,6) check(settled_amount is null or settled_amount >= 0),
 status text not null default 'reserved' check(status in ('reserved','settled','released','expired')),
 idempotency_key text not null unique,
 expires_at timestamptz not null,
 settled_at timestamptz,
 created_at timestamptz not null default now()
);
create table if not exists public.quota_policies (
 id uuid primary key default gen_random_uuid(),
 scope_type text not null check(scope_type in ('platform','workspace','partner','user')),
 scope_id uuid,
 metric_key text not null,
 limit_value numeric(20,6) not null check(limit_value >= 0),
 window_seconds integer not null check(window_seconds > 0),
 enabled boolean not null default true,
 created_at timestamptz not null default now(),
 check((scope_type='platform' and scope_id is null) or (scope_type<>'platform' and scope_id is not null)),
 unique(scope_type,scope_id,metric_key,window_seconds)
);
create table if not exists public.quota_usage (
 id uuid primary key default gen_random_uuid(),
 policy_id uuid not null references public.quota_policies(id),
 scope_type text not null,
 scope_id uuid,
 metric_key text not null,
 window_start timestamptz not null,
 used_value numeric(20,6) not null default 0 check(used_value >= 0),
 updated_at timestamptz not null default now(),
 unique(policy_id,scope_type,scope_id,metric_key,window_start)
);
create table if not exists public.partner_campaigns (
 id uuid primary key default gen_random_uuid(),
 partner_id uuid not null references public.partner_organizations(id) on delete cascade,
 location_id uuid references public.partner_locations(id) on delete cascade,
 name text not null,
 status text not null default 'draft' check(status in ('draft','pending','active','paused','completed','cancelled')),
 starts_at timestamptz,
 ends_at timestamptz,
 budget numeric(20,6) check(budget is null or budget >= 0),
 config jsonb not null default '{}'::jsonb,
 created_by uuid references auth.users(id),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 check(ends_at is null or starts_at is null or ends_at > starts_at)
);
create table if not exists public.campaign_rewards (
 id uuid primary key default gen_random_uuid(),
 campaign_id uuid not null references public.partner_campaigns(id) on delete cascade,
 reward_type text not null check(reward_type in ('credit','discount','access','voucher','benefit')),
 name text not null,
 quantity_limit integer check(quantity_limit is null or quantity_limit >= 0),
 quantity_claimed integer not null default 0 check(quantity_claimed >= 0),
 reward_value numeric(20,6) check(reward_value is null or reward_value >= 0),
 config jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 check(quantity_limit is null or quantity_claimed <= quantity_limit)
);
create table if not exists public.reward_claims (
 id uuid primary key default gen_random_uuid(),
 reward_id uuid not null references public.campaign_rewards(id),
 campaign_id uuid not null references public.partner_campaigns(id),
 user_id uuid not null references auth.users(id) on delete cascade,
 status text not null default 'claimed' check(status in ('claimed','redeemed','expired','revoked')),
 idempotency_key text not null,
 claimed_at timestamptz not null default now(),
 redeemed_at timestamptz,
 unique(user_id,idempotency_key)
);
create table if not exists public.idempotency_keys (
 id uuid primary key default gen_random_uuid(),
 scope_key text not null,
 idempotency_key text not null,
 request_hash text not null,
 response_status integer,
 response_body jsonb,
 status text not null default 'processing' check(status in ('processing','completed','failed')),
 expires_at timestamptz not null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique(scope_key,idempotency_key)
);
create table if not exists public.outbox_events (
 id uuid primary key default gen_random_uuid(),
 aggregate_type text not null,
 aggregate_id uuid not null,
 event_type text not null,
 payload jsonb not null default '{}'::jsonb,
 status text not null default 'pending' check(status in ('pending','processing','published','failed','dead_letter')),
 attempts integer not null default 0 check(attempts >= 0),
 available_at timestamptz not null default now(),
 locked_at timestamptz,
 published_at timestamptz,
 last_error text,
 created_at timestamptz not null default now()
);
create table if not exists public.artifacts (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 workspace_id uuid references public.workspaces(id) on delete cascade,
 run_id uuid references public.agent_runs(id) on delete set null,
 storage_path text not null,
 mime_type text,
 size_bytes bigint check(size_bytes is null or size_bytes >= 0),
 checksum_sha256 text,
 metadata jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now(),
 unique(storage_path)
);

create index if not exists conversations_user_updated_idx on public.conversations(user_id,updated_at desc);
create index if not exists messages_conversation_created_idx on public.conversation_messages(conversation_id,created_at);
create index if not exists agent_runs_worker_idx on public.agent_runs(status,available_at,created_at) where status in ('queued','running');
create index if not exists agent_runs_tenant_idx on public.agent_runs(user_id,workspace_id,created_at desc);
create index if not exists agent_events_run_idx on public.agent_run_events(run_id,sequence);
create index if not exists tool_executions_run_idx on public.tool_executions(run_id,created_at);
create index if not exists llm_usage_user_idx on public.llm_usage(user_id,created_at desc);
create index if not exists llm_usage_run_idx on public.llm_usage(run_id);
create index if not exists credit_ledger_wallet_idx on public.credit_ledger(wallet_id,created_at desc);
create index if not exists reservations_due_idx on public.credit_reservations(expires_at) where status='reserved';
create index if not exists quota_usage_lookup_idx on public.quota_usage(policy_id,window_start);
create index if not exists campaign_partner_idx on public.partner_campaigns(partner_id,status,starts_at);
create index if not exists reward_claims_user_idx on public.reward_claims(user_id,claimed_at desc);
create index if not exists outbox_dispatch_idx on public.outbox_events(status,available_at,created_at) where status in ('pending','failed');
create index if not exists artifacts_owner_idx on public.artifacts(user_id,created_at desc);

-- New business tables are server-only. RLS is an additional deny-by-default boundary.
do $$
declare t text;
begin
 foreach t in array array[
 'conversations','conversation_messages','agent_definitions','agent_runs','agent_run_steps',
 'agent_run_events','agent_run_checkpoints','tool_executions','llm_providers','llm_models',
 'llm_routing_policies','llm_usage','wallet_accounts','credit_ledger','credit_reservations',
 'quota_policies','quota_usage','partner_campaigns','campaign_rewards','reward_claims',
 'idempotency_keys','outbox_events','artifacts'
 ] loop
  execute format('alter table public.%I enable row level security',t);
  execute format('create policy %I on public.%I as restrictive for all to anon, authenticated using (false) with check (false)',t||'_deny_client_access',t);
  execute format('revoke all on table public.%I from anon, authenticated',t);
  execute format('grant select, insert, update, delete on table public.%I to service_role',t);
 end loop;
end $$;

create or replace function public.prevent_credit_ledger_mutation()
returns trigger language plpgsql set search_path = '' as $$
begin
 raise exception 'credit_ledger is append-only';
end;
$$;
revoke all on function public.prevent_credit_ledger_mutation() from public, anon, authenticated;
create trigger credit_ledger_immutable before update or delete on public.credit_ledger
for each row execute function public.prevent_credit_ledger_mutation();
