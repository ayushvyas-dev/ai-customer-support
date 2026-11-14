"""Evaluation runner for AI Customer Support Agent with decoupled 2-stage execution.

Stage 1 (Generation): Agent generates decisions/replies for test cases -> saved to eval_outputs.json.
Stage 2 (Judging): LLM Judge evaluates eval_outputs.json -> outputs latest_results.json and evaluation_report.md.

Allows re-scoring or adjusting the judge rubric in seconds without re-running the agent.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any
import argparse
import json
import logging
import sys
import time
from dotenv import load_dotenv

# Ensure backend root is in sys.path and load environment variables
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

from app.config import settings
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


class CachedDecision:
    """Reconstructed decision object from cached eval_outputs.json."""

    def __init__(self, data: dict[str, Any]):
        self.section = data.get("section", "other")
        self.action = data.get("action", "reply")
        self.reply = data.get("reply", "")
        self.reason = data.get("reason", "")
        self.proposed_action = data.get("proposed_action", None)


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
            f"Thank you for contacting Nexa Mobile. {sample_phrases}. "
            "A support specialist has received your inquiry and will follow up shortly.\n\n"
            "Nexa Mobile Support"
        )
    else:
        reply = (
            f"Thank you for contacting Nexa Mobile Support. Regarding your inquiry on {section}: "
            f"{sample_phrases}. Please let us know if you have further questions.\n\n"
            "Nexa Mobile Support"
        )

    return MockDecision(
        section=section,
        action=action,
        reply=reply,
        reason=f"Dry run mock response for {case.get('id', case.get('name', 'test'))}",
    )


def generate_single_output(case: dict[str, Any], mock: bool = False) -> dict[str, Any]:
    """Execute the agent pipeline for one test case and record output."""
    thread, has_attachments = format_case_email(case)
    t0 = time.time()

    if mock:
        decision = create_mock_decision(case)
        t_elapsed = time.time() - t0
        return {
            "id": case.get("id", "unknown"),
            "name": case.get("name", ""),
            "category": case.get("category", "general"),
            "case": case,
            "decision": {
                "section": decision.section,
                "action": decision.action,
                "reply": decision.reply,
                "reason": decision.reason,
                "proposed_action": getattr(decision, "proposed_action", None),
                "latency_seconds": round(t_elapsed, 3),
            },
        }

    try:
        from app.ai.decide import decide

        decision = decide(thread, has_attachments=has_attachments)
        t_elapsed = time.time() - t0
        return {
            "id": case.get("id", "unknown"),
            "name": case.get("name", ""),
            "category": case.get("category", "general"),
            "case": case,
            "decision": {
                "section": decision.section,
                "action": decision.action,
                "reply": decision.reply,
                "reason": decision.reason,
                "proposed_action": getattr(decision, "proposed_action", None),
                "latency_seconds": round(t_elapsed, 3),
            },
        }
    except Exception as e:
        t_elapsed = time.time() - t0
        logger.error("Agent generation failed for %s: %s", case.get("id"), e)
        return {
            "id": case.get("id", "unknown"),
            "name": case.get("name", ""),
            "category": case.get("category", "general"),
            "case": case,
            "decision": {
                "section": "ERROR",
                "action": "ERROR",
                "reply": "",
                "reason": f"Agent Exception: {e}",
                "proposed_action": None,
                "latency_seconds": round(t_elapsed, 3),
                "error": str(e),
            },
        }


def run_stage1_generate(
    cases: list[dict[str, Any]],
    outputs_path: Path,
    mock: bool = False,
    workers: int = 1,
    delay: float = 0.0,
) -> list[dict[str, Any]]:
    """Stage 1: Generate agent responses for all test cases and save to eval_outputs.json."""
    total = len(cases)
    mode_str = "MOCK (Dry Run)" if mock else "LIVE (Agent Invocation)"

    print(f"\n{'='*80}")
    print(f" STAGE 1: Agent Output Generation")
    print(f" Mode: {mode_str} | Generating {total} case(s) with {workers} worker(s)")
    print(f" Target Output File: {outputs_path}")
    print(f"{'='*80}\n")

    outputs = []
    t_stage1_start = time.time()

    if workers <= 1:
        for idx, case in enumerate(cases):
            if idx > 0 and delay > 0 and not mock:
                print(f"[Pacing] Waiting {delay:.1f}s...", end="", flush=True)
                time.sleep(delay)
                print("\r" + " " * 40 + "\r", end="", flush=True)

            case_label = f"[{idx+1}/{total}] {case.get('id'):<9} {case.get('name', ''):<28}"
            print(f"{case_label} | generating...", end="", flush=True)
            res = generate_single_output(case, mock=mock)
            outputs.append(res)
            lat = res["decision"].get("latency_seconds", 0.0)
            sec = res["decision"].get("section", "error")
            act = res["decision"].get("action", "error")
            print(f"\r{case_label} | generated ({lat:>5.1f}s) | Act: {sec}/{act}")
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_case = {executor.submit(generate_single_output, c, mock): c for c in cases}
            for idx, future in enumerate(future_to_case):
                res = future.result()
                outputs.append(res)
                lat = res["decision"].get("latency_seconds", 0.0)
                sec = res["decision"].get("section", "error")
                act = res["decision"].get("action", "error")
                print(f"[{idx+1}/{total}] {res['id']:<9} {res['name']:<28} | generated ({lat:>5.1f}s) | Act: {sec}/{act}")

    # Sort outputs by ID
    outputs.sort(key=lambda r: str(r.get("id", "")))
    t_stage1_elapsed = time.time() - t_stage1_start

    # Save to eval_outputs.json
    outputs_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now().isoformat(),
        "total": len(outputs),
        "elapsed_seconds": round(t_stage1_elapsed, 2),
        "mock": mock,
        "agent_model": settings.agent_model or "gemini-2.5-flash",
        "outputs": outputs,
    }
    with open(outputs_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"\n>>> Stage 1 Complete: {len(outputs)} outputs saved to {outputs_path} ({t_stage1_elapsed:.1f}s)")
    return outputs


def run_stage2_judge(
    outputs: list[dict[str, Any]],
    results_path: Path,
    report_path: Path,
    mock: bool = False,
    workers: int = 1,
    delay: float = 0.0,
) -> list[dict[str, Any]]:
    """Stage 2: LLM-as-a-Judge evaluates pre-generated outputs from eval_outputs.json."""
    total = len(outputs)
    evaluator_model_name = settings.evaluator_model or "openai/gpt-oss-120b"
    provider = "Google GenAI" if "gemini" in evaluator_model_name.lower() else "Groq"
    mode_str = "MOCK (Dry Run)" if mock else f"LIVE (LLM Judge: {evaluator_model_name} via {provider})"

    print(f"\n{'='*80}")
    print(f" STAGE 2: LLM-as-a-Judge Evaluation")
    print(f" Mode: {mode_str} | Evaluating {total} case(s) with {workers} worker(s)")
    print(f" Evaluator Model: {evaluator_model_name} | Rate Pacing Delay: {delay}s")
    print(f"{'='*80}\n")

    results = []

    def judge_item(item: dict[str, Any]) -> dict[str, Any]:
        case = item["case"]
        decision = CachedDecision(item["decision"])
        return evaluate_case(case, decision, mock=mock)

    if workers <= 1:
        for idx, item in enumerate(outputs):
            if idx > 0 and delay > 0 and not mock:
                print(f"[Pacing] Waiting {delay:.1f}s for judge rate limit...", end="", flush=True)
                time.sleep(delay)
                print("\r" + " " * 50 + "\r", end="", flush=True)

            case_label = f"[{idx+1}/{total}] {item.get('id'):<9} {item.get('name', ''):<28}"
            print(f"{case_label} | judging...", end="", flush=True)
            t_start = time.time()
            res = judge_item(item)
            t_elapsed = time.time() - t_start
            results.append(res)
            status_icon = "PASS" if res["passed"] else "FAIL"
            score_val = res.get("score", 0.0)
            print(
                f"\r{case_label} | [{status_icon:4}] ({t_elapsed:>5.1f}s) | Score: {score_val:.2f} | "
                f"Exp: {res['expected']['section']}/{res['expected']['action']:<9} | "
                f"Act: {res['actual']['section']}/{res['actual']['action']}"
            )
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_item = {executor.submit(judge_item, item): item for item in outputs}
            for idx, future in enumerate(future_to_item):
                res = future.result()
                results.append(res)
                status_icon = "PASS" if res["passed"] else "FAIL"
                score_val = res.get("score", 0.0)
                print(
                    f"[{idx+1}/{total}] {res['id']:<9} {res['name']:<28} | [{status_icon:4}] | Score: {score_val:.2f} | "
                    f"Exp: {res['expected']['section']}/{res['expected']['action']:<9} | "
                    f"Act: {res['actual']['section']}/{res['actual']['action']}"
                )

    # Sort results by ID
    results.sort(key=lambda r: str(r.get("id", "")))

    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    avg_score = (sum(r.get("score", 0.0) for r in results) / total) if total > 0 else 0.0
    section_accuracy = (sum(1 for r in results if r["section_match"]) / total * 100) if total > 0 else 0.0
    action_accuracy = (sum(1 for r in results if r["action_match"]) / total * 100) if total > 0 else 0.0
    avg_faithfulness = (sum(r.get("faithfulness_score", 0.0) for r in results) / total) if total > 0 else 0.0
    guardrail_compliance = (sum(1 for r in results if r.get("guardrail_compliance")) / total * 100) if total > 0 else 0.0
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    # Aggregate category statistics
    category_stats: dict[str, dict[str, Any]] = {}
    for r in results:
        cat = r.get("category", "general")
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "failed": 0, "scores": []}
        category_stats[cat]["total"] += 1
        category_stats[cat]["scores"].append(r.get("score", 0.0))
        if r["passed"]:
            category_stats[cat]["passed"] += 1
        else:
            category_stats[cat]["failed"] += 1

    for cat, data in category_stats.items():
        scores = data.pop("scores")
        data["avg_score"] = (sum(scores) / len(scores)) if scores else 0.0

    summary = {
        "timestamp": datetime.now().isoformat(),
        "evaluator_model": evaluator_model_name,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "avg_score": avg_score,
        "section_accuracy": section_accuracy,
        "action_accuracy": action_accuracy,
        "avg_faithfulness": avg_faithfulness,
        "guardrail_compliance": guardrail_compliance,
        "mock": mock,
        "categories": category_stats,
    }

    # Save structured results JSON
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)

    # Generate Markdown report
    generate_markdown_report(results, summary, report_path)

    print("\n" + "=" * 80)
    print(f" LLM Judge Evaluation Summary ({evaluator_model_name}):")
    print(f" Fully Passed:               {passed}/{total} ({pass_rate:.1f}%)")
    print(f" Average Score:              {avg_score:.2f} / 1.0")
    print(f" Section Accuracy:           {section_accuracy:.1f}%")
    print(f" Action Accuracy:            {action_accuracy:.1f}%")
    print(f" Average Faithfulness:       {avg_faithfulness:.2f} / 1.0")
    print(f" Guardrail Compliance:       {guardrail_compliance:.1f}%")
    print(f" Results JSON saved:         {results_path}")
    print(f" Evaluation Report saved:    {report_path}")
    print("=" * 80)

    return results


def generate_markdown_report(
    results: list[dict[str, Any]],
    summary: dict[str, Any],
    report_file: Path,
):
    """Generate structured markdown report with LLM-as-a-Judge evaluations."""
    report_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# AI Customer Support Agent - LLM Judge Evaluation Report",
        "",
        f"- **Generated At:** {summary['timestamp']}",
        f"- **Evaluator Model (LLM Judge):** `{summary.get('evaluator_model', 'openai/gpt-oss-120b')}`",
        f"- **Execution Mode:** {'Mock (Dry-Run)' if summary.get('mock') else 'Live LLM-as-a-Judge'}",
        f"- **Total Test Cases:** {summary['total']}",
        f"- **Passed:** {summary['passed']} ({summary['pass_rate']:.1f}%)",
        f"- **Failed:** {summary['failed']}",
        f"- **Average Quality Score:** {summary['avg_score']:.2f} / 1.0",
        f"- **Section Classification Accuracy:** {summary['section_accuracy']:.1f}%",
        f"- **Action Routing Accuracy:** {summary['action_accuracy']:.1f}%",
        f"- **Average Faithfulness / Groundedness:** {summary['avg_faithfulness']:.2f} / 1.0",
        f"- **Guardrail & Safety Compliance:** {summary['guardrail_compliance']:.1f}%",
        "",
        "## Category Breakdown",
        "",
        "| Category | Total | Passed | Failed | Pass Rate | Avg Score |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for cat, stats in summary.get("categories", {}).items():
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        avg_sc = stats.get("avg_score", 0.0)
        lines.append(
            f"| {cat} | {stats['total']} | {stats['passed']} | {stats['failed']} | {rate:.1f}% | {avg_sc:.2f} |"
        )

    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| ID | Name | Category | Status | Score | Expected | Actual | Judge Reasoning / Flaws |")
    lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |")

    for r in results:
        status = "PASSED" if r["passed"] else "FAILED"
        score_str = f"{r.get('score', 0.0):.2f}"
        exp_str = f"{r['expected']['section']}/{r['expected']['action']}"
        act_str = f"{r['actual']['section']}/{r['actual']['action']}"
        judge_note = r.get("judge_reasoning", "")
        if r.get("errors"):
            judge_note += " (Errors: " + "; ".join(r["errors"]) + ")"
        clean_note = judge_note.replace("\n", " ").replace("|", "\\|")
        if len(clean_note) > 160:
            clean_note = clean_note[:157] + "..."
        lines.append(
            f"| {r['id']} | {r['name']} | {r['category']} | {status} | {score_str} | `{exp_str}` | `{act_str}` | {clean_note} |"
        )

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def load_cases(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Load and filter test cases from eval_cases.json."""
    evals_dir = Path(__file__).resolve().parent
    file_path = Path(args.file) if args.file else (evals_dir / "eval_cases.json")

    if not file_path.is_file():
        print(f"Error: Eval cases file not found at {file_path}")
        sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    if args.case_id:
        cases = [c for c in cases if c.get("id") == args.case_id or c.get("name") == args.case_id]

    if args.category:
        cases = [c for c in cases if c.get("category") == args.category]

    if args.limit and args.limit > 0:
        cases = cases[: args.limit]

    return cases


def main():
    parser = argparse.ArgumentParser(
        description="Run AI Customer Support Agent Evaluations (Decoupled 2-Stage Pipeline)."
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        choices=["both", "generate", "judge"],
        default="both",
        help="Execution mode: 'generate' (Run 1: save agent outputs), 'judge' (Run 2: evaluate outputs), 'both' (default)",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Shortcut for --mode generate (Run 1: agent generates outputs to eval_outputs.json)",
    )
    parser.add_argument(
        "--judge-only",
        action="store_true",
        help="Shortcut for --mode judge (Run 2: LLM judge evaluates eval_outputs.json)",
    )
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
        default=1,
        help="Number of concurrent worker threads (default: 1)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between evaluations to respect rate limits (default: 0.0)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Dry run with mock responses (verifies test framework offline without external LLM API)",
    )
    parser.add_argument(
        "--outputs-file",
        type=str,
        default=None,
        help="Path to eval_outputs.json file (default: backend/evals/results/eval_outputs.json)",
    )
    parser.add_argument(
        "--output-results",
        type=str,
        default=None,
        help="Path to output JSON results file (default: backend/evals/results/latest_results.json)",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default=None,
        help="Path to output Markdown evaluation report (default: backend/evals/reports/evaluation_report.md)",
    )

    args = parser.parse_args()

    # Determine mode
    mode = args.mode
    if args.generate_only:
        mode = "generate"
    elif args.judge_only:
        mode = "judge"

    evals_dir = Path(__file__).resolve().parent
    outputs_path = (
        Path(args.outputs_file) if args.outputs_file else (evals_dir / "results" / "eval_outputs.json")
    )
    results_path = (
        Path(args.output_results) if args.output_results else (evals_dir / "results" / "latest_results.json")
    )
    report_path = (
        Path(args.output_report) if args.output_report else (evals_dir / "reports" / "evaluation_report.md")
    )

    outputs: list[dict[str, Any]] = []

    # Run 1: Generation Phase
    if mode in ("both", "generate"):
        cases = load_cases(args)
        if not cases:
            print("No test cases found matching criteria.")
            sys.exit(0)
        outputs = run_stage1_generate(
            cases=cases,
            outputs_path=outputs_path,
            mock=args.mock,
            workers=args.workers,
            delay=args.delay,
        )

    # Run 2: Judging Phase
    if mode in ("both", "judge"):
        if mode == "judge":
            if not outputs_path.is_file():
                print(f"Error: Outputs file '{outputs_path}' not found.")
                print("Please run with '--mode generate' (or '--generate-only') first to generate agent outputs.")
                sys.exit(1)
            print(f"Loading cached agent outputs from: {outputs_path}")
            with open(outputs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            outputs = data.get("outputs", [])

            # Filter loaded outputs if case-id, category, or limit was passed to judge
            if args.case_id:
                outputs = [o for o in outputs if o.get("id") == args.case_id or o.get("name") == args.case_id]
            if args.category:
                outputs = [o for o in outputs if o.get("category") == args.category]
            if args.limit and args.limit > 0:
                outputs = outputs[: args.limit]

            if not outputs:
                print("No cached outputs found matching filter criteria.")
                sys.exit(0)

        run_stage2_judge(
            outputs=outputs,
            results_path=results_path,
            report_path=report_path,
            mock=args.mock,
            workers=args.workers,
            delay=args.delay,
        )


if __name__ == "__main__":
    main()
