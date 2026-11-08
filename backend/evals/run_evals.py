"""Evaluation runner for AI Customer Support Agent.

Evaluates test cases from eval_cases.json against the agent pipeline,
verifying section classification, action routing (reply vs escalate),
and key phrase compliance. Outputs structured results to results/latest_results.json
and an evaluation report to reports/evaluation_report.md.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
import argparse
import json
import logging
import sys

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from evals.evaluators import evaluate_case

# Set up logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("evals")


class MockDecision:
    """Mock decision object used during dry-run (--mock)."""

    def __init__(self, section: str, action: str, reply: str = "", reason: str = "Mock execution"):
        self.section = section
        self.action = action
        self.reply = reply
        self.reason = reason
        self.proposed_action = None


def format_case_email(case: dict[str, Any]) -> tuple[str, bool]:
    """Format a test case input into thread text and attachment flag."""
    inp = case.get("input", {})
    sender = inp.get("sender", "Customer <customer@example.com>")
    subject = inp.get("subject", "")
    body = inp.get("body", "")
    has_attachments = inp.get("has_attachments", False)
    thread = f"Subject: {subject}\n\nCustomer ({sender}):\n{body}"
    return thread, has_attachments


def create_mock_decision(case: dict[str, Any]) -> MockDecision:
    """Generate a mock decision matching the expected output for dry runs."""
    expected = case.get("expected_output", {})
    section = expected.get("section", "other")
    action = expected.get("action", "reply")
    required = expected.get("required_key_phrases", [])

    sample_phrases = " ".join(required) if required else "Details and support provided."
    if action == "escalate":
        reply = (
            f"Thank you for contacting Nexa Support. {sample_phrases}. "
            "A support specialist has received your inquiry and will follow up shortly. "
            "Nexa Mobile Support."
        )
    else:
        reply = (
            f"Thank you for contacting Nexa Mobile Support. Regarding your inquiry on {section}: "
            f"{sample_phrases}. Please let us know if you have further questions. Nexa Mobile Support."
        )

    return MockDecision(
        section=section,
        action=action,
        reply=reply,
        reason=f"Dry run mock response for {case.get('id', case.get('name', 'test'))}",
    )


def run_single_eval(case: dict[str, Any], mock: bool = False) -> dict[str, Any]:
    """Execute evaluation for one test case."""
    thread, has_attachments = format_case_email(case)

    if mock:
        decision = create_mock_decision(case)
    else:
        try:
            from app.ai.decide import decide

            decision = decide(thread, has_attachments=has_attachments)
        except Exception as e:
            logger.error("Error running evaluation for %s: %s", case.get("id", case.get("name")), e)
            return {
                "id": case.get("id", "unknown"),
                "name": case.get("name", ""),
                "category": case.get("category", "general"),
                "passed": False,
                "section_match": False,
                "action_match": False,
                "phrases_match": False,
                "expected": {
                    "section": case.get("expected_output", {}).get("section", ""),
                    "action": case.get("expected_output", {}).get("action", ""),
                },
                "actual": {
                    "section": "ERROR",
                    "action": "ERROR",
                },
                "reply_preview": "",
                "reason": f"Execution Exception: {e}",
                "errors": [str(e)],
            }

    return evaluate_case(case, decision)


def load_cases(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Load and filter test cases from eval_cases.json."""
    evals_dir = Path(__file__).resolve().parent
    file_path = Path(args.file) if args.file else (evals_dir / "eval_cases.json")

    if not file_path.is_file():
        print(f"Error: Eval cases file not found at {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # Filter by specific ID or name
    if args.case_id:
        cases = [c for c in cases if c.get("id") == args.case_id or c.get("name") == args.case_id]

    # Filter by category
    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]

    # Limit total cases
    if args.limit and args.limit > 0:
        cases = cases[: args.limit]

    return cases


def generate_markdown_report(
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    report_file: Path,
):
    """Generate structured markdown report."""
    report_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# AI Customer Support Agent - Evaluation Report",
        "",
        f"- **Generated At:** {summary['timestamp']}",
        f"- **Total Test Cases:** {summary['total']}",
        f"- **Passed:** {summary['passed']} ({summary['pass_rate']:.1f}%)",
        f"- **Failed:** {summary['failed']}",
        f"- **Section Classification Accuracy:** {summary['section_accuracy']:.1f}%",
        f"- **Action Decision Accuracy:** {summary['action_accuracy']:.1f}%",
        f"- **Key Phrase Compliance:** {summary['phrases_compliance']:.1f}%",
        f"- **Execution Mode:** {'Mock (Dry-Run)' if summary.get('mock') else 'Live Agent'}",
        "",
        "## Category Breakdown",
        "",
        "| Category | Total | Passed | Failed | Pass Rate |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for cat, stats in summary.get("categories", {}).items():
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        lines.append(f"| {cat} | {stats['total']} | {stats['passed']} | {stats['failed']} | {rate:.1f}% |")

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| ID | Name | Category | Status | Expected | Actual | Error / Notes |")
    lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :--- |")

    for r in results:
        status = "PASSED" if r["passed"] else "FAILED"
        exp_str = f"{r['expected']['section']}/{r['expected']['action']}"
        act_str = f"{r['actual']['section']}/{r['actual']['action']}"
        err = "; ".join(r.get("errors", []))
        if not err and not r["passed"]:
            if not r["section_match"]:
                err = f"Section mismatch: expected {r['expected']['section']}, got {r['actual']['section']}"
            elif not r["action_match"]:
                err = f"Action mismatch: expected {r['expected']['action']}, got {r['actual']['action']}"
        lines.append(
            f"| {r['id']} | {r['name']} | {r['category']} | {status} | `{exp_str}` | `{act_str}` | {err} |"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run AI Customer Support Agent Evaluations.")
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        default=None,
        help="Path to evaluation test cases JSON file (default: backend/evals/eval_cases.json)",
    )
    parser.add_argument(
        "-c",
        "--category",
        type=str,
        default=None,
        help="Filter test cases by category (e.g. answer_accuracy, guardrails_security)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=None,
        help="Limit number of evaluation test cases to execute",
    )
    parser.add_argument(
        "--case-id",
        type=str,
        default=None,
        help="Run a specific test case by id (e.g. eval-001) or name",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=3,
        help="Number of concurrent worker threads (default: 3)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Dry run with mock responses (verifies test framework offline without external LLM API)",
    )
    parser.add_argument(
        "--output-results",
        type=str,
        default=None,
        help="Path to output JSON results file",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="Path to output Markdown evaluation report",
    )

    args = parser.parse_args()

    evals_dir = Path(__file__).resolve().parent
    results_path = (
        Path(args.output_results) if args.output_results else (evals_dir / "results" / "latest_results.json")
    )
    report_path = (
        Path(args.output_report) if args.output_report else (evals_dir / "reports" / "evaluation_report.md")
    )

    cases = load_cases(args)
    total = len(cases)

    if total == 0:
        print("No test cases found matching criteria.")
        sys.exit(0)

    mode_str = "MOCK (Dry Run)" if args.mock else "LIVE (Agent Invocation)"
    print(f"================================================================================")
    print(f" AI Customer Support Agent Evaluation Suite")
    print(f" Mode: {mode_str} | Running {total} test cases with {args.workers} worker(s)")
    print(f"================================================================================\n")

    results = []

    if args.workers <= 1:
        for case in cases:
            res = run_single_eval(case, mock=args.mock)
            results.append(res)
            status_icon = "PASS" if res["passed"] else "FAIL"
            print(
                f"[{status_icon:4}] {res['id']:<10} {res['name']:<32} | "
                f"Exp: {res['expected']['section']}/{res['expected']['action']:<9} | "
                f"Act: {res['actual']['section']}/{res['actual']['action']}"
            )
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_case = {executor.submit(run_single_eval, c, args.mock): c for c in cases}
            for future in future_to_case:
                res = future.result()
                results.append(res)
                status_icon = "PASS" if res["passed"] else "FAIL"
                print(
                    f"[{status_icon:4}] {res['id']:<10} {res['name']:<32} | "
                    f"Exp: {res['expected']['section']}/{res['expected']['action']:<9} | "
                    f"Act: {res['actual']['section']}/{res['actual']['action']}"
                )

    # Sort results by ID for consistent reporting
    results.sort(key=lambda r: str(r.get("id", "")))

    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    section_accuracy = (sum(1 for r in results if r["section_match"]) / total * 100) if total > 0 else 0.0
    action_accuracy = (sum(1 for r in results if r["action_match"]) / total * 100) if total > 0 else 0.0
    phrases_compliance = (sum(1 for r in results if r["phrases_match"]) / total * 100) if total > 0 else 0.0
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    # Aggregate category statistics
    category_stats: dict[str, dict[str, int]] = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "failed": 0}
        category_stats[cat]["total"] += 1
        if r["passed"]:
            category_stats[cat]["passed"] += 1
        else:
            category_stats[cat]["failed"] += 1

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "section_accuracy": section_accuracy,
        "action_accuracy": action_accuracy,
        "phrases_compliance": phrases_compliance,
        "mock": args.mock,
        "categories": category_stats,
    }

    # Save structured results JSON
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    # Generate Markdown report
    generate_markdown_report(results, summary, report_path)

    print("\n" + "=" * 80)
    print(f" Evaluation Summary:")
    print(f" Fully Passed:               {passed}/{total} ({pass_rate:.1f}%)")
    print(f" Section Accuracy:           {section_accuracy:.1f}%")
    print(f" Action Accuracy:            {action_accuracy:.1f}%")
    print(f" Key Phrase Compliance:      {phrases_compliance:.1f}%")
    print(f" Results JSON saved:         {results_path}")
    print(f" Evaluation Report saved:    {report_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
