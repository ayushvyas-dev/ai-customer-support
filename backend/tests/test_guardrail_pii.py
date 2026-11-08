import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.guards import detect_pii, mask_pii


class TestPIIGuardrail(unittest.TestCase):
    """Test suite for Guardrail 3: PII (Personally Identifiable Information) Protection."""

    def test_mask_credit_cards(self):
        """Valid payment cards must be redacted while preserving Amazon order IDs."""
        # Valid Luhn Visa card: 4532 0150 0000 0048
        email_with_card = "Please refund to my card 4532-0150-0000-0048 for order 112-5520341-0093312."
        masked = mask_pii(email_with_card)
        self.assertNotIn("4532-0150-0000-0048", masked)
        self.assertIn("[REDACTED_CREDIT_CARD]", masked)
        # Amazon order number MUST be preserved
        self.assertIn("112-5520341-0093312", masked)

    def test_mask_cvv(self):
        """Card verification codes / CVVs must be redacted."""
        email_with_cvv = "My card security code is cvv: 842 and card is ready."
        masked = mask_pii(email_with_cvv)
        self.assertNotIn("842", masked)
        self.assertIn("[REDACTED_CVV]", masked)

    def test_mask_otp_codes(self):
        """One-time passwords (OTPs) and verification codes must be redacted."""
        email_with_otp = "Here is my one-time password OTP: 739201 to verify the account."
        masked = mask_pii(email_with_otp)
        self.assertNotIn("739201", masked)
        self.assertIn("[REDACTED_OTP]", masked)

    def test_mask_passwords(self):
        """Customer passwords must be redacted."""
        email_with_pwd = "My Amazon account password: SuperSecretP@ss123 please log in."
        masked = mask_pii(email_with_pwd)
        self.assertNotIn("SuperSecretP@ss123", masked)
        self.assertIn("[REDACTED_PASSWORD]", masked)

    def test_mask_ssn(self):
        """Social Security Numbers must be redacted."""
        email_with_ssn = "My SSN is 123-45-6789 for identity verification."
        masked = mask_pii(email_with_ssn)
        self.assertNotIn("123-45-6789", masked)
        self.assertIn("[REDACTED_SSN]", masked)

    def test_mask_internal_api_keys(self):
        """Internal API keys (Groq, Gemini, OpenAI) must be masked to prevent credential leaks."""
        text_with_keys = "API key: gsk_1234567890abcdefghijklmnopqrstuvwxyz"
        masked = mask_pii(text_with_keys)
        self.assertNotIn("gsk_1234567890abcdefghijklmnopqrstuvwxyz", masked)
        self.assertIn("[REDACTED_API_KEY]", masked)

    def test_detect_pii_identifies_types(self):
        """detect_pii must identify and classify each type of sensitive data present."""
        sample = "Card: 4532 0150 0000 0048, CVV: 991, OTP: 123456, Order 112-9988776-1234567"
        findings = detect_pii(sample)
        types_found = {f["type"] for f in findings}
        self.assertIn("credit_card", types_found)
        self.assertIn("cvv", types_found)
        self.assertIn("otp", types_found)
        # Order number must NOT be in findings as credit_card
        for f in findings:
            self.assertNotEqual(f["value"], "112-9988776-1234567")


if __name__ == "__main__":
    unittest.main()

