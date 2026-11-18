-- Phase 08: tenant-scoped knowledge retrieval foundation for OpenManus RAG.
-- Additive only. Document bytes remain in private Storage; rows below hold searchable text/chunks.
create extension if not exists vector with schema extensions;

create table if not exists public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  title text not null check (length(title) between 1 and 500),
  source_type text not null default 'text' check (source_type in ('text','file','url')),
  source_ref text,
  content_sha256 text not null check (content_sha256 ~ '^[0-9a-f]{64}$'),
  status text not null default 'ready' check (status in ('processing','ready','failed','archived')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists knowledge_documents_owner_workspace_idx
  on public.knowledge_documents(owner_user_id, workspace_id, created_at desc);
create unique index if not exists knowledge_documents_owner_scope_digest_uidx
  on public.knowledge_documents(owner_user_id, coalesce(workspace_id, '00000000-0000-0000-0000-000000000000'::uuid), content_sha256);

create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.knowledge_documents(id) on delete cascade,
  owner_user_id uuid not null references auth.users(id) on delete cascade,
  workspace_id uuid references public.workspaces(id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  content text not null check (length(content) between 1 and 12000),
  embedding extensions.vector(1536) not null,
  token_count integer check (token_count is null or token_count >= 0),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique(document_id, chunk_index)
);
create index if not exists knowledge_chunks_owner_workspace_idx
  on public.knowledge_chunks(owner_user_id, workspace_id, document_id);
create index if not exists knowledge_chunks_embedding_ivfflat_idx
  on public.knowledge_chunks using ivfflat (embedding extensions.vector_cosine_ops)
  with (lists = 100);

alter table public.knowledge_documents enable row level security;
alter table public.knowledge_chunks enable row level security;
drop policy if exists knowledge_documents_server_only on public.knowledge_documents;
create policy knowledge_documents_server_only on public.knowledge_documents
  for all to anon, authenticated using (false) with check (false);
drop policy if exists knowledge_chunks_server_only on public.knowledge_chunks;
create policy knowledge_chunks_server_only on public.knowledge_chunks
  for all to anon, authenticated using (false) with check (false);
revoke all on public.knowledge_documents, public.knowledge_chunks from public, anon, authenticated;
grant all on public.knowledge_documents, public.knowledge_chunks to service_role;

create or replace function public.moreai_match_knowledge_chunks(
  p_user_id uuid,
  p_workspace_id uuid,
  p_query_embedding extensions.vector(1536),
  p_match_count integer default 8,
  p_document_ids uuid[] default null
)
returns table (
  chunk_id uuid,
  document_id uuid,
  title text,
  content text,
  similarity double precision,
  metadata jsonb
)
language sql
stable
security definer
set search_path = ''
as $$
  select
    c.id,
    c.document_id,
    d.title,
    c.content,
    1 - (c.embedding OPERATOR(extensions.<=>) p_query_embedding) as similarity,
    c.metadata
  from public.knowledge_chunks c
  join public.knowledge_documents d on d.id = c.document_id
  where c.owner_user_id = p_user_id
    and (c.workspace_id is null or c.workspace_id = p_workspace_id)
    and d.owner_user_id = p_user_id
    and (d.workspace_id is null or d.workspace_id = p_workspace_id)
    and d.status = 'ready'
    and (p_document_ids is null or c.document_id = any(p_document_ids))
  order by c.embedding OPERATOR(extensions.<=>) p_query_embedding
  limit greatest(1, least(coalesce(p_match_count, 8), 20));
$$;
revoke all on function public.moreai_match_knowledge_chunks(uuid,uuid,extensions.vector,integer,uuid[]) from public, anon, authenticated;
grant execute on function public.moreai_match_knowledge_chunks(uuid,uuid,extensions.vector,integer,uuid[]) to service_role;
