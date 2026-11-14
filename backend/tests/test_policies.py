import unittest
from datetime import datetime, timedelta, timezone

from app.ai.policies import PolicyDecision, evaluate_action_policy


class TestActionPolicies(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.recent_order = {
            "order_id": "NX-1001",
            "purchase_date": (self.now - timedelta(days=10)).isoformat(),
            "model": "Nexa Phone Pro 12",
        }
        self.old_order = {
            "order_id": "NX-1004",
            "purchase_date": (self.now - timedelta(days=90)).isoformat(),
            "model": "Nexa Earbuds Active",
        }

    def test_lookup_and_tracking_are_tier1_autonomous(self):
        p1 = evaluate_action_policy("tool_lookup_order", {"order_id": "NX-1001"})
        self.assertEqual(p1.tier, "tier_1")
        self.assertFalse(p1.requires_approval)

        p2 = evaluate_action_policy(
            "tool_track_package", {"carrier": "FedEx", "tracking_number": "TRK-123"}
        )
        self.assertEqual(p2.tier, "tier_1")
        self.assertFalse(p2.requires_approval)

    def test_kb_search_is_tier1(self):
        p = evaluate_action_policy("tool_search_knowledge_base", {"query": "battery troubleshooting"})
        self.assertEqual(p.tier, "tier_1")
        self.assertFalse(p.requires_approval)

    def test_rma_return_within_30_days_is_tier1(self):
        p = evaluate_action_policy(
            "tool_request_rma_return",
            {"order_id": "NX-1001", "reason": "Defective port", "items": ["SKU-1"]},
            order=self.recent_order,
        )
        self.assertEqual(p.tier, "tier_1")
        self.assertFalse(p.requires_approval)

    def test_rma_return_outside_30_days_is_tier2_hitl(self):
        p = evaluate_action_policy(
            "tool_request_rma_return",
            {"order_id": "NX-1004", "reason": "Changed mind", "items": ["SKU-4"]},
            order=self.old_order,
        )
        self.assertEqual(p.tier, "tier_2")
        self.assertTrue(p.requires_approval)
        self.assertIn("30-day", p.reason)

    def test_low_cost_accessory_replacement_is_tier1(self):
        p = evaluate_action_policy(
            "tool_dispatch_replacement",
            {"order_id": "NX-1002", "sku": "SKU-ACC-65W-CHG", "reason": "Frayed wire"},
            item_price_cents=2499,
            is_accessory=True,
        )
        self.assertEqual(p.tier, "tier_1")
        self.assertFalse(p.requires_approval)

    def test_phone_replacement_is_tier2_hitl(self):
        p = evaluate_action_policy(
            "tool_dispatch_replacement",
            {"order_id": "NX-1001", "sku": "SKU-NEXA-PRO12-256", "reason": "Broken screen"},
            item_price_cents=89900,
            is_accessory=False,
        )
        self.assertEqual(p.tier, "tier_2")
        self.assertTrue(p.requires_approval)

    def test_refund_is_tier2_hitl(self):
        p = evaluate_action_policy(
            "tool_request_refund",
            {"order_id": "NX-1001", "amount_usd": 50.0, "reason": "Customer dissatisfied"},
        )
        self.assertEqual(p.tier, "tier_2")
        self.assertTrue(p.requires_approval)

    def test_safety_hazard_forces_tier2_urgent(self):
        p = evaluate_action_policy(
            "tool_dispatch_replacement",
            {"order_id": "NX-1003", "sku": "SKU-PRO12", "reason": "Battery swelling and smoke"},
        )
        self.assertEqual(p.tier, "tier_2")
        self.assertTrue(p.requires_approval)
        self.assertIn("Safety", p.reason)


if __name__ == "__main__":
    unittest.main()

