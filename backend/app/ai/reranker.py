import json
import logging
import os
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)


def compute_rrf_score(
    dense_rank: int | None, sparse_rank: int | None, k: int = 60
) -> float:
    """Calculate Reciprocal Rank Fusion (RRF) score for a document.

    Args:
        dense_rank: 1-based rank in semantic vector search (None if absent).
        sparse_rank: 1-based rank in keyword/FTS search (None if absent).
        k: Smoothing constant (standard is 60).
    """
    score = 0.0
    if dense_rank is not None and dense_rank > 0:
        score += 1.0 / (k + dense_rank)
    if sparse_rank is not None and sparse_rank > 0:
        score += 1.0 / (k + sparse_rank)
    return score


class RankedItem(BaseModel):
    index: int = Field(description="The 0-based index of the passage")
    relevance_score: float = Field(
        description="Relevance score from 0.0 (irrelevant) to 10.0 (directly answers query)"
    )


class RerankResult(BaseModel):
    ranking: list[RankedItem] = Field(description="List of scored passages")


def get_reranker_llm():
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    models = settings.get_agent_models()
    model_name = models[0] if models else "gemini-2.5-flash"
    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.0,
        google_api_key=api_key,
        api_version="v1beta",
        timeout=10,
    )


RERANK_PROMPT = """
You are a precision relevance scoring judge for a customer support retrieval system.
Evaluate the following candidate document snippets against the customer query.
Assign a relevance score from 0.0 to 10.0 indicating how accurately and directly the snippet answers the customer query.

Customer Query: {query}

Snippets to Evaluate:
{snippets}
"""


def rerank_passages(
    query: str, passages: list[dict[str, Any]], top_k: int = 4
) -> list[dict[str, Any]]:
    """Rerank candidate passages using LLM relevance scoring with fallback to RRF rank.

    Args:
        query: The customer query or search phrase.
        passages: List of candidate passage dicts with "chunk_text", "title", "rrf_score".
        top_k: Number of highest-ranked passages to return.

    Returns:
        The top_k most relevant passage dicts sorted by relevance.
    """
    if not passages:
        return []

    if len(passages) <= top_k:
        return sorted(passages, key=lambda p: p.get("rrf_score", 0.0), reverse=True)

    # Attempt LLM-based zero-shot cross-scoring
    try:
        llm = get_reranker_llm()
        structured_llm = llm.with_structured_output(RerankResult)

        snippets_text = "\n\n".join(
            f"--- Snippet [{idx}] ---\nTitle: {p.get('title')}\nContent: {p.get('chunk_text')[:400]}"
            for idx, p in enumerate(passages)
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You judge document relevance accurately."),
                ("human", RERANK_PROMPT),
            ]
        )
        chain = prompt | structured_llm
        output: RerankResult = chain.invoke({"query": query, "snippets": snippets_text})

        # Map scores to passages
        scores_by_idx = {item.index: item.relevance_score for item in output.ranking}
        for idx, p in enumerate(passages):
            p["rerank_score"] = scores_by_idx.get(idx, 0.0)

        sorted_passages = sorted(
            passages,
            key=lambda p: (p.get("rerank_score", 0.0), p.get("rrf_score", 0.0)),
            reverse=True,
        )
        return sorted_passages[:top_k]

    except Exception as ex:
        logger.warning("LLM reranking unavailable or failed: %s. Using RRF score order.", ex)
        # Safe fallback: Sort by RRF score descending
        sorted_by_rrf = sorted(
            passages, key=lambda p: p.get("rrf_score", 0.0), reverse=True
        )
        return sorted_by_rrf[:top_k]

