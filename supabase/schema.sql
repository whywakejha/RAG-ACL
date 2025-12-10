-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- 1. Create a table to store our mock users (for the PoC identity provider)
create table app_users (
  id uuid primary key default gen_random_uuid(),
  username text unique not null,
  role text not null -- e.g., 'engineer', 'hr', 'public'
);

-- 2. Create the documents table with vector embeddings
create table documents (
  id bigserial primary key,
  content text not null,
  metadata jsonb,
  embedding vector(1536), -- OpenAI embedding size
  allowed_roles text[] -- The ACL: which roles can see this? e.g. ['engineer', 'admin']
);

-- 3. Enable RLS
alter table documents enable row level security;

-- 4. Create the Policy
-- This policy checks a custom session variable 'app.current_user_role'
-- If 'allowed_roles' is null, it's public.
-- If 'allowed_roles' contains the current role, it's visible.
create policy "RLS based on API-set role"
on documents
for select
using (
  allowed_roles is null 
  or 
  current_setting('app.current_user_role', true) = any(allowed_roles)
);

-- 5. RPC Function for similarity search
-- We need this because we want to safely set the config variable within the transaction of the search
create or replace function match_documents (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  user_role text
)
returns table (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  -- Set the local configuration parameter for this transaction/request
  -- We cast to text to be safe
  perform set_config('app.current_user_role', user_role, true);

  return query
  select
    documents.id,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) as similarity
  from documents
  where 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by documents.embedding <=> query_embedding
  limit match_count;
end;
$$;
