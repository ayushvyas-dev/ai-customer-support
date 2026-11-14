import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.config import settings


def connect() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, autocommit=True, row_factory=dict_row)


def start_event(gmail_message_id: str, max_attempts: int = 3) -> dict | None:
    """Claim a message. Returns None when it is already processed/skipped or exceeded max attempts."""
    with connect() as conn:
        return conn.execute(
            """
            insert into events (gmail_message_id) values (%s)
            on conflict (gmail_message_id) do update
              set attempts = events.attempts + 1, status = 'processing', error = null
              where events.status in ('failed', 'processing') and events.attempts < %s
            returning id, attempts
            """,
            (gmail_message_id, max_attempts),
        ).fetchone()


def is_event_completed(gmail_message_id: str, max_attempts: int = 3) -> bool:
    with connect() as conn:
        row = conn.execute(
            "select status, attempts from events where gmail_message_id = %s",
            (gmail_message_id,),
        ).fetchone()
        if not row:
            return False
        return row["status"] in ("processed", "skipped") or row["attempts"] >= max_attempts



def finish_event(event_id: int, status: str, result: dict) -> None:
    with connect() as conn:
        conn.execute(
            "update events set status = %s, result = %s, processed_at = now() where id = %s",
            (status, Jsonb(result), event_id),
        )


def fail_event(event_id: int, error: str) -> None:
    with connect() as conn:
        conn.execute(
            "update events set status = 'failed', error = %s where id = %s",
            (error, event_id),
        )


def upsert_ticket(gmail_thread_id: str, customer_email: str, subject: str) -> int:
    with connect() as conn:
        row = conn.execute(
            """
            insert into tickets (gmail_thread_id, customer_email, subject)
            values (%s, %s, %s)
            on conflict (gmail_thread_id) do update set updated_at = now()
            returning id
            """,
            (gmail_thread_id, customer_email, subject),
        ).fetchone()
        return row["id"]


def update_ticket(
    ticket_id: int, status: str, category: str | None = None, proposed_action: str | None = None
) -> None:
    with connect() as conn:
        conn.execute(
            """
            update tickets
            set status = %s, category = coalesce(%s, category),
                proposed_action = %s, updated_at = now()
            where id = %s
            """,
            (status, category, proposed_action, ticket_id),
        )


def save_message(
    ticket_id: int, gmail_message_id: str, direction: str, from_address: str, body: str
) -> None:
    with connect() as conn:
        conn.execute(
            """
            insert into messages (ticket_id, gmail_message_id, direction, from_address, body)
            values (%s, %s, %s, %s, %s)
            on conflict (gmail_message_id) do nothing
            """,
            (ticket_id, gmail_message_id, direction, from_address, body),
        )

def list_sections() -> list[str]:
    with connect() as conn:
        rows = conn.execute("select distinct section from knowledge_base order by section").fetchall()
        return [row["section"] for row in rows]


def get_section(section: str) -> list[dict]:
    with connect() as conn:
        return conn.execute(
            "select title, content from knowledge_base where section = %s order by id",
            (section,),
        ).fetchall()


# Dashboard helper functions


def get_events(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    with connect() as conn:
        conditions = []
        params: list = []
        if status and status != "all":
            conditions.append("status = %s")
            params.append(status)
        if search:
            conditions.append("(gmail_message_id ilike %s or error ilike %s or result::text ilike %s)")
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        where_clause = f"where {' and '.join(conditions)}" if conditions else ""

        total = conn.execute(f"select count(*) as count from events {where_clause}", params).fetchone()["count"]

        query = f"""
            select id, gmail_message_id, status, attempts, error, result, created_at, processed_at
            from events
            {where_clause}
            order by created_at desc
            limit %s offset %s
        """
        rows = conn.execute(query, [*params, limit, offset]).fetchall()
        return rows, total


def get_event_by_id(event_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            "select id, gmail_message_id, status, attempts, error, result, created_at, processed_at from events where id = %s",
            (event_id,),
        ).fetchone()


def get_events_stats() -> dict:
    with connect() as conn:
        rows = conn.execute(
            "select status, count(*) as count from events group by status"
        ).fetchall()
        stats = {"total": 0, "processing": 0, "processed": 0, "skipped": 0, "failed": 0}
        for r in rows:
            stats[r["status"]] = r["count"]
            stats["total"] += r["count"]
        return stats


def get_tickets(
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    with connect() as conn:
        conditions = []
        params: list = []
        if status and status != "all":
            conditions.append("t.status = %s")
            params.append(status)
        if search:
            conditions.append("(t.customer_email ilike %s or t.subject ilike %s or t.category ilike %s or t.proposed_action ilike %s)")
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        where_clause = f"where {' and '.join(conditions)}" if conditions else ""

        total = conn.execute(
            f"select count(*) as count from tickets t {where_clause}", params
        ).fetchone()["count"]

        query = f"""
            select
                t.id,
                t.gmail_thread_id,
                t.customer_email,
                t.subject,
                t.category,
                t.status,
                t.proposed_action,
                t.created_at,
                t.updated_at,
                count(m.id) as message_count
            from tickets t
            left join messages m on m.ticket_id = t.id
            {where_clause}
            group by t.id
            order by t.updated_at desc
            limit %s offset %s
        """
        rows = conn.execute(query, [*params, limit, offset]).fetchall()
        return rows, total


def get_ticket_by_id(ticket_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            """
            select id, gmail_thread_id, customer_email, subject, category, status, proposed_action, created_at, updated_at
            from tickets
            where id = %s
            """,
            (ticket_id,),
        ).fetchone()


def get_ticket_messages(ticket_id: int) -> list[dict]:
    with connect() as conn:
        return conn.execute(
            """
            select id, ticket_id, gmail_message_id, direction, from_address, body, created_at
            from messages
            where ticket_id = %s
            order by created_at asc
            """,
            (ticket_id,),
        ).fetchall()


def get_tickets_stats() -> dict:
    with connect() as conn:
        rows = conn.execute(
            "select status, count(*) as count from tickets group by status"
        ).fetchall()
        stats = {"total": 0, "open": 0, "answered": 0, "escalated": 0}
        for r in rows:
            stats[r["status"]] = r["count"]
            stats["total"] += r["count"]
        return stats


def get_knowledge_base_entries(
    section: str | None = None,
    search: str | None = None,
) -> list[dict]:
    with connect() as conn:
        conditions = []
        params: list = []
        if section and section != "all":
            conditions.append("section = %s")
            params.append(section)
        if search:
            conditions.append("(title ilike %s or content ilike %s or section ilike %s)")
            wildcard = f"%{search}%"
            params.extend([wildcard, wildcard, wildcard])

        where_clause = f"where {' and '.join(conditions)}" if conditions else ""
        query = f"""
            select id, section, title, content, updated_at
            from knowledge_base
            {where_clause}
            order by section asc, title asc
        """
        return conn.execute(query, params).fetchall()


def get_knowledge_base_entry(entry_id: int) -> dict | None:
    with connect() as conn:
        return conn.execute(
            "select id, section, title, content, updated_at from knowledge_base where id = %s",
            (entry_id,),
        ).fetchone()


def upsert_knowledge_base_entry(
    section: str, title: str, content: str, entry_id: int | None = None
) -> int:
    with connect() as conn:
        if entry_id:
            row = conn.execute(
                """
                update knowledge_base
                set section = %s, title = %s, content = %s, updated_at = now()
                where id = %s
                returning id
                """,
                (section, title, content, entry_id),
            ).fetchone()
            if row:
                return row["id"]

        row = conn.execute(
            """
            insert into knowledge_base (section, title, content)
            values (%s, %s, %s)
            on conflict (section, title) do update
            set content = excluded.content, updated_at = now()
            returning id
            """,
            (section, title, content),
        ).fetchone()
        return row["id"]


def delete_knowledge_base_entry(entry_id: int) -> bool:
    with connect() as conn:
        result = conn.execute("delete from knowledge_base where id = %s", (entry_id,))
        return result.rowcount > 0


# Gmail Watch State helpers


def get_watch_state() -> dict | None:
    with connect() as conn:
        return conn.execute(
            "select id, history_id, expiration, updated_at from gmail_watch_state where id = 1"
        ).fetchone()


def upsert_watch_state(history_id: int | str, expiration: int | str) -> None:
    with connect() as conn:
        conn.execute(
            """
            insert into gmail_watch_state (id, history_id, expiration, updated_at)
            values (1, %s, %s, now())
            on conflict (id) do update
            set history_id = excluded.history_id,
                expiration = excluded.expiration,
                updated_at = now()
            """,
            (int(history_id), int(expiration)),
        )


# Enterprise Agentic CRM & ERP helpers


def upsert_customer(
    email: str,
    name: str,
    loyalty_tier: str = "standard",
    churn_risk_score: float = 0.1,
) -> int:
    with connect() as conn:
        row = conn.execute(
            """
            insert into customers (email, name, loyalty_tier, churn_risk_score)
            values (%s, %s, %s, %s)
            on conflict (email) do update
            set name = excluded.name,
                loyalty_tier = excluded.loyalty_tier,
                churn_risk_score = excluded.churn_risk_score
            returning id
            """,
            (email.strip().lower(), name, loyalty_tier, churn_risk_score),
        ).fetchone()
        return row["id"]


def get_customer(email: str) -> dict | None:
    with connect() as conn:
        return conn.execute(
            "select id, email, name, loyalty_tier, churn_risk_score, created_at from customers where email = %s",
            (email.strip().lower(),),
        ).fetchone()


def upsert_order(
    order_id: str,
    customer_email: str,
    purchase_date: str,
    model: str,
    status: str = "delivered",
    serial_number: str | None = None,
    carrier: str | None = None,
    tracking_number: str | None = None,
    warranty_end_date: str | None = None,
) -> str:
    with connect() as conn:
        row = conn.execute(
            """
            insert into orders (
                order_id, customer_email, purchase_date, model, status,
                serial_number, carrier, tracking_number, warranty_end_date
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (order_id) do update
            set status = excluded.status,
                carrier = coalesce(excluded.carrier, orders.carrier),
                tracking_number = coalesce(excluded.tracking_number, orders.tracking_number),
                warranty_end_date = coalesce(excluded.warranty_end_date, orders.warranty_end_date)
            returning order_id
            """,
            (
                order_id.strip().upper(),
                customer_email.strip().lower(),
                purchase_date,
                model,
                status,
                serial_number,
                carrier,
                tracking_number,
                warranty_end_date,
            ),
        ).fetchone()
        return row["order_id"]


def get_order(order_id: str, customer_email: str | None = None) -> dict | None:
    with connect() as conn:
        if customer_email:
            return conn.execute(
                """
                select order_id, customer_email, purchase_date, model, status,
                       serial_number, carrier, tracking_number, warranty_end_date, created_at
                from orders
                where order_id = %s and customer_email = %s
                """,
                (order_id.strip().upper(), customer_email.strip().lower()),
            ).fetchone()
        return conn.execute(
            """
            select order_id, customer_email, purchase_date, model, status,
                   serial_number, carrier, tracking_number, warranty_end_date, created_at
            from orders
            where order_id = %s
            """,
            (order_id.strip().upper(),),
        ).fetchone()


def add_order_item(
    order_id: str,
    sku: str,
    title: str,
    unit_price_cents: int,
    is_accessory: bool = False,
) -> int:
    with connect() as conn:
        row = conn.execute(
            """
            insert into order_items (order_id, sku, title, unit_price_cents, is_accessory)
            values (%s, %s, %s, %s, %s)
            returning id
            """,
            (order_id.strip().upper(), sku, title, unit_price_cents, is_accessory),
        ).fetchone()
        return row["id"]


def get_order_items(order_id: str) -> list[dict]:
    with connect() as conn:
        return conn.execute(
            """
            select id, order_id, sku, title, unit_price_cents, is_accessory
            from order_items
            where order_id = %s
            order by id asc
            """,
            (order_id.strip().upper(),),
        ).fetchall()


def create_rma_record(
    rma_id: str,
    order_id: str,
    customer_email: str,
    status: str,
    reason: str,
    return_label_url: str,
) -> str:
    with connect() as conn:
        row = conn.execute(
            """
            insert into rma_requests (rma_id, order_id, customer_email, status, reason, return_label_url)
            values (%s, %s, %s, %s, %s, %s)
            on conflict (rma_id) do update
            set status = excluded.status, return_label_url = excluded.return_label_url
            returning rma_id
            """,
            (
                rma_id.strip().upper(),
                order_id.strip().upper(),
                customer_email.strip().lower(),
                status,
                reason,
                return_label_url,
            ),
        ).fetchone()
        return row["rma_id"]


def get_rma(rma_id: str) -> dict | None:
    with connect() as conn:
        return conn.execute(
            """
            select rma_id, order_id, customer_email, status, reason, return_label_url, created_at
            from rma_requests
            where rma_id = %s
            """,
            (rma_id.strip().upper(),),
        ).fetchone()


def create_approval(
    thread_id: str,
    action_type: str,
    payload: dict,
    proposed_reply: str | None = None,
) -> str:
    with connect() as conn:
        row = conn.execute(
            """
            insert into approvals (thread_id, action_type, payload, status, proposed_reply)
            values (%s, %s, %s, 'pending', %s)
            returning id::text
            """,
            (thread_id, action_type, Jsonb(payload), proposed_reply),
        ).fetchone()
        return str(row["id"])


def get_pending_approvals() -> list[dict]:
    with connect() as conn:
        return conn.execute(
            """
            select id::text, thread_id, action_type, payload, status, proposed_reply, created_at
            from approvals
            where status = 'pending'
            order by created_at desc
            """
        ).fetchall()


def resolve_approval(approval_id: str, status: str, resolved_by: str) -> bool:
    with connect() as conn:
        result = conn.execute(
            """
            update approvals
            set status = %s, resolved_at = now(), resolved_by = %s
            where id = %s::uuid and status = 'pending'
            """,
            (status, resolved_by, approval_id),
        )
        return result.rowcount > 0


