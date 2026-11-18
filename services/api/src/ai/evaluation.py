"""
MSGI One — AI Evaluation Suite
Evaluates the 15 canonical test cases against the MSGI AI Command Centre.
Principles: Pressman QA Metrics & Somerville Traceability.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.ai.graph import run_command_centre
from src.core.dependencies import AuthenticatedUser


def run_evaluation_suite() -> Dict[str, Any]:
    eval_file = Path(__file__).resolve().parents[4] / "supabase" / "seed" / "ai_evaluation_cases.jsonl"
    if not eval_file.exists():
        raise FileNotFoundError(f"Evaluation file '{eval_file}' not found.")

    cases: List[Dict[str, Any]] = []
    with open(eval_file, mode="r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))

    passed = 0
    failed = 0
    results: List[Dict[str, Any]] = []

    print("================================================================================")
    print(f"MSGI ONE — AI COMMAND CENTRE EVALUATION SUITE ({len(cases)} SCENARIOS)")
    print("================================================================================")

    for case in cases:
        case_id = case["id"]
        category = case["category"]
        prompt = case["user_input"]
        user_roles = case.get("user_roles", ["student"])

        test_user = AuthenticatedUser(
            id=f"user-eval-{case_id}",
            email=f"eval.{case_id}@example.msgi.edu",
            first_name="Eval",
            last_name="Tester",
            roles=user_roles,
            is_verified=True,
        )

        res = run_command_centre(prompt=prompt, user=test_user, session_id=f"sess-{case_id}")

        status_ok = True
        error_notes: List[str] = []

        # Check safety check if expected
        if case.get("safety_check"):
            if res.get("status") != "rejected":
                status_ok = False
                error_notes.append(f"Expected status 'rejected', got '{res.get('status')}'")
        else:
            # Check route/intent
            expected_route = case.get("expected_route")
            if expected_route and res.get("intent") != expected_route:
                status_ok = False
                error_notes.append(f"Expected route '{expected_route}', got '{res.get('intent')}'")

            # Check human approval requirement
            if case.get("requires_human_approval"):
                if res.get("status") != "interrupted" or not res.get("pending_approval"):
                    status_ok = False
                    error_notes.append("Expected action to be interrupted for human approval")

            # Check expected entities
            for ent in case.get("expected_entities", []):
                ent_lower = ent.lower()
                summary_lower = res.get("final_summary", "").lower()
                evidence_text = json.dumps(res.get("evidence", [])).lower()
                actions_text = json.dumps(res.get("action_logs", [])).lower()

                if ent_lower not in summary_lower and ent_lower not in evidence_text and ent_lower not in actions_text:
                    status_ok = False
                    error_notes.append(f"Expected entity '{ent}' not found in summary or evidence")

        if status_ok:
            passed += 1
            status_str = "PASS"
        else:
            failed += 1
            status_str = "FAIL"

        print(f"[{status_str}] {case_id:10} | {category:30} | Latency: {res.get('latency_ms', 0)}ms")
        for err in error_notes:
            print(f"       -> ERROR: {err}")

        results.append({
            "id": case_id,
            "category": category,
            "status": status_str,
            "latency_ms": res.get("latency_ms", 0),
            "errors": error_notes,
        })

    print("================================================================================")
    print(f"EVALUATION SUMMARY: {passed}/{len(cases)} Passed ({round(passed / len(cases) * 100, 1)}%) | Failed: {failed}")
    print("================================================================================")

    return {
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(cases) * 100, 1),
        "results": results,
    }


if __name__ == "__main__":
    run_evaluation_suite()
