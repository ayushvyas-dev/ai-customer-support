import json
import logging
import os
from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app import db
from app.ai.reranker import compute_rrf_score, rerank_passages
from app.config import settings

logger = logging.getLogger(__name__)


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        output_dimensionality=768,
        google_api_key=api_key,
    )


def embed_text(text: str) -> list[float]:
    embeddings = get_embeddings()
    return embeddings.embed_query(text)


def index_knowledge_base_entry(
    kb_id: int, section: str, title: str, content: str
) -> int:
    """Chunks an entry and stores vectors in PostgreSQL."""
    delete_embeddings_for_kb_id(kb_id)

    # Chunk content by paragraphs / headers or lines
    chunks = []
    current_chunk = []
    current_len = 0

    lines = content.splitlines()
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        current_chunk.append(line_str)
        current_len += len(line_str)
        if current_len >= 500:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    if not chunks:
        chunks = [f"{title}\n{content}".strip()]

    embeddings = get_embeddings()
    vectors = embeddings.embed_documents(chunks)

    count = 0
    with db.connect() as conn:
        for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
            meta = json.dumps({"section": section, "title": title, "kb_id": kb_id})
            # Format vector as postgres vector string: '[0.1, 0.2, ...]'
            vec_str = "[" + ",".join(str(f) for f in vec) + "]"
            conn.execute(
                """
                insert into knowledge_base_embeddings (knowledge_base_id, chunk_index, chunk_text, embedding, metadata)
                values (%s, %s, %s, %s::vector, %s)
                """,
                (kb_id, idx, chunk, vec_str, meta),
            )
            count += 1
    return count


def index_pdf_document(
    kb_id: int, section: str, title: str, chunks: list[dict[str, Any]]
) -> int:
    """Index pre-chunked PDF pages with metadata into PostgreSQL."""
    delete_embeddings_for_kb_id(kb_id)
    if not chunks:
        return 0

    chunk_texts = [c["chunk_text"] for c in chunks]
    embeddings = get_embeddings()
    vectors = embeddings.embed_documents(chunk_texts)

    count = 0
    with db.connect() as conn:
        for idx, (chunk_data, vec) in enumerate(zip(chunks, vectors)):
            meta = {
                "section": section,
                "title": title,
                "kb_id": kb_id,
                "source_type": "pdf",
                "page": chunk_data.get("metadata", {}).get("page", 1),
                "filename": chunk_data.get("metadata", {}).get("filename", title),
            }
            vec_str = "[" + ",".join(str(f) for f in vec) + "]"
            conn.execute(
                """
                insert into knowledge_base_embeddings (knowledge_base_id, chunk_index, chunk_text, embedding, metadata)
                values (%s, %s, %s, %s::vector, %s)
                """,
                (kb_id, idx, chunk_data["chunk_text"], vec_str, json.dumps(meta)),
            )
            count += 1
    return count


def delete_embeddings_for_kb_id(kb_id: int) -> None:
    with db.connect() as conn:
        conn.execute(
            "delete from knowledge_base_embeddings where knowledge_base_id = %s",
            (kb_id,),
        )


def search_hybrid(
    query: str, section: str | None = None, top_k: int = 4, alpha: float = 0.5
) -> list[str]:
    """Hybrid Search combining dense vector similarity and sparse PostgreSQL FTS with RRF and reranking."""
    clean_query = query.strip()
    if not clean_query:
        return []

    # 1. Dense Semantic Vector Search
    dense_candidates: list[dict[str, Any]] = []
    try:
        vec = embed_text(clean_query)
        vec_str = "[" + ",".join(str(f) for f in vec) + "]"

        with db.connect() as conn:
            if section and section != "other":
                query_sql = """
                    select id, chunk_text, metadata->>'title' as title, metadata->>'section' as sec,
                           metadata, 1 - (embedding <=> %s::vector) as similarity
                    from knowledge_base_embeddings
                    where metadata->>'section' in (%s, 'brand-and-tone', 'escalation-rules')
                    order by embedding <=> %s::vector asc
                    limit 10
                """
                dense_candidates = conn.execute(query_sql, (vec_str, section, vec_str)).fetchall()
            else:
                query_sql = """
                    select id, chunk_text, metadata->>'title' as title, metadata->>'section' as sec,
                           metadata, 1 - (embedding <=> %s::vector) as similarity
                    from knowledge_base_embeddings
                    order by embedding <=> %s::vector asc
                    limit 10
                """
                dense_candidates = conn.execute(query_sql, (vec_str, vec_str)).fetchall()
    except Exception as ex:
        logger.warning("Dense vector search failed: %s", ex)

    # 2. Sparse PostgreSQL Full-Text Search (FTS)
    sparse_candidates: list[dict[str, Any]] = []
    try:
        with db.connect() as conn:
            if section and section != "other":
                sparse_sql = """
                    select id, chunk_text, metadata->>'title' as title, metadata->>'section' as sec,
                           metadata, ts_rank_cd(fts, plainto_tsquery('english', %s)) as fts_rank
                    from knowledge_base_embeddings
                    where fts @@ plainto_tsquery('english', %s)
                      and metadata->>'section' in (%s, 'brand-and-tone', 'escalation-rules')
                    order by fts_rank desc
                    limit 10
                """
                sparse_candidates = conn.execute(sparse_sql, (clean_query, clean_query, section)).fetchall()
            else:
                sparse_sql = """
                    select id, chunk_text, metadata->>'title' as title, metadata->>'section' as sec,
                           metadata, ts_rank_cd(fts, plainto_tsquery('english', %s)) as fts_rank
                    from knowledge_base_embeddings
                    where fts @@ plainto_tsquery('english', %s)
                    order by fts_rank desc
                    limit 10
                """
                sparse_candidates = conn.execute(sparse_sql, (clean_query, clean_query)).fetchall()
    except Exception as ex:
        logger.warning("Sparse FTS query failed (fts column might not be migrated yet): %s", ex)

    # 3. Reciprocal Rank Fusion (RRF)
    # Map each candidate by unique key (id or title+chunk_text)
    fused_items: dict[str, dict[str, Any]] = {}

    for rank, item in enumerate(dense_candidates, start=1):
        key = str(item.get("id")) or f"{item.get('title')}_{item.get('chunk_text')[:50]}"
        if key not in fused_items:
            meta = item.get("metadata")
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            fused_items[key] = {
                "chunk_text": item.get("chunk_text", ""),
                "title": item.get("title") or "Document",
                "sec": item.get("sec") or "general",
                "metadata": meta or {},
                "dense_rank": rank,
                "sparse_rank": None,
            }
        else:
            fused_items[key]["dense_rank"] = rank

    for rank, item in enumerate(sparse_candidates, start=1):
        key = str(item.get("id")) or f"{item.get('title')}_{item.get('chunk_text')[:50]}"
        if key not in fused_items:
            meta = item.get("metadata")
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            fused_items[key] = {
                "chunk_text": item.get("chunk_text", ""),
                "title": item.get("title") or "Document",
                "sec": item.get("sec") or "general",
                "metadata": meta or {},
                "dense_rank": None,
                "sparse_rank": rank,
            }
        else:
            fused_items[key]["sparse_rank"] = rank

    # Compute RRF score for all fused items
    fused_list = []
    for item in fused_items.values():
        item["rrf_score"] = compute_rrf_score(item["dense_rank"], item["sparse_rank"], k=60)
        fused_list.append(item)

    if not fused_list:
        return []

    # 4. Rerank top candidates with cross-scoring
    reranked = rerank_passages(query=clean_query, passages=fused_list, top_k=top_k)

    # 5. Format results into structured markdown snippets for LLM
    docs: list[str] = []
    for r in reranked:
        title = r.get("title") or "Document"
        meta = r.get("metadata", {})
        page = meta.get("page") if isinstance(meta, dict) else None
        page_suffix = f" (Page {page})" if page else ""
        docs.append(f"## {title}{page_suffix}\n{r.get('chunk_text', '')}")

    return docs


def search_similar(query: str, section: str | None = None, top_k: int = 4) -> list[str]:
    """Semantic & Hybrid search against knowledge_base_embeddings (backwards compatible)."""
    return search_hybrid(query=query, section=section, top_k=top_k)


def reindex_all() -> int:
    """Reindexes all knowledge_base rows into embeddings table."""
    with db.connect() as conn:
        entries = conn.execute(
            "select id, section, title, content from knowledge_base order by id"
        ).fetchall()

    total_chunks = 0
    for e in entries:
        total_chunks += index_knowledge_base_entry(
            kb_id=e["id"],
            section=e["section"],
            title=e["title"],
            content=e["content"],
        )
    return total_chunks

