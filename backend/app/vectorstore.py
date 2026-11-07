import json
import logging
import os
from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app import db
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


def delete_embeddings_for_kb_id(kb_id: int) -> None:
    with db.connect() as conn:
        conn.execute(
            "delete from knowledge_base_embeddings where knowledge_base_id = %s",
            (kb_id,),
        )


def search_similar(query: str, section: str | None = None, top_k: int = 4) -> list[str]:
    """Semantic vector search against knowledge_base_embeddings using cosine distance."""
    vec = embed_text(query)
    vec_str = "[" + ",".join(str(f) for f in vec) + "]"

    with db.connect() as conn:
        if section and section != "other":
            query_sql = """
                select chunk_text, metadata->>'title' as title, metadata->>'section' as sec,
                       1 - (embedding <=> %s::vector) as similarity
                from knowledge_base_embeddings
                where metadata->>'section' in (%s, 'brand-and-tone', 'escalation-rules')
                order by embedding <=> %s::vector asc
                limit %s
            """
            rows = conn.execute(query_sql, (vec_str, section, vec_str, top_k)).fetchall()
        else:
            query_sql = """
                select chunk_text, metadata->>'title' as title, metadata->>'section' as sec,
                       1 - (embedding <=> %s::vector) as similarity
                from knowledge_base_embeddings
                order by embedding <=> %s::vector asc
                limit %s
            """
            rows = conn.execute(query_sql, (vec_str, vec_str, top_k)).fetchall()

    docs = []
    for r in rows:
        title = r.get("title") or "Document"
        docs.append(f"## {title}\n{r['chunk_text']}")
    return docs


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

