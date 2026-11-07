import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.guards import grade_documents, verify_grounding


class TestHallucinationGuardrail(unittest.TestCase):
    """Test suite for Guardrail 1: Hallucination Prevention & Context Grounding."""

    def test_grade_documents_relevant(self):
        """Relevant documents matching query terms must pass grading."""
        query = "My Nexa One phone charges very slowly with the original cable"
        docs = [
            "## Battery and charging issues\nIf the phone charges slowly:\n1. Check cable connection.\n2. Try another USB-C cable.",
            "## Charger compatibility\nNexa One supports up to 33W fast charging.",
        ]
        self.assertTrue(grade_documents(query, docs))

    def test_grade_documents_irrelevant_rejected(self):
        """Documents with zero semantic overlap to the query must be rejected."""
        query = "My display has flickering lines and dead pixels on screen"
        docs = [
            "## Shipping charges\nAmazon handles all delivery charges at checkout.",
            "## Amazon fulfillment and order processing\nAll orders are fulfilled by Amazon logistics.",
        ]
        self.assertFalse(grade_documents(query, docs))

    def test_grade_documents_empty(self):
        """Empty documents or blank text must fail grading."""
        self.assertFalse(grade_documents("Any query", []))
        self.assertFalse(grade_documents("Any query", ["   ", "\n\n"]))

    def test_verify_grounding_valid_response(self):
        """Grounded response adhering to official facts must pass."""
        reply = (
            "Nexa smartphones include a 1-year limited manufacturer warranty from the date of purchase. "
            "It covers manufacturing defects in internal components.\n\nNexa Mobile Support"
        )
        docs = ["## Smartphone warranty coverage\nAll Nexa smartphones include a 1-year limited warranty."]
        is_grounded, msg = verify_grounding(reply, docs, "returns-and-warranty")
        self.assertTrue(is_grounded)
        self.assertEqual(msg, "")

    def test_verify_grounding_detects_invented_warranty_duration(self):
        """Invented warranty durations (e.g., 2-year or lifetime) must be caught."""
        hallucinated_replies = [
            "All Nexa phones come with our exclusive 2-year warranty.\n\nNexa Mobile Support",
            "You are covered by our lifetime warranty against all failures.\n\nNexa Mobile Support",
            "We offer a 3-year warranty on all smartphones.\n\nNexa Mobile Support",
        ]
        docs = ["## Smartphone warranty coverage\nAll Nexa smartphones include a 1-year limited warranty."]
        for reply in hallucinated_replies:
            is_grounded, msg = verify_grounding(reply, docs, "returns-and-warranty")
            self.assertFalse(is_grounded)
            self.assertIn("Hallucinated warranty duration", msg)

    def test_verify_grounding_detects_false_coverage_claims(self):
        """Claims that excluded damages (water, drops) are covered must be caught."""
        hallucinated_replies = [
            "Do not worry, water damage is covered under your standard warranty.\n\nNexa Mobile Support",
            "Your cracked screen is covered under warranty and will be repaired.\n\nNexa Mobile Support",
            "Accidental damage is covered under our policy.\n\nNexa Mobile Support",
        ]
        docs = ["## Warranty exclusions\nAccidental drops, cracked screens, and liquid damage are not covered."]
        for reply in hallucinated_replies:
            is_grounded, msg = verify_grounding(reply, docs, "returns-and-warranty")
            self.assertFalse(is_grounded)
            self.assertIn("False warranty coverage assertion", msg)

    def test_verify_grounding_detects_invented_return_window(self):
        """Claims of non-existent 60-day or 90-day return windows must be caught."""
        reply = "You can return your phone within our 60-day return window on Amazon.\n\nNexa Mobile Support"
        docs = ["## Return policy\nAmazon provides a 30-day return window."]
        is_grounded, msg = verify_grounding(reply, docs, "returns-and-warranty")
        self.assertFalse(is_grounded)
        self.assertIn("Hallucinated return window", msg)

    def test_verify_grounding_detects_invented_models(self):
        """Mentions of non-existent smartphone models must be caught."""
        reply = "We recommend checking out the new Nexa Ultra with satellite connectivity.\n\nNexa Mobile Support"
        docs = ["## Product lineup\nNexa One, Nexa One Pro, and Nexa Lite."]
        is_grounded, msg = verify_grounding(reply, docs, "smartphone")
        self.assertFalse(is_grounded)
        self.assertIn("Hallucinated product model", msg)


if __name__ == "__main__":
    unittest.main()

