import unittest
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.guards import detect_unauthorized_commitments


class TestBusinessRulesGuardrail(unittest.TestCase):
    """Test suite for Guardrail 4: Business Rule & Commitment Enforcement."""

    def test_detect_unauthorized_refund_promises(self):
        """Promises to issue, approve, or disburse refunds must be intercepted."""
        violations = [
            "I have processed a full refund to your original payment method.\n\nNexa Mobile Support",
            "Your refund has been approved and the funds are on their way.\n\nNexa Mobile Support",
            "We will refund the amount of Rs. 24,999 to your card immediately.\n\nNexa Mobile Support",
            "I will credit the amount back to your bank account.\n\nNexa Mobile Support",
        ]
        for violation in violations:
            has_commitment, reason = detect_unauthorized_commitments(violation)
            self.assertTrue(has_commitment, f"Failed to detect: {violation}")
            self.assertIn("refund", reason.lower())

    def test_detect_unauthorized_discount_and_coupon_promises(self):
        """Promises of discount codes, promo codes, or free credits must be caught."""
        violations = [
            "As an apology, please use discount code 'SAVE50' for 50% off your next purchase.\n\nNexa Mobile Support",
            "Here is a promo code 'FREE100' for a free accessory.\n\nNexa Mobile Support",
            "We can offer you a 25% discount on the Nexa One Pro.\n\nNexa Mobile Support",
            "I have applied a free credit of Rs. 1000 to your account.\n\nNexa Mobile Support",
        ]
        for violation in violations:
            has_commitment, reason = detect_unauthorized_commitments(violation)
            self.assertTrue(has_commitment, f"Failed to detect: {violation}")
            self.assertIn("discount", reason.lower())

    def test_detect_unauthorized_order_cancellation_promises(self):
        """Promises that the bot cancelled or will cancel an order must be caught."""
        violations = [
            "I have cancelled your order 112-5520341-0093312 as requested.\n\nNexa Mobile Support",
            "We will cancel the order for you before dispatch.\n\nNexa Mobile Support",
            "Your cancellation has been confirmed.\n\nNexa Mobile Support",
        ]
        for violation in violations:
            has_commitment, reason = detect_unauthorized_commitments(violation)
            self.assertTrue(has_commitment, f"Failed to detect: {violation}")
            self.assertIn("cancellation", reason.lower())

    def test_detect_unauthorized_free_replacement_promises(self):
        """Promises to ship free replacement phones or accessories must be caught."""
        violations = [
            "We will send you a free replacement phone right away.\n\nNexa Mobile Support",
            "Your replacement unit has been dispatched and is on the way.\n\nNexa Mobile Support",
            "I am shipping you a free charger to resolve this issue.\n\nNexa Mobile Support",
        ]
        for violation in violations:
            has_commitment, reason = detect_unauthorized_commitments(violation)
            self.assertTrue(has_commitment, f"Failed to detect: {violation}")
            self.assertIn("replacement", reason.lower())

    def test_detect_unauthorized_phone_call_promises(self):
        """Promises that a colleague or manager will call the customer must be caught."""
        violations = [
            "Our support team will call you on your phone tomorrow morning.\n\nNexa Mobile Support",
            "I will arrange a phone call with our technical supervisor.\n\nNexa Mobile Support",
            "A manager shall call you at 4 PM to discuss this.\n\nNexa Mobile Support",
        ]
        for violation in violations:
            has_commitment, reason = detect_unauthorized_commitments(violation)
            self.assertTrue(has_commitment, f"Failed to detect: {violation}")
            self.assertIn("callback", reason.lower())

    def test_legitimate_policy_explanations_are_permitted(self):
        """Explaining official Amazon return and refund procedures without promising them must be allowed."""
        permitted_responses = [
            (
                "You can check return and refund eligibility directly on Amazon by visiting: "
                "Amazon > Your Orders > Select the Nexa product > Return or Replace Items.\n\nNexa Mobile Support"
            ),
            (
                "Nexa customer support cannot directly issue refunds. A colleague will review your order details.\n\n"
                "Nexa Mobile Support"
            ),
            (
                "To troubleshoot slow charging, please verify that your USB-C cable is fully plugged into the wall charger.\n\n"
                "Nexa Mobile Support"
            ),
        ]
        for resp in permitted_responses:
            has_commitment, reason = detect_unauthorized_commitments(resp)
            self.assertFalse(has_commitment, f"Legitimate response was falsely flagged: {resp} (Reason: {reason})")

    def test_authorized_refund_with_executed_tool_is_permitted(self):
        """When tool_request_refund has executed, refund statements are permitted as authorized commitments."""
        reply = "We have processed a courtesy refund of $25.00 for your order NX-1001.\n\nNexa Mobile Support"
        executed_tools = [{"tool": "tool_request_refund", "result": '{"status": "processed"}'}]
        has_commitment, reason = detect_unauthorized_commitments(reply, executed_tools=executed_tools)
        self.assertFalse(has_commitment, f"Authorized refund was falsely flagged: {reason}")

    def test_authorized_replacement_with_executed_tool_is_permitted(self):
        """When tool_dispatch_replacement has executed, replacement dispatch statements are permitted."""
        reply = "Your replacement unit has been dispatched and is on the way via FedEx.\n\nNexa Mobile Support"
        executed_tools = [{"tool": "tool_dispatch_replacement", "result": '{"status": "dispatched"}'}]
        has_commitment, reason = detect_unauthorized_commitments(reply, executed_tools=executed_tools)
        self.assertFalse(has_commitment, f"Authorized replacement was falsely flagged: {reason}")

    def test_rejected_tool_fails_commitment_check(self):
        """When a refund tool was rejected by supervisor, the refund commitment remains unauthorized."""
        reply = "We have processed a full refund to your original payment method.\n\nNexa Mobile Support"
        executed_tools = [{"tool": "tool_request_refund", "status": "rejected"}]
        has_commitment, reason = detect_unauthorized_commitments(reply, executed_tools=executed_tools)
        self.assertTrue(has_commitment, "Rejected refund was improperly allowed")


if __name__ == "__main__":
    unittest.main()

