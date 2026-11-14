import unittest
from datetime import datetime, timedelta, timezone

from app.services.enterprise import (
    EnterpriseService,
    get_carrier_tracking,
    get_customer_profile,
    issue_replacement_order,
    issue_store_credit_or_refund,
    lookup_order,
    create_rma,
    verify_warranty_status,
)


class TestEnterpriseService(unittest.TestCase):
    def setUp(self):
        self.service = EnterpriseService(use_db=False)
        self.service.seed_fixtures()

    def test_get_customer_profile_found(self):
        profile = self.service.get_customer_profile("john.doe@example.com")
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "John Doe")
        self.assertEqual(profile["loyalty_tier"], "vip")

    def test_get_customer_profile_not_found(self):
        profile = self.service.get_customer_profile("nonexistent@example.com")
        self.assertIsNone(profile)

    def test_lookup_order_success(self):
        order = self.service.lookup_order("NX-1001", "john.doe@example.com")
        self.assertIsNotNone(order)
        self.assertEqual(order["order_id"], "NX-1001")
        self.assertEqual(order["model"], "Nexa Phone Pro 12")
        self.assertGreater(len(order["items"]), 0)

    def test_lookup_order_email_mismatch(self):
        order = self.service.lookup_order("NX-1001", "wrong.email@example.com")
        self.assertIsNone(order)

    def test_carrier_tracking(self):
        tracking = self.service.get_carrier_tracking("FedEx", "TRK-992144")
        self.assertIn("status", tracking)
        self.assertEqual(tracking["carrier"], "FedEx")
        self.assertIn("checkpoints", tracking)

    def test_verify_warranty_active(self):
        warranty = self.service.verify_warranty_status("NX-1001")
        self.assertTrue(warranty["is_covered"])
        self.assertEqual(warranty["status"], "active")

    def test_verify_warranty_expired(self):
        warranty = self.service.verify_warranty_status("NX-1004")
        self.assertFalse(warranty["is_covered"])
        self.assertEqual(warranty["status"], "expired")

    def test_create_rma(self):
        rma = self.service.create_rma(
            order_id="NX-1001",
            reason="Defective display flickering",
            items=["SKU-NEXA-PRO12-256"],
        )
        self.assertIn("rma_id", rma)
        self.assertTrue(rma["rma_id"].startswith("RMA-NX-"))
        self.assertIn("return_label_url", rma)
        self.assertEqual(rma["status"], "label_generated")

    def test_issue_replacement_order(self):
        replacement = self.service.issue_replacement_order(
            order_id="NX-1002",
            sku="SKU-ACC-65W-CHG",
            reason="Frayed charging cable",
        )
        self.assertIn("replacement_order_id", replacement)
        self.assertEqual(replacement["status"], "dispatched")

    def test_issue_store_credit_or_refund(self):
        refund = self.service.issue_store_credit_or_refund(
            order_id="NX-1001",
            amount_usd=25.0,
            reason="Customer courtesy discount for shipping delay",
        )
        self.assertIn("refund_id", refund)
        self.assertEqual(refund["amount_usd"], 25.0)
        self.assertEqual(refund["status"], "processed")

    def test_module_level_helpers(self):
        customer = get_customer_profile("john.doe@example.com")
        self.assertIsNotNone(customer)
        order = lookup_order("NX-1001")
        self.assertIsNotNone(order)


if __name__ == "__main__":
    unittest.main()

