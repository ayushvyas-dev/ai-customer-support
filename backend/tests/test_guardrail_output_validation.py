import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.guards import (
    DEFAULT_ESCALATION_ACKNOWLEDGEMENT,
    extract_text_from_content,
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


    def test_extract_text_from_content_with_list_of_blocks(self):
        """LangChain content blocks from Gemini/multimodal LLMs must be cleanly parsed to text."""
        raw_blocks = [
            {
                "type": "text",
                "text": "Hello Ayush,\n\nTo return your smartphone, please follow the Amazon return portal.\n\nNexa Mobile Support",
                "extras": {"signature": "abc123xyz"},
            }
        ]
        extracted = extract_text_from_content(raw_blocks)
        self.assertNotIn("type", extracted)
        self.assertNotIn("signature", extracted)
        self.assertIn("Hello Ayush,", extracted)
        self.assertTrue(extracted.endswith("Nexa Mobile Support"))

    def test_extract_text_from_content_with_stringified_list(self):
        """Stringified representations of content blocks must also be unpacked cleanly."""
        stringified_raw = "[{'type': 'text', 'text': 'Hello Ayush,\\n\\nTo return your smartphone.\\n\\nNexa Mobile Support', 'extras': {'signature': '123'}}]"
        extracted = extract_text_from_content(stringified_raw)
        self.assertNotIn("{'type'", extracted)
        self.assertNotIn("'signature'", extracted)
        self.assertIn("Hello Ayush,", extracted)

    def test_extract_text_from_content_ignores_internal_thought_blocks(self):
        """Thinking tokens from reasoning models must never be included in outbound customer text."""
        raw_blocks_with_thought = [
            {"type": "thought", "thought": "The user wants a return. Looking up return policy."},
            {"type": "text", "text": "Hello customer, here is how you return.\n\nNexa Mobile Support"},
        ]
        extracted = extract_text_from_content(raw_blocks_with_thought)
        self.assertNotIn("Looking up return policy", extracted)
        self.assertIn("Hello customer, here is how you return.", extracted)

    def test_sanitize_output_cleans_structured_payloads(self):
        """Sanitizing a structured payload directly returns clean customer email prose."""
        raw_blocks = [
            {
                "type": "text",
                "text": "Hello Ayush,\n\nPlease follow the steps in your Amazon account.",
            }
        ]
        sanitized = sanitize_output(raw_blocks)
        self.assertNotIn("{'type'", sanitized)
        self.assertIn("Hello Ayush,", sanitized)
        self.assertTrue(sanitized.endswith("Nexa Mobile Support"))


if __name__ == "__main__":
    unittest.main()

