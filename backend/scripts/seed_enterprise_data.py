import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app import db
from app.services.enterprise import EnterpriseService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_enterprise_data")


def seed_database():
    logger.info("Initializing Enterprise mock data generator...")
    service = EnterpriseService(use_db=False)
    service.seed_fixtures()

    now = datetime.now(timezone.utc)

    try:
        logger.info("Connecting to Supabase PostgreSQL database...")
        with db.connect() as conn:
            # 1. Seed Customers
            logger.info("Seeding customers table...")
            for email, cust in service._customers.items():
                conn.execute(
                    """
                    insert into customers (email, name, loyalty_tier, churn_risk_score, created_at)
                    values (%s, %s, %s, %s, %s)
                    on conflict (email) do update
                    set name = excluded.name,
                        loyalty_tier = excluded.loyalty_tier,
                        churn_risk_score = excluded.churn_risk_score
                    """,
                    (
                        cust["email"],
                        cust["name"],
                        cust["loyalty_tier"],
                        cust["churn_risk_score"],
                        cust["created_at"],
                    ),
                )
                logger.info("  ✓ Seeded customer: %s (%s)", cust["name"], email)

            # 2. Seed Orders
            logger.info("Seeding orders table...")
            for order_id, order in service._orders.items():
                conn.execute(
                    """
                    insert into orders (
                        order_id, customer_email, purchase_date, model, status,
                        serial_number, carrier, tracking_number, warranty_end_date
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    on conflict (order_id) do update
                    set status = excluded.status,
                        carrier = excluded.carrier,
                        tracking_number = excluded.tracking_number,
                        warranty_end_date = excluded.warranty_end_date
                    """,
                    (
                        order["order_id"],
                        order["customer_email"],
                        order["purchase_date"],
                        order["model"],
                        order["status"],
                        order["serial_number"],
                        order["carrier"],
                        order["tracking_number"],
                        order["warranty_end_date"],
                    ),
                )
                logger.info("  ✓ Seeded order: %s [%s] for %s", order_id, order["model"], order["customer_email"])

            # 3. Seed Order Items
            logger.info("Seeding order_items table...")
            for order_id, items in service._order_items.items():
                # Clear existing items for idempotency
                conn.execute("delete from order_items where order_id = %s", (order_id,))
                for item in items:
                    conn.execute(
                        """
                        insert into order_items (order_id, sku, title, unit_price_cents, is_accessory)
                        values (%s, %s, %s, %s, %s)
                        """,
                        (
                            order_id,
                            item["sku"],
                            item["title"],
                            item["unit_price_cents"],
                            item["is_accessory"],
                        ),
                    )
                logger.info("  ✓ Seeded %d items for order %s", len(items), order_id)

        logger.info("✅ Successfully seeded enterprise CRM, orders, and inventory tables in PostgreSQL!")

    except Exception as e:
        logger.warning(
            "⚠️ Database write skipped or unconnectable (offline / sandbox environment): %s. "
            "EnterpriseService in-memory fallback will continue serving mock data.",
            e,
        )


if __name__ == "__main__":
    seed_database()

