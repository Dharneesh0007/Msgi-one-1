"""
MSGI One — Phase 3 Comprehensive Verification Script
Agentic AI Command Centre: Master Orchestrator + Domain Agents + HITL Approvals.
Principles: Pressman QA Metrics & Somerville Verification.
"""

import sys
import subprocess
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_API_DIR = _ROOT / "services" / "api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))


def run_step(step_name: str, cmd_list: list) -> bool:
    print(f"\n---> [STEP] {step_name}")
    start = time.time()
    try:
        res = subprocess.run(cmd_list, cwd=str(_ROOT), capture_output=True, text=True, check=True)
        elapsed = round(time.time() - start, 2)
        print(f"      Status: PASS ({elapsed}s)")
        if res.stdout:
            lines = res.stdout.strip().splitlines()
            for line in lines[-5:]:
                print(f"      {line}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"      Status: FAIL ({round(time.time() - start, 2)}s)")
        print(f"      Error: {e.stderr or e.stdout}")
        return False


def main():
    print("================================================================================")
    print("MSGI ONE — PHASE 3 FULL VERIFICATION & EVIDENCE SUITE")
    print("================================================================================")

    steps = [
        (
            "1. Validate Synthetic CSV Ingestion",
            ["uv", "run", "--offline", "--no-sync", "--project", "services/api", "python", "scripts/import_synthetic_data.py"],
        ),
        (
            "2. Run AI Command Centre 15-Scenario Evaluation Suite",
            ["uv", "run", "--offline", "--no-sync", "--project", "services/api", "python", "services/api/src/ai/evaluation.py"],
        ),
        (
            "3. Run Full Pytest Regression Suite (61 Tests)",
            ["uv", "run", "--offline", "--no-sync", "--project", "services/api", "pytest", "services/api/tests", "-q"],
        ),
    ]

    all_pass = True
    for name, cmd in steps:
        if not run_step(name, cmd):
            all_pass = False
            break

    print("\n================================================================================")
    if all_pass:
        print("PHASE 3 VERIFICATION COMPLETE: ALL GATES PASS (100% READY FOR REVIEW)")
    else:
        print("PHASE 3 VERIFICATION FAILED: Review step logs above.")
    print("================================================================================")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
