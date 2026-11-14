import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app import db

logger = logging.getLogger(__name__)


class EnterpriseService:
    """Enterprise service layer managing CRM, Orders, Logistics, RMA, and Warranty data."""

    def __init__(self, use_db: bool = True):
        self.use_db = use_db
        self._customers: Dict[str, dict] = {}
        self._orders: Dict[str, dict] = {}
        self._order_items: Dict[str, List[dict]] = {}
        self._rmas: Dict[str, dict] = {}
        self._refunds: Dict[str, dict] = {}
        self._replacements: Dict[str, dict] = {}
        self.seed_fixtures()

    def seed_fixtures(self) -> None:
        """Seed realistic in-memory test data for Nexa Mobile."""
        now = datetime.now(timezone.utc)

        # Customers
        self._customers["john.doe@example.com"] = {
            "email": "john.doe@example.com",
            "name": "John Doe",
            "loyalty_tier": "vip",
            "churn_risk_score": 0.05,
            "created_at": (now - timedelta(days=120)).isoformat(),
        }
        self._customers["sarah.smith@example.com"] = {
            "email": "sarah.smith@example.com",
            "name": "Sarah Smith",
            "loyalty_tier": "standard",
            "churn_risk_score": 0.2,
            "created_at": (now - timedelta(days=60)).isoformat(),
        }
        self._customers["hazard.user@example.com"] = {
            "email": "hazard.user@example.com",
            "name": "Alex Vance",
            "loyalty_tier": "standard",
            "churn_risk_score": 0.5,
            "created_at": (now - timedelta(days=30)).isoformat(),
        }
        self._customers["out.of.policy@example.com"] = {
            "email": "out.of.policy@example.com",
            "name": "Michael Brown",
            "loyalty_tier": "standard",
            "churn_risk_score": 0.4,
            "created_at": (now - timedelta(days=200)).isoformat(),
        }

        # Order 1: Recent Phone (Active Warranty, Delivered 14 days ago)
        self._orders["NX-1001"] = {
            "order_id": "NX-1001",
            "customer_email": "john.doe@example.com",
            "purchase_date": (now - timedelta(days=14)).isoformat(),
            "model": "Nexa Phone Pro 12",
            "status": "delivered",
            "serial_number": "NXPRO12-SN-883921",
            "carrier": "FedEx",
            "tracking_number": "TRK-992144",
            "warranty_end_date": (now + timedelta(days=351)).isoformat(),
        }
        self._order_items["NX-1001"] = [
            {
                "sku": "SKU-NEXA-PRO12-256",
                "title": "Nexa Phone Pro 12 (256GB - Midnight Blue)",
                "unit_price_cents": 89900,
                "is_accessory": False,
            },
            {
                "sku": "SKU-ACC-CASE-CL",
                "title": "Nexa Armor Shockproof Case",
                "unit_price_cents": 2999,
                "is_accessory": True,
            },
        ]

        # Order 2: Accessory (Delivered 45 days ago, Active 1-yr Warranty)
        self._orders["NX-1002"] = {
            "order_id": "NX-1002",
            "customer_email": "sarah.smith@example.com",
            "purchase_date": (now - timedelta(days=45)).isoformat(),
            "model": "Nexa 65W Fast Charger Kit",
            "status": "delivered",
            "serial_number": "CHG65-SN-10928",
            "carrier": "UPS",
            "tracking_number": "1Z999AA10123456784",
            "warranty_end_date": (now + timedelta(days=320)).isoformat(),
        }
        self._order_items["NX-1002"] = [
            {
                "sku": "SKU-ACC-65W-CHG",
                "title": "Nexa 65W Dual-Port GaN Fast Charger + 2m Braided Cable",
                "unit_price_cents": 2499,
                "is_accessory": True,
            }
        ]

        # Order 3: Phone with Hazard Report (Delivered 20 days ago)
        self._orders["NX-1003"] = {
            "order_id": "NX-1003",
            "customer_email": "hazard.user@example.com",
            "purchase_date": (now - timedelta(days=20)).isoformat(),
            "model": "Nexa Phone Pro 12",
            "status": "delivered",
            "serial_number": "NXPRO12-SN-772109",
            "carrier": "Amazon Logistics",
            "tracking_number": "TBA0918237192",
            "warranty_end_date": (now + timedelta(days=345)).isoformat(),
        }
        self._order_items["NX-1003"] = [
            {
                "sku": "SKU-NEXA-PRO12-128",
                "title": "Nexa Phone Pro 12 (128GB - Phantom Gray)",
                "unit_price_cents": 79900,
                "is_accessory": False,
            }
        ]

        # Order 4: Expired Warranty & Outside Return Policy (Purchased 400 days ago)
        self._orders["NX-1004"] = {
            "order_id": "NX-1004",
            "customer_email": "out.of.policy@example.com",
            "purchase_date": (now - timedelta(days=400)).isoformat(),
            "model": "Nexa Earbuds Active",
            "status": "delivered",
            "serial_number": "EAR-SN-00129",
            "carrier": "USPS",
            "tracking_number": "9400100000000000000000",
            "warranty_end_date": (now - timedelta(days=35)).isoformat(),
        }
        self._order_items["NX-1004"] = [
            {
                "sku": "SKU-ACC-EAR-BUDS",
                "title": "Nexa Earbuds Active Wireless",
                "unit_price_cents": 4999,
                "is_accessory": True,
            }
        ]

    def get_customer_profile(self, email: str) -> Optional[dict]:
        """Fetch customer CRM profile by email."""
        norm_email = email.strip().lower()
        if self.use_db:
            try:
                row = db.get_customer(norm_email)
                if row:
                    return dict(row)
            except Exception as e:
                logger.warning("DB read failed for customer %s, using memory: %s", norm_email, e)

        return self._customers.get(norm_email)

    def lookup_order(self, order_id: str, email: Optional[str] = None) -> Optional[dict]:
        """Fetch order details, items, and verification status."""
        norm_id = order_id.strip().upper()
        norm_email = email.strip().lower() if email else None

        order: Optional[dict] = None
        if self.use_db:
            try:
                row = db.get_order(norm_id, norm_email)
                if row:
                    order = dict(row)
                    items = db.get_order_items(norm_id)
                    order["items"] = [dict(i) for i in items]
            except Exception as e:
                logger.warning("DB read failed for order %s, using memory: %s", norm_id, e)

        if not order:
            mem_order = self._orders.get(norm_id)
            if mem_order:
                if norm_email and mem_order["customer_email"].lower() != norm_email:
                    return None
                order = dict(mem_order)
                order["items"] = list(self._order_items.get(norm_id, []))

        return order

    def get_carrier_tracking(self, carrier: str, tracking_number: str) -> dict:
        """Simulate real-time shipping carrier tracking status."""
        norm_trk = tracking_number.strip()
        return {
            "carrier": carrier,
            "tracking_number": norm_trk,
            "status": "delivered",
            "delivered_at": (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d %H:%M UTC"),
            "delivery_address_city": "Seattle, WA",
            "signed_by": "Front Door / Resident",
            "checkpoints": [
                {"timestamp": "2026-11-10 09:12", "location": "Seattle, WA", "status": "Delivered"},
                {"timestamp": "2026-11-10 06:45", "location": "Seattle, WA", "status": "Out for delivery"},
                {"timestamp": "2026-11-09 21:30", "location": "Kent, WA", "status": "Arrived at sorting hub"},
            ],
        }

    def verify_warranty_status(self, order_id: str) -> dict:
        """Verify whether an order/item is covered under Nexa's 1-year limited warranty."""
        order = self.lookup_order(order_id)
        if not order:
            return {"order_id": order_id, "is_covered": False, "status": "order_not_found"}

        warranty_end_raw = order.get("warranty_end_date")
        if not warranty_end_raw:
            return {"order_id": order_id, "is_covered": False, "status": "no_warranty_record"}

        if isinstance(warranty_end_raw, str):
            warranty_end = datetime.fromisoformat(warranty_end_raw.replace("Z", "+00:00"))
        else:
            warranty_end = warranty_end_raw

        now = datetime.now(timezone.utc)
        is_covered = warranty_end > now
        days_remaining = (warranty_end - now).days if is_covered else 0

        return {
            "order_id": order["order_id"],
            "model": order["model"],
            "serial_number": order.get("serial_number"),
            "is_covered": is_covered,
            "status": "active" if is_covered else "expired",
            "warranty_end_date": warranty_end.strftime("%Y-%m-%d"),
            "days_remaining": days_remaining,
            "policy": "1-year limited manufacturer warranty against defects in materials and workmanship.",
        }

    def create_rma(self, order_id: str, reason: str, items: List[str]) -> dict:
        """Create a Return Merchandise Authorization (RMA) and return prepaid shipping label."""
        order = self.lookup_order(order_id)
        customer_email = order["customer_email"] if order else "customer@example.com"
        rma_id = f"RMA-NX-{uuid.uuid4().hex[:8].upper()}"
        label_url = f"https://returns.nexamobile.com/labels/{rma_id}.pdf"

        rma_record = {
            "rma_id": rma_id,
            "order_id": order_id.upper(),
            "customer_email": customer_email,
            "status": "label_generated",
            "reason": reason,
            "items": items,
            "return_label_url": label_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "instructions": (
                "Please print the attached prepaid return label, affix it to the packaging, "
                "and drop the package off at any authorized FedEx or Amazon Return drop-off location."
            ),
        }

        if self.use_db:
            try:
                db.create_rma_record(
                    rma_id=rma_id,
                    order_id=order_id,
                    customer_email=customer_email,
                    status="label_generated",
                    reason=reason,
                    return_label_url=label_url,
                )
            except Exception as e:
                logger.warning("DB insert failed for RMA %s: %s", rma_id, e)

        self._rmas[rma_id] = rma_record
        return rma_record

    def issue_replacement_order(self, order_id: str, sku: str, reason: str) -> dict:
        """Issue an immediate warranty replacement order for defective accessories or parts."""
        order = self.lookup_order(order_id)
        replacement_id = f"REPL-NX-{uuid.uuid4().hex[:8].upper()}"
        tracking_num = f"TRK-REPL-{uuid.uuid4().hex[:6].upper()}"

        record = {
            "replacement_order_id": replacement_id,
            "original_order_id": order_id.upper(),
            "sku": sku,
            "status": "dispatched",
            "carrier": "FedEx Express 2-Day",
            "tracking_number": tracking_num,
            "reason": reason,
            "dispatched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d"),
        }
        self._replacements[replacement_id] = record
        return record

    def issue_store_credit_or_refund(self, order_id: str, amount_usd: float, reason: str) -> dict:
        """Issue a refund or courtesy credit for an order."""
        refund_id = f"REF-NX-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "refund_id": refund_id,
            "order_id": order_id.upper(),
            "amount_usd": round(amount_usd, 2),
            "status": "processed",
            "reason": reason,
            "processed_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        self._refunds[refund_id] = record
        return record


# Global default instance
default_enterprise_service = EnterpriseService()


def get_customer_profile(email: str) -> Optional[dict]:
    return default_enterprise_service.get_customer_profile(email)


def lookup_order(order_id: str, email: Optional[str] = None) -> Optional[dict]:
    return default_enterprise_service.lookup_order(order_id, email)


def get_carrier_tracking(carrier: str, tracking_number: str) -> dict:
    return default_enterprise_service.get_carrier_tracking(carrier, tracking_number)


def verify_warranty_status(order_id: str) -> dict:
    return default_enterprise_service.verify_warranty_status(order_id)


def create_rma(order_id: str, reason: str, items: List[str]) -> dict:
    return default_enterprise_service.create_rma(order_id, reason, items)


def issue_replacement_order(order_id: str, sku: str, reason: str) -> dict:
    return default_enterprise_service.issue_replacement_order(order_id, sku, reason)


def issue_store_credit_or_refund(order_id: str, amount_usd: float, reason: str) -> dict:
    return default_enterprise_service.issue_store_credit_or_refund(order_id, amount_usd, reason)

