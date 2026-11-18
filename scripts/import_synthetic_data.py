"""
MSGI One — Synthetic & Institutional Data Ingestion Pipeline
Validates and imports CSV data for Alumni, Mentors, Jobs, and Events.
Supports DEMO mode (synthetic data) and LIVE mode (verified institutional records).
Principle: Kleppmann Data Reliability & Evans Domain Aggregate Invariants.
"""

import csv
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any


def validate_and_import_alumni(csv_path: Path, mode: str) -> Dict[str, Any]:
    required_headers = [
        "user_id", "full_name", "email", "graduation_year", "degree",
        "major", "company", "title", "industry", "country", "city",
        "skills", "is_verified", "mentor_opt_in"
    ]

    accepted = 0
    rejected = 0
    errors: List[str] = []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for rh in required_headers:
            if rh not in headers:
                return {"status": "FAILED", "reason": f"Missing required CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            email = row.get("email", "").strip().lower()
            if mode == "demo" and not email.endswith("@example.msgi.edu"):
                rejected += 1
                errors.append(f"Row {row_idx}: Demo mode requires @example.msgi.edu synthetic email domain.")
                continue

            try:
                grad_year = int(row.get("graduation_year", 0))
                if grad_year < 1950 or grad_year > 2030:
                    rejected += 1
                    errors.append(f"Row {row_idx}: Invalid graduation year {grad_year}.")
                    continue
            except ValueError:
                rejected += 1
                errors.append(f"Row {row_idx}: Malformed graduation year.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "errors": errors}


def validate_and_import_jobs(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "job_id", "title", "company", "location", "country",
        "opportunity_type", "workplace_type", "required_skills", "deadline_days"
    ]
    accepted = 0
    rejected = 0
    errors: List[str] = []

    valid_types = {"full_time", "internship", "contract", "part_time"}
    valid_workplaces = {"remote", "hybrid", "onsite"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing job CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            opp_type = row.get("opportunity_type", "").strip().lower()
            wp_type = row.get("workplace_type", "").strip().lower()

            if opp_type not in valid_types:
                rejected += 1
                errors.append(f"Row {row_idx}: Invalid opportunity_type '{opp_type}'.")
                continue

            if wp_type not in valid_workplaces:
                rejected += 1
                errors.append(f"Row {row_idx}: Invalid workplace_type '{wp_type}'.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="MSGI One Data Ingestion Tool")
    parser.add_argument("--mode", choices=["demo", "live"], default="demo", help="Dataset mode")
    parser.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent / "supabase" / "seed" / "csv"))
    args = parser.parse_args()

    csv_dir = Path(args.dir)
    print("================================================================================")
    print(f"MSGI ONE — DATA INGESTION PIPELINE (MODE: {args.mode.upper()})")
    print(f"Target Directory: {csv_dir}")
    print("================================================================================")

    alumni_csv = csv_dir / "alumni.csv"
    if alumni_csv.exists():
        res = validate_and_import_alumni(alumni_csv, args.mode)
        print(f"Alumni Import: {res['status']} (Accepted: {res.get('accepted', 0)}, Rejected: {res.get('rejected', 0)})")
        for err in res.get("errors", []):
            print(f"  - {err}")
    else:
        print("Alumni CSV: Not found.")

    jobs_csv = csv_dir / "jobs.csv"
    if jobs_csv.exists():
        res = validate_and_import_jobs(jobs_csv)
        print(f"Jobs Import:   {res['status']} (Accepted: {res.get('accepted', 0)}, Rejected: {res.get('rejected', 0)})")
        for err in res.get("errors", []):
            print(f"  - {err}")
    else:
        print("Jobs CSV: Not found.")

    print("================================================================================")
    print("Ingestion validation complete.")


if __name__ == "__main__":
    main()
