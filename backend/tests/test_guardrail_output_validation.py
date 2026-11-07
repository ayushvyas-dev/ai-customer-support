import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.guards import (
    DEFAULT_ESCALATION_ACKNOWLEDGEMENT,
    sanitize_output,
    validate_output,
)


class TestOutputValidationGuardrail(unittest.TestCase):
    """Test suite for Guardrail 5: Output Validation, Formatting & Escalation Standards."""

    def test_validate_output_valid_response(self):
        """A complete, well-formed response without defects must pass validation."""
        valid_reply = (
            "Hello Oliver,\n\nAll Nexa smartphones include a 1-year limited manufacturer warranty "
            "covering internal hardware and battery defects. Valid proof of purchase from Amazon is required.\n\n"
            "Nexa Mobile Support"
        )
        is_valid, msg = validate_output(valid_reply)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_validate_output_rejects_empty_or_too_short(self):
        """Empty or excessively short responses must fail validation."""
        bad_replies = ["", "   ", "Hello", "Too short!"]
        for reply in bad_replies:
            is_valid, msg = validate_output(reply)
            self.assertFalse(is_valid)
            self.assertIn("short or empty", msg.lower())

    def test_validate_output_detects_unresolved_placeholders(self):
        """Draft placeholders like [Insert Name] or TODO must fail validation."""
        bad_replies = [
            "Hello [Customer Name], please restart your Nexa One.\n\nNexa Mobile Support",
            "Dear customer, your order [Order Number] is being investigated.\n\nNexa Mobile Support",
            "Please try the steps outlined below. TODO: add camera instructions.\n\nNexa Mobile Support",
            "Hello {name}, thank you for contacting Nexa.\n\nNexa Mobile Support",
            "Your repair date is TBD by our service team.\n\nNexa Mobile Support",
        ]
        for reply in bad_replies:
            is_valid, msg = validate_output(reply)
            self.assertFalse(is_valid)
            self.assertIn("Unresolved placeholder detected", msg)

    def test_validate_output_detects_outbound_pii_leak(self):
        """Outbound replies that inadvertently leak credit cards or API keys must fail validation."""
        leaky_reply = (
            "We verified your payment with card 4532 0150 0000 0048. Please wait.\n\n"
            "Nexa Mobile Support"
        )
        is_valid, msg = validate_output(leaky_reply)
        self.assertFalse(is_valid)
        self.assertIn("Outbound reply contains sensitive PII", msg)

    def test_sanitize_output_cleans_forbidden_ai_mentions(self):
        """Forbidden terms like 'AI' or 'knowledge base' must be sanitized."""
        dirty_reply = (
            "According to our knowledge base, the Nexa One supports 33W charging. "
            "As an AI, I am here to help.\n\nNexa Mobile Support"
        )
        cleaned = sanitize_output(dirty_reply)
        self.assertNotIn("knowledge base", cleaned.lower())
        self.assertNotIn("as an ai", cleaned.lower())
        self.assertIn("support team", cleaned.lower())

    def test_sanitize_output_enforces_required_signoff(self):
        """Replies missing the required corporate sign-off must have it appended."""
        reply_without_signoff = "Please disconnect the charger and restart your device for 10 seconds."
        cleaned = sanitize_output(reply_without_signoff)
        self.assertTrue(cleaned.endswith("Nexa Mobile Support"))

    def test_default_escalation_acknowledgement_compliance(self):
        """Default escalation message must satisfy brand tone, SLA, and sign-off standards."""
        self.assertIn("Nexa Mobile", DEFAULT_ESCALATION_ACKNOWLEDGEMENT)
        self.assertIn("one business day", DEFAULT_ESCALATION_ACKNOWLEDGEMENT)
        self.assertIn("Nexa Mobile Support", DEFAULT_ESCALATION_ACKNOWLEDGEMENT)
        self.assertNotIn("AI", DEFAULT_ESCALATION_ACKNOWLEDGEMENT)


if __name__ == "__main__":
    unittest.main()

