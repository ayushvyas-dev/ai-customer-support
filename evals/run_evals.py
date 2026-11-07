import logging
from concurrent.futures import ThreadPoolExecutor

from app.ai.decide import decide
from evals.golden_emails import GOLDEN_EMAILS

logging.basicConfig(level=logging.WARNING)


def run_single_eval(case: dict) -> dict:
    name = case["name"]
    email_text = case["email"]
    expected_section = case["section"]
    expected_action = case["action"]

    try:
        decision = decide(email_text)
        actual_section = decision.section
        actual_action = decision.action

        section_match = actual_section == expected_section
        action_match = actual_action == expected_action

        return {
            "name": name,
            "passed": section_match and action_match,
            "section_match": section_match,
            "action_match": action_match,
            "expected": f"({expected_section}, {expected_action})",
            "actual": f"({actual_section}, {actual_action})",
            "reason": decision.reason[:80] if decision.reason else "",
        }
    except Exception as e:
        return {
            "name": name,
            "passed": False,
            "section_match": False,
            "action_match": False,
            "expected": f"({expected_section}, {expected_action})",
            "actual": f"ERROR: {e}",
            "reason": str(e),
        }


def main():
    print(f"Running golden email evaluation suite on {len(GOLDEN_EMAILS)} test cases...\n")
    results = []

    # Run evaluations with thread pool
    with ThreadPoolExecutor(max_workers=3) as executor:
        for res in executor.map(run_single_eval, GOLDEN_EMAILS):
            results.append(res)
            status_icon = "PASS" if res["passed"] else "FAIL"
            print(
                f"[{status_icon:4}] {res['name']:<35} | Expected: {res['expected']:<25} | Actual: {res['actual']}"
            )

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    section_accuracy = sum(1 for r in results if r["section_match"]) / total * 100
    action_accuracy = sum(1 for r in results if r["action_match"]) / total * 100

    print("\n" + "=" * 80)
    print(f"Evaluation Summary: {passed}/{total} fully passed ({passed/total*100:.1f}%)")
    print(f"Section Classification Accuracy: {section_accuracy:.1f}%")
    print(f"Action (reply/escalate) Accuracy: {action_accuracy:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
