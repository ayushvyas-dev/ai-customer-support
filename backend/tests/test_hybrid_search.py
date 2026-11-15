import unittest
from unittest.mock import MagicMock, patch

from app.ai.reranker import compute_rrf_score, rerank_passages
from app.vectorstore import search_hybrid


class TestHybridSearchAndReranker(unittest.TestCase):
    def test_compute_rrf_score(self):
        # Item present in both dense (rank 1) and sparse (rank 2)
        score_both = compute_rrf_score(dense_rank=1, sparse_rank=2, k=60)
        # 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.01639 + 0.01613 = ~0.03252
        self.assertAlmostEqual(score_both, (1 / 61) + (1 / 62), places=5)

        # Item present only in dense (rank 1)
        score_dense_only = compute_rrf_score(dense_rank=1, sparse_rank=None, k=60)
        self.assertAlmostEqual(score_dense_only, 1 / 61, places=5)

    def test_reranker_fallback_on_llm_exception(self):
        passages = [
            {"chunk_text": "Battery specifications 5000mAh", "title": "Specs", "rrf_score": 0.032},
            {"chunk_text": "Irrelevant shipping note", "title": "Shipping", "rrf_score": 0.015},
            {"chunk_text": "Charging cable replacement policy", "title": "Warranty", "rrf_score": 0.028},
        ]
        # Simulate LLM failure
        with patch("app.ai.reranker.get_reranker_llm", side_effect=Exception("API unavailable")):
            reranked = rerank_passages(query="What is the battery capacity?", passages=passages, top_k=2)

        self.assertEqual(len(reranked), 2)
        # Falls back to rrf_score order: 0.032, then 0.028
        self.assertEqual(reranked[0]["title"], "Specs")
        self.assertEqual(reranked[1]["title"], "Warranty")

    @patch("app.vectorstore.embed_text", return_value=[0.1] * 768)
    @patch("app.db.connect")
    def test_search_hybrid_formats_page_number_if_present(self, mock_connect, mock_embed):
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn

        # Dense results
        mock_conn.execute.return_value.fetchall.side_effect = [
            # First call: dense search
            [
                {
                    "id": 1,
                    "chunk_text": "Battery details",
                    "title": "Nexa One Manual.pdf",
                    "sec": "smartphone",
                    "metadata": {"page": 7, "source_type": "pdf"},
                    "similarity": 0.92,
                }
            ],
            # Second call: sparse search
            [
                {
                    "id": 1,
                    "chunk_text": "Battery details",
                    "title": "Nexa One Manual.pdf",
                    "sec": "smartphone",
                    "metadata": {"page": 7, "source_type": "pdf"},
                    "fts_rank": 0.85,
                }
            ],
        ]

        with patch("app.ai.reranker.get_reranker_llm", side_effect=Exception("offline")):
            results = search_hybrid(query="How long does battery last?", section="smartphone", top_k=1)

        self.assertEqual(len(results), 1)
        self.assertIn("Page 7", results[0])
        self.assertIn("Nexa One Manual.pdf", results[0])
        self.assertIn("Battery details", results[0])


if __name__ == "__main__":
    unittest.main()

