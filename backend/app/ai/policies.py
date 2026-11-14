from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

TierType = Literal["tier_1", "tier_2"]


class PolicyDecision(BaseModel):
    tier: TierType = Field(description="Tier 1 = Autonomous execution; Tier 2 = Human supervisor approval required")
    requires_approval: bool = Field(description="True if human supervisor must approve prior to execution")
    action_type: str = Field(description="Action name or tool name being governed")
    reason: str = Field(description="Policy justification for the tier assignment")
    is_urgent: bool = Field(default=False, description="True for safety hazards or VIP churn risks")


def evaluate_action_policy(
    tool_name: str,
    args: Dict[str, Any],
    order: Optional[Dict[str, Any]] = None,
    item_price_cents: Optional[int] = None,
    is_accessory: Optional[bool] = None,
) -> PolicyDecision:
    """Evaluate whether a tool invocation can execute autonomously (Tier 1) or requires Human-in-the-Loop review (Tier 2)."""
    # 1. Global Safety Check
    reason_text = str(args.get("reason", "")).lower()
    safety_triggers = {"swelling", "swollen", "smoke", "smoking", "fire", "burning", "sparks", "exploded", "hazard"}
    if any(trigger in reason_text for trigger in safety_triggers):
        return PolicyDecision(
            tier="tier_2",
            requires_approval=True,
            action_type=tool_name,
            reason="Safety hazard detected in action justification. Immediate supervisor and compliance review required.",
            is_urgent=True,
        )

    # 2. Read-Only / Information Retrieval Tools -> Always Tier 1
    if tool_name in {"tool_lookup_order", "tool_track_package", "tool_verify_warranty", "tool_search_knowledge_base"}:
        return PolicyDecision(
            tier="tier_1",
            requires_approval=False,
            action_type=tool_name,
            reason="Read-only inquiry: autonomous execution permitted.",
        )

    # 3. Return RMA Requests
    if tool_name == "tool_request_rma_return":
        if order and order.get("purchase_date"):
            try:
                p_date_raw = order["purchase_date"]
                if isinstance(p_date_raw, str):
                    p_date = datetime.fromisoformat(p_date_raw.replace("Z", "+00:00"))
                else:
                    p_date = p_date_raw
                days_since_purchase = (datetime.now(timezone.utc) - p_date).days
                if days_since_purchase <= 30:
                    return PolicyDecision(
                        tier="tier_1",
                        requires_approval=False,
                        action_type=tool_name,
                        reason=f"Return within standard 30-day window ({days_since_purchase} days since purchase). Autonomous RMA label generation permitted.",
                    )
                else:
                    return PolicyDecision(
                        tier="tier_2",
                        requires_approval=True,
                        action_type=tool_name,
                        reason=f"Return request outside 30-day window ({days_since_purchase} days since purchase). Supervisor policy exception approval required.",
                    )
            except Exception:
                pass
        # Order details unknown or purchase date missing -> Tier 2
        return PolicyDecision(
            tier="tier_2",
            requires_approval=True,
            action_type=tool_name,
            reason="Order purchase date unverified. Return requires human verification.",
        )

    # 4. Replacement Dispatches
    if tool_name == "tool_dispatch_replacement":
        # Check accessory status & price threshold ($25.00 = 2500 cents)
        if is_accessory is True and (item_price_cents is not None and item_price_cents <= 2500):
            return PolicyDecision(
                tier="tier_1",
                requires_approval=False,
                action_type=tool_name,
                reason="Low-cost accessory replacement under warranty (<= $25.00). Autonomous fulfillment permitted.",
            )
        elif is_accessory is True and item_price_cents is None:
            # Sku check
            sku = str(args.get("sku", "")).upper()
            if "ACC" in sku or "CHG" in sku or "CABLE" in sku or "CASE" in sku:
                return PolicyDecision(
                    tier="tier_1",
                    requires_approval=False,
                    action_type=tool_name,
                    reason="Accessory SKU replacement under warranty. Autonomous fulfillment permitted.",
                )

        return PolicyDecision(
            tier="tier_2",
            requires_approval=True,
            action_type=tool_name,
            reason="Full unit or high-value hardware replacement requires supervisor authorization.",
        )

    # 5. Refunds / Financial Transactions
    if tool_name == "tool_request_refund":
        amount = float(args.get("amount_usd", 0.0))
        return PolicyDecision(
            tier="tier_2",
            requires_approval=True,
            action_type=tool_name,
            reason=f"Financial transaction (Refund of ${amount:.2f}) requires human supervisor approval.",
        )

    # Default fallback -> Tier 2
    return PolicyDecision(
        tier="tier_2",
        requires_approval=True,
        action_type=tool_name,
        reason=f"Action '{tool_name}' requires human supervisor review.",
    )

