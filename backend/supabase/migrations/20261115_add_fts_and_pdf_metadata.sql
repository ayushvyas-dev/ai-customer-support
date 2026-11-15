-- Add source_type and filename to knowledge_base
alter table knowledge_base add column if not exists source_type text not null default 'text';
alter table knowledge_base add column if not exists filename text;

-- Add generated tsvector column for Full-Text Search (FTS) on knowledge_base_embeddings
alter table knowledge_base_embeddings add column if not exists fts tsvector 
  generated always as (to_tsvector('english', chunk_text)) stored;

-- Add GIN index for high performance sparse FTS queries
create index if not exists kb_embeddings_fts_idx on knowledge_base_embeddings using gin (fts);

