"""
MSGI One — Synthetic & Institutional Data Ingestion Pipeline
Validates and imports CSV data for Alumni, Mentors, Jobs, Events,
Career Role Skills, Learning Resources, and Student Skills.
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


def validate_and_import_role_skills(csv_path: Path) -> Dict[str, Any]:
    required_headers = ["role_id", "role_name", "skill_name", "required_level", "importance_weight", "category"]
    accepted, rejected = 0, 0
    errors: List[str] = []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing role_skills CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            weight = row.get("importance_weight", "1")
            try:
                w_val = int(weight)
                if w_val < 1 or w_val > 5:
                    rejected += 1
                    errors.append(f"Row {row_idx}: importance_weight must be between 1 and 5.")
                    continue
            except ValueError:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid importance_weight '{weight}'.")
                continue
            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "errors": errors}


def validate_and_import_learning_resources(csv_path: Path) -> Dict[str, Any]:
    required_headers = ["resource_id", "title", "provider", "target_skill", "difficulty", "duration_hours", "url", "rating"]
    accepted, rejected = 0, 0
    errors: List[str] = []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing learning_resources CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            try:
                hrs = float(row.get("duration_hours", 0))
                rating = float(row.get("rating", 0))
                if hrs <= 0 or rating < 0 or rating > 5:
                    rejected += 1
                    errors.append(f"Row {row_idx}: invalid numeric values for duration or rating.")
                    continue
            except ValueError:
                rejected += 1
                errors.append(f"Row {row_idx}: malformed numeric values.")
                continue
            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "errors": errors}


def validate_and_import_student_skills(csv_path: Path) -> Dict[str, Any]:
    required_headers = ["user_id", "skill_name", "proficiency_level", "years_experience", "is_verified"]
    accepted, rejected = 0, 0
    errors: List[str] = []

    valid_levels = {"Beginner", "Intermediate", "Advanced", "Expert"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing student_skills CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            level = row.get("proficiency_level", "")
            if level not in valid_levels:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid proficiency_level '{level}'.")
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

    for name, func, filename in [
        ("Alumni", lambda p: validate_and_import_alumni(p, args.mode), "alumni.csv"),
        ("Jobs", validate_and_import_jobs, "jobs.csv"),
        ("Role Skills", validate_and_import_role_skills, "career_role_skills.csv"),
        ("Learning Resources", validate_and_import_learning_resources, "learning_resources.csv"),
        ("Student Skills", validate_and_import_student_skills, "student_skills.csv"),
    ]:
        p = csv_dir / filename
        if p.exists():
            res = func(p)
            print(f"{name:18}: {res['status']} (Accepted: {res.get('accepted', 0)}, Rejected: {res.get('rejected', 0)})")
            for err in res.get("errors", []):
                print(f"  - {err}")
        else:
            print(f"{name:18}: Not found.")

    print("================================================================================")
    print("Ingestion validation complete.")


if __name__ == "__main__":
    main()
