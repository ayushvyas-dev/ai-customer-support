import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.guards import detect_prompt_injection, mask_pii
from app.services import enterprise
from app.vectorstore import search_similar

logger = logging.getLogger(__name__)

KB_DIR = Path(__file__).resolve().parents[2] / "knowledge_base"


# =====================================================================
# Audit & Sanitization Helpers
# =====================================================================


def _sanitize_input(text: Optional[str]) -> str:
    """Sanitize incoming text parameter: strip whitespace, mask PII, remove injection markers."""
    if not text:
        return ""
    sanitized = mask_pii(text.strip())
    # Strip common prompt injection command fragments if present
    is_inj, _ = detect_prompt_injection(sanitized)
    if is_inj:
        sanitized = sanitized.replace("Ignore all instructions", "").replace("ignore all previous instructions", "").strip()
    return sanitized


def _log_tool_call(tool_name: str, args: Dict[str, Any], output_dict: Dict[str, Any]) -> None:
    """Audit log tool invocations without storing unmasked tokens."""
    logger.info("Executing Tool [%s] with args: %s", tool_name, json.dumps(args, default=str))


# =====================================================================
# Schema Definitions
# =====================================================================


class LookupOrderInput(BaseModel):
    order_id: str = Field(description="The unique Nexa or Amazon order identifier, e.g. 'NX-1001'.")
    customer_email: Optional[str] = Field(
        default=None, description="Optional customer email address to verify order ownership."
    )


class TrackPackageInput(BaseModel):
    carrier: str = Field(description="The shipping carrier name, e.g. 'FedEx', 'UPS', 'Amazon Logistics'.")
    tracking_number: str = Field(description="The shipment tracking number, e.g. 'TRK-992144'.")


class VerifyWarrantyInput(BaseModel):
    order_id: str = Field(description="The order number associated with the device, e.g. 'NX-1001'.")


class SearchKnowledgeBaseInput(BaseModel):
    query: str = Field(description="The search inquiry or technical question about Nexa products or policies.")
    section: Optional[str] = Field(
        default=None,
        description="Optional knowledge base section filter, e.g. 'smartphone', 'accessories', 'shipping', 'returns-and-warranty'.",
    )


class RequestRmaInput(BaseModel):
    order_id: str = Field(description="The order number being returned, e.g. 'NX-1001'.")
    reason: str = Field(description="Detailed reason for the return or exchange.")
    items: List[str] = Field(description="List of product SKUs to be returned.")


class DispatchReplacementInput(BaseModel):
    order_id: str = Field(description="The original order number under warranty, e.g. 'NX-1002'.")
    sku: str = Field(description="The replacement part or accessory SKU, e.g. 'SKU-ACC-65W-CHG'.")
    reason: str = Field(description="Reason for warranty replacement, e.g. 'Frayed charging cable'.")


class RequestRefundInput(BaseModel):
    order_id: str = Field(description="The order number for the refund, e.g. 'NX-1001'.")
    amount_usd: float = Field(description="Amount in USD to refund or credit, e.g. 25.0.")
    reason: str = Field(description="Business reason or justification for the refund.")


# =====================================================================
# Tool Definitions
# =====================================================================


@tool("tool_lookup_order", args_schema=LookupOrderInput)
def tool_lookup_order(order_id: str, customer_email: Optional[str] = None) -> str:
    """Look up an order in the enterprise database. Returns status, items, purchase date, tracking info, and warranty dates."""
    clean_id = _sanitize_input(order_id)
    clean_email = _sanitize_input(customer_email) if customer_email else None

    order = enterprise.lookup_order(clean_id, clean_email)
    if not order:
        resp = {"error": True, "message": f"Order '{clean_id}' was not found in the Nexa database."}
        _log_tool_call("tool_lookup_order", {"order_id": clean_id}, resp)
        return json.dumps(resp)

    resp = {
        "error": False,
        "order_id": order["order_id"],
        "customer_email": order["customer_email"],
        "model": order["model"],
        "status": order["status"],
        "purchase_date": order["purchase_date"],
        "carrier": order.get("carrier"),
        "tracking_number": order.get("tracking_number"),
        "warranty_end_date": order.get("warranty_end_date"),
        "items": order.get("items", []),
    }
    _log_tool_call("tool_lookup_order", {"order_id": clean_id}, resp)
    return json.dumps(resp)


@tool("tool_track_package", args_schema=TrackPackageInput)
def tool_track_package(carrier: str, tracking_number: str) -> str:
    """Query live logistics carrier status and delivery checkpoints for a shipment."""
    clean_carrier = _sanitize_input(carrier)
    clean_trk = _sanitize_input(tracking_number)

    data = enterprise.get_carrier_tracking(clean_carrier, clean_trk)
    _log_tool_call("tool_track_package", {"carrier": clean_carrier, "tracking_number": clean_trk}, data)
    return json.dumps(data)


@tool("tool_verify_warranty", args_schema=VerifyWarrantyInput)
def tool_verify_warranty(order_id: str) -> str:
    """Verify whether a customer's product is covered under the 1-year limited manufacturer warranty."""
    clean_id = _sanitize_input(order_id)
    data = enterprise.verify_warranty_status(clean_id)
    _log_tool_call("tool_verify_warranty", {"order_id": clean_id}, data)
    return json.dumps(data)


@tool("tool_search_knowledge_base", args_schema=SearchKnowledgeBaseInput)
def tool_search_knowledge_base(query: str, section: Optional[str] = None) -> str:
    """Perform a semantic vector search on Nexa product specifications, troubleshooting manuals, and brand policies."""
    clean_query = _sanitize_input(query)
    clean_sec = _sanitize_input(section) if section else None

    results: List[str] = []
    # Try pgvector search
    try:
        results = search_similar(query=clean_query, section=clean_sec, top_k=4)
    except Exception as e:
        logger.warning("Vector search unavailable, falling back to local KB files: %s", e)

    # Fallback: scan markdown files directly
    if not results and KB_DIR.exists():
        target_files = [KB_DIR / f"{clean_sec}.md"] if clean_sec and (KB_DIR / f"{clean_sec}.md").exists() else list(KB_DIR.glob("*.md"))
        q_words = set(clean_query.lower().split())
        for f in target_files:
            try:
                content = f.read_text(encoding="utf-8")
                blocks = content.split("\n## ")
                for b in blocks:
                    title, _, text = b.partition("\n")
                    if any(w in (title + text).lower() for w in q_words):
                        results.append(f"## {title.strip()}\n{text.strip()[:400]}")
                        if len(results) >= 4:
                            break
            except Exception:
                continue

    resp = {
        "query": clean_query,
        "section": clean_sec or "all",
        "results": results or ["No matching documentation found."],
    }
    _log_tool_call("tool_search_knowledge_base", {"query": clean_query, "section": clean_sec}, resp)
    return json.dumps(resp)


@tool("tool_request_rma_return", args_schema=RequestRmaInput)
def tool_request_rma_return(order_id: str, reason: str, items: List[str]) -> str:
    """Initiate a Return Merchandise Authorization (RMA) and generate a prepaid shipping return label."""
    clean_id = _sanitize_input(order_id)
    clean_reason = _sanitize_input(reason)
    clean_items = [_sanitize_input(i) for i in items]

    data = enterprise.create_rma(clean_id, clean_reason, clean_items)
    _log_tool_call("tool_request_rma_return", {"order_id": clean_id, "reason": clean_reason}, data)
    return json.dumps(data)


@tool("tool_dispatch_replacement", args_schema=DispatchReplacementInput)
def tool_dispatch_replacement(order_id: str, sku: str, reason: str) -> str:
    """Order and dispatch an immediate warranty replacement accessory (charging cables, adapters, cases)."""
    clean_id = _sanitize_input(order_id)
    clean_sku = _sanitize_input(sku)
    clean_reason = _sanitize_input(reason)

    data = enterprise.issue_replacement_order(clean_id, clean_sku, clean_reason)
    _log_tool_call("tool_dispatch_replacement", {"order_id": clean_id, "sku": clean_sku}, data)
    return json.dumps(data)


@tool("tool_request_refund", args_schema=RequestRefundInput)
def tool_request_refund(order_id: str, amount_usd: float, reason: str) -> str:
    """Process or request a partial/full courtesy refund for a customer order."""
    clean_id = _sanitize_input(order_id)
    clean_reason = _sanitize_input(reason)

    data = enterprise.issue_store_credit_or_refund(clean_id, amount_usd, clean_reason)
    _log_tool_call("tool_request_refund", {"order_id": clean_id, "amount_usd": amount_usd}, data)
    return json.dumps(data)


# List of all available agentic tools
SUPPORT_TOOLS = [
    tool_lookup_order,
    tool_track_package,
    tool_verify_warranty,
    tool_search_knowledge_base,
    tool_request_rma_return,
    tool_dispatch_replacement,
    tool_request_refund,
]

