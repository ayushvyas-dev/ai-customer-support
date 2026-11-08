from app.ai.schemas import Issue

# Steps where the reply goes to the customer, because they have to check or send something first.
CUSTOMER_STEPS = {"troubleshooting-steps", "ask-details"}


def resolve_issue(issue: Issue) -> str:
    """Decide the next step for a reported problem. The model reports, Python decides."""
    step = next_step(issue)
    if step not in CUSTOMER_STEPS | {"escalate"} and not issue.order_number:
        return "ask-details"
    return step


def next_step(issue: Issue) -> str:
    # Swelling, smoke, burning smell, or dangerous overheating must escalate immediately.
    if issue.safety_risk or issue.problem == "safety-hazard":
        return "escalate"

    # Physical damage requires human review and inspection.
    if issue.problem == "physical-damage":
        if not issue.order_number or not issue.model:
            return "ask-details"
        return "escalate"

    # Unresponsive devices: guide 30-min charge + power button reset first.
    if issue.problem == "not-turning-on":
        if not issue.troubleshooting_attempted:
            return "troubleshooting-steps"
        if not issue.order_number or not issue.model:
            return "ask-details"
        return "escalate"

    # Standard smartphone issues: offer troubleshooting steps first, then escalate.
    if issue.product == "smartphone":
        if issue.problem in {
            "slow-charging",
            "battery-drain",
            "display-issue",
            "camera-issue",
            "performance-lag",
            "connectivity-issue",
        }:
            if not issue.troubleshooting_attempted:
                return "troubleshooting-steps"
            if not issue.order_number or not issue.model:
                return "ask-details"
            return "escalate"

    # Accessories issues:
    if issue.product == "accessories":
        if issue.problem == "incompatible-accessory":
            if not issue.order_number or not issue.model:
                return "ask-details"
            return "escalate"
        if issue.problem in {"missing-accessory", "damaged-accessory"}:
            if not issue.order_number:
                return "ask-details"
            return "escalate"

    return "escalate"