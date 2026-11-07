-- Enable pgvector extension
create extension if not exists vector;

-- Knowledge base embeddings table
create table if not exists knowledge_base_embeddings (
  id bigint generated always as identity primary key,
  knowledge_base_id bigint not null references knowledge_base (id) on delete cascade,
  chunk_index int not null default 0,
  chunk_text text not null,
  embedding vector(768) not null,
  metadata jsonb default '{}',
  created_at timestamptz not null default now()
);

-- Gmail watch state table (singleton)
create table if not exists gmail_watch_state (
  id int primary key default 1,
  history_id bigint not null,
  expiration bigint not null,
  updated_at timestamptz not null default now()
);

alter table knowledge_base_embeddings enable row level security;
alter table gmail_watch_state enable row level security;

