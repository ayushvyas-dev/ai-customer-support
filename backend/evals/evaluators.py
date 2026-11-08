"""Automated evaluators for evaluating AI Customer Support Agent decisions against eval_cases.json.
"""

from typing import Any


def evaluate_section(actual_section: str, expected_section: str) -> bool:
    """Evaluate whether the classified section matches expectation."""
    if not expected_section:
        return True
    return actual_section.lower().strip() == expected_section.lower().strip()


def evaluate_action(actual_action: str, expected_action: str) -> bool:
    """Evaluate whether the action (reply vs escalate) matches expectation."""
    if not expected_action:
        return True
    return actual_action.lower().strip() == expected_action.lower().strip()


def evaluate_key_phrases(
    reply: str,
    required_phrases: list[str],
    prohibited_phrases: list[str],
) -> tuple[bool, list[str]]:
    """Verify presence of required phrases and absence of prohibited phrases."""
    reply_lower = (reply or "").lower()
    errors = []

    for req in required_phrases:
        if req.lower() not in reply_lower:
            errors.append(f"Missing required phrase: '{req}'")

    for proh in prohibited_phrases:
        if proh.lower() in reply_lower:
            errors.append(f"Contains prohibited phrase: '{proh}'")

    return len(errors) == 0, errors


def evaluate_case(case: dict[str, Any], decision: Any) -> dict[str, Any]:
    """Run automated evaluation for a single test case from eval_cases.json."""
    expected_out = case.get("expected_output", {})
    expected_section = expected_out.get("section", "")
    expected_action = expected_out.get("action", "")
    required = expected_out.get("required_key_phrases", [])
    prohibited = expected_out.get("prohibited_key_phrases", [])

    actual_section = getattr(decision, "section", "") or ""
    actual_action = getattr(decision, "action", "") or ""
    actual_reply = getattr(decision, "reply", "") or ""
    actual_reason = getattr(decision, "reason", "") or ""

    section_ok = evaluate_section(actual_section, expected_section)
    action_ok = evaluate_action(actual_action, expected_action)
    phrases_ok, phrase_errors = evaluate_key_phrases(actual_reply, required, prohibited)

    overall_passed = section_ok and action_ok and phrases_ok

    return {
        "id": case.get("id", "unknown"),
        "name": case.get("name", ""),
        "category": case.get("category", "general"),
        "passed": overall_passed,
        "section_match": section_ok,
        "action_match": action_ok,
        "phrases_match": phrases_ok,
        "expected": {
            "section": expected_section,
            "action": expected_action,
        },
        "actual": {
            "section": actual_section,
            "action": actual_action,
        },
        "reply_preview": (actual_reply[:120] + "...") if len(actual_reply) > 120 else actual_reply,
        "reason": actual_reason,
        "errors": phrase_errors,
    }
