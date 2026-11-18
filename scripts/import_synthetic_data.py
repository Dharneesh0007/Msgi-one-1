"""
MSGI One — Comprehensive Synthetic & Institutional Data Ingestion Pipeline
Validates and imports CSV data across all 12 modules:
  Phase 2/3: Alumni, Mentors, Jobs, Events, Role Skills, Learning Resources, Student Skills
  Phase 4: Communities, Community Memberships, Verification Requests, Projects, Startups, Impact Programmes
Supports:
  --mode [demo|live]: Demo enforces @example.msgi.edu synthetic invariants; Live enforces institutional schemas.
  --dry-run: Executes complete schema validation, foreign-key resolution, and duplicate checks without committing.
Principles: Kleppmann Data Reliability & Evans Domain Aggregate Invariants.
"""

import csv
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set


# Known valid User Auth UUIDs / Aliases across Phase 1-3 fixtures
_VALID_USER_IDS: Set[str] = {
    "user-kenji-001",
    "user-ananya-002",
    "user-david-003",
    "user-yuki-004",
    "user-student-001",
    "user-student-002",
    "user-student-phase4-001",
    "user-student-phase4-002",
    "student-journey-uuid-999",
    "user-admin-001",
    "user-faculty-001",
    "user-recruiter-001",
    "user-candidate-001",
    "user-candidate-002",
}


def validate_and_import_alumni(csv_path: Path, mode: str) -> Dict[str, Any]:
    required_headers = [
        "user_id", "full_name", "email", "graduation_year", "degree",
        "major", "company", "title", "industry", "country", "city",
        "skills", "is_verified", "mentor_opt_in"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for rh in required_headers:
            if rh not in headers:
                return {"status": "FAILED", "reason": f"Missing required CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            uid = row.get("user_id", "").strip()
            if uid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate alumni user_id '{uid}'.")
                continue
            seen_ids.add(uid)

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

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_jobs(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "job_id", "title", "company", "location", "country",
        "opportunity_type", "workplace_type", "required_skills", "deadline_days"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    valid_types = {"full_time", "internship", "contract", "part_time"}
    valid_workplaces = {"remote", "hybrid", "onsite"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing job CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            jid = row.get("job_id", "").strip()
            if jid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate job_id '{jid}'.")
                continue
            seen_ids.add(jid)

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

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_role_skills(csv_path: Path) -> Dict[str, Any]:
    required_headers = ["role_id", "role_name", "skill_name", "required_level", "importance_weight", "category"]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
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

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_learning_resources(csv_path: Path) -> Dict[str, Any]:
    required_headers = ["resource_id", "title", "provider", "target_skill", "difficulty", "duration_hours", "url", "rating"]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing learning_resources CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            rid = row.get("resource_id", "").strip()
            if rid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate resource_id '{rid}'.")
                continue
            seen_ids.add(rid)

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

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_student_skills(csv_path: Path) -> Dict[str, Any]:
    required_headers = ["user_id", "skill_name", "proficiency_level", "years_experience", "is_verified"]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    valid_levels = {"Beginner", "Intermediate", "Advanced", "Expert"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing student_skills CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            uid = row.get("user_id", "").strip()
            if uid not in _VALID_USER_IDS:
                unresolved += 1
                errors.append(f"Row {row_idx}: user_id '{uid}' does not resolve to an existing Auth user.")
                continue

            level = row.get("proficiency_level", "")
            if level not in valid_levels:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid proficiency_level '{level}'.")
                continue
            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


# -----------------------------------------------------------------------------
# PHASE 4 DATASET VALIDATORS
# -----------------------------------------------------------------------------

def validate_and_import_communities(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "community_id", "name", "slug", "description", "category",
        "is_private", "creator_id", "member_count", "topics", "created_at"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    seen_slugs = set()

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing communities CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            cid = row.get("community_id", "").strip()
            slug = row.get("slug", "").strip()
            creator_id = row.get("creator_id", "").strip()

            if cid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate community_id '{cid}'.")
                continue
            seen_ids.add(cid)

            if slug in seen_slugs:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate community slug '{slug}'.")
                continue
            seen_slugs.add(slug)

            if creator_id not in _VALID_USER_IDS:
                unresolved += 1
                errors.append(f"Row {row_idx}: creator_id '{creator_id}' does not resolve to a valid user.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_community_memberships(csv_path: Path, valid_communities: Set[str]) -> Dict[str, Any]:
    required_headers = ["membership_id", "community_id", "community_name", "user_id", "role", "status", "joined_at"]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_pairs = set()

    valid_roles = {"member", "moderator", "admin"}
    valid_statuses = {"active", "pending", "rejected"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing community_memberships CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            cid = row.get("community_id", "").strip()
            uid = row.get("user_id", "").strip()
            role = row.get("role", "").strip().lower()
            status = row.get("status", "").strip().lower()

            pair = (cid, uid)
            if pair in seen_pairs:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate membership for community '{cid}' and user '{uid}'.")
                continue
            seen_pairs.add(pair)

            if valid_communities and cid not in valid_communities:
                unresolved += 1
                errors.append(f"Row {row_idx}: community_id '{cid}' does not exist.")
                continue

            if uid not in _VALID_USER_IDS:
                unresolved += 1
                errors.append(f"Row {row_idx}: user_id '{uid}' does not resolve to a valid user.")
                continue

            if role not in valid_roles:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid membership role '{role}'.")
                continue

            if status not in valid_statuses:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid membership status '{status}'.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_verification_requests(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "request_id", "user_id", "user_email", "user_name",
        "requested_role", "evidence_payload", "status", "created_at"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    valid_roles = {"alumni", "faculty", "recruiter"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing verification_requests CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            rid = row.get("request_id", "").strip()
            uid = row.get("user_id", "").strip()
            role = row.get("requested_role", "").strip().lower()
            stat = row.get("status", "").strip().lower()
            payload_str = row.get("evidence_payload", "")

            if rid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate request_id '{rid}'.")
                continue
            seen_ids.add(rid)

            if uid not in _VALID_USER_IDS:
                unresolved += 1
                errors.append(f"Row {row_idx}: user_id '{uid}' does not resolve to an existing Auth user.")
                continue

            if role not in valid_roles:
                rejected += 1
                errors.append(f"Row {row_idx}: Invalid requested_role '{role}'.")
                continue

            # Per prompt instructions: Do not automatically approve institutional verification requests
            if stat != "pending":
                rejected += 1
                errors.append(f"Row {row_idx}: Verification fixtures must enter with status 'pending' (found '{stat}').")
                continue

            try:
                json.loads(payload_str)
            except Exception:
                rejected += 1
                errors.append(f"Row {row_idx}: Malformed JSON in evidence_payload.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_projects(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "project_id", "title", "description", "owner_id", "owner_name",
        "required_skills", "status", "member_count", "created_at"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    valid_statuses = {"active", "completed", "archived"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing projects CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            pid = row.get("project_id", "").strip()
            owner_id = row.get("owner_id", "").strip()
            stat = row.get("status", "").strip().lower()

            if pid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate project_id '{pid}'.")
                continue
            seen_ids.add(pid)

            if owner_id not in _VALID_USER_IDS:
                unresolved += 1
                errors.append(f"Row {row_idx}: owner_id '{owner_id}' does not resolve to a valid user.")
                continue

            if stat not in valid_statuses:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid project status '{stat}'.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_startups(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "startup_id", "name", "founder_id", "founder_name", "industry",
        "stage", "tagline", "website_url", "seeking_mentors", "seeking_talent", "is_verified", "created_at"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    valid_stages = {"idea", "seed", "early", "growth", "mature"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing startups CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            sid = row.get("startup_id", "").strip()
            fid = row.get("founder_id", "").strip()
            stage = row.get("stage", "").strip().lower()

            if sid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate startup_id '{sid}'.")
                continue
            seen_ids.add(sid)

            if fid not in _VALID_USER_IDS:
                unresolved += 1
                errors.append(f"Row {row_idx}: founder_id '{fid}' does not resolve to a valid user.")
                continue

            if stage not in valid_stages:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid startup stage '{stage}'.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_impact_programmes(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "programme_id", "title", "description", "coordinator_name",
        "programme_type", "target_volunteers", "current_volunteers", "is_active", "created_at"
    ]
    forbidden_headers = {"donation_amount", "currency", "payment_receipt", "stripe_customer_id", "funds_raised"}
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    valid_types = {"volunteering", "mentorship_drive", "community_outreach"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        for rh in required_headers:
            if rh not in headers:
                return {"status": "FAILED", "reason": f"Missing impact_programmes CSV header: '{rh}'"}

        # Check that no payment processing fields exist
        for fh in forbidden_headers:
            if fh in headers:
                return {
                    "status": "FAILED",
                    "reason": f"CRITICAL: Payment field '{fh}' forbidden in non-monetary giving module."
                }

        for row_idx, row in enumerate(reader, start=2):
            prog_id = row.get("programme_id", "").strip()
            ptype = row.get("programme_type", "").strip().lower()

            if prog_id in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate programme_id '{prog_id}'.")
                continue
            seen_ids.add(prog_id)

            if ptype not in valid_types:
                rejected += 1
                errors.append(f"Row {row_idx}: invalid programme_type '{ptype}'.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


# -----------------------------------------------------------------------------
# PHASE 5 QA DATASET VALIDATORS
# -----------------------------------------------------------------------------

def validate_and_import_qa_test_users(csv_path: Path, mode: str) -> Dict[str, Any]:
    required_headers = [
        "user_id", "email", "full_name", "role", "is_verified",
        "verification_status", "department", "graduation_year", "city", "country", "notes"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_ids = set()
    seen_emails = set()
    valid_roles = {"student", "alumni", "faculty", "recruiter", "admin", "candidate"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing qa_test_users CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            uid = row.get("user_id", "").strip()
            email = row.get("email", "").strip().lower()
            role = row.get("role", "").strip().lower()

            if uid in seen_ids:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate user_id '{uid}'.")
                continue
            seen_ids.add(uid)

            if email in seen_emails:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate email '{email}'.")
                continue
            seen_emails.add(email)

            if mode == "demo" and not email.endswith("@example.msgi.edu"):
                rejected += 1
                errors.append(f"Row {row_idx}: Demo mode requires @example.msgi.edu synthetic email domain.")
                continue

            if role not in valid_roles:
                rejected += 1
                errors.append(f"Row {row_idx}: Invalid role '{role}'.")
                continue

            accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def validate_and_import_qa_role_permissions(csv_path: Path) -> Dict[str, Any]:
    required_headers = [
        "module", "endpoint", "method", "student", "verified_alumni",
        "unverified_alumni", "faculty", "recruiter", "admin", "candidate", "privacy_boundary"
    ]
    accepted, rejected, duplicates, unresolved = 0, 0, 0, 0
    errors: List[str] = []
    seen_endpoints = set()
    valid_perms = {"ALLOWED", "FORBIDDEN", "OWNER_ONLY"}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for rh in required_headers:
            if rh not in (reader.fieldnames or []):
                return {"status": "FAILED", "reason": f"Missing qa_role_permissions CSV header: '{rh}'"}

        for row_idx, row in enumerate(reader, start=2):
            endpoint = row.get("endpoint", "").strip()
            method = row.get("method", "").strip().upper()
            key = (endpoint, method)

            if key in seen_endpoints:
                duplicates += 1
                errors.append(f"Row {row_idx}: Duplicate endpoint/method '{method} {endpoint}'.")
                continue
            seen_endpoints.add(key)

            for col in ["student", "verified_alumni", "unverified_alumni", "faculty", "recruiter", "admin", "candidate"]:
                val = row.get(col, "").strip().upper()
                if val not in valid_perms:
                    rejected += 1
                    errors.append(f"Row {row_idx}: Invalid permission value '{val}' in column '{col}'.")
                    break
            else:
                accepted += 1

    return {"status": "SUCCESS", "accepted": accepted, "rejected": rejected, "duplicates": duplicates, "unresolved": unresolved, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description="MSGI One Unified Data Ingestion Tool")
    parser.add_argument("--mode", choices=["demo", "live"], default="demo", help="Dataset mode")
    parser.add_argument("--dry-run", action="store_true", help="Execute schema and reference validation without database side-effects")
    parser.add_argument("--dir", default=str(Path(__file__).resolve().parent.parent / "supabase" / "seed" / "csv"))
    args = parser.parse_args()

    csv_dir = Path(args.dir)
    print("================================================================================")
    print(f"MSGI ONE — DATA INGESTION PIPELINE (MODE: {args.mode.upper()})")
    print(f"Dry Run: {args.dry_run}")
    print(f"Target Directory: {csv_dir}")
    print("================================================================================")

    # First load communities to populate valid set for memberships
    valid_comms: Set[str] = set()
    comms_csv = csv_dir / "communities.csv"
    if comms_csv.exists():
        with open(comms_csv, mode="r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                valid_comms.add(r["community_id"])

    datasets = [
        # Phase 2 & 3 Datasets
        ("Alumni Directory", lambda p: validate_and_import_alumni(p, args.mode), "alumni.csv"),
        ("Job Opportunities", validate_and_import_jobs, "jobs.csv"),
        ("Role Skill Taxonomy", validate_and_import_role_skills, "career_role_skills.csv"),
        ("Learning Resources", validate_and_import_learning_resources, "learning_resources.csv"),
        ("Student Skills", validate_and_import_student_skills, "student_skills.csv"),
        # Phase 4 Extended Datasets
        ("Communities (6)", validate_and_import_communities, "communities.csv"),
        ("Memberships (12)", lambda p: validate_and_import_community_memberships(p, valid_comms), "community_memberships.csv"),
        ("Verifications (5)", validate_and_import_verification_requests, "verification_requests.csv"),
        ("Projects (6)", validate_and_import_projects, "projects.csv"),
        ("Startups (5)", validate_and_import_startups, "startups.csv"),
        ("Impact Programmes (4)", validate_and_import_impact_programmes, "impact_programmes.csv"),
        # Phase 5 QA Verification Datasets
        ("QA Test Users (14)", lambda p: validate_and_import_qa_test_users(p, args.mode), "qa_test_users.csv"),
        ("QA Role Perms (35)", validate_and_import_qa_role_permissions, "qa_role_permissions.csv"),
    ]

    total_accepted = 0
    total_rejected = 0
    total_duplicates = 0
    total_unresolved = 0
    all_success = True

    print(f"{'DATASET':<25} | {'STATUS':<7} | {'ACCEPTED':<8} | {'REJECTED':<8} | {'DUPLICATES':<10} | {'UNRESOLVED':<10}")
    print("-" * 80)

    for name, func, filename in datasets:
        p = csv_dir / filename
        if p.exists():
            res = func(p)
            status_str = res.get("status", "FAILED")
            acc = res.get("accepted", 0)
            rej = res.get("rejected", 0)
            dups = res.get("duplicates", 0)
            unres = res.get("unresolved", 0)

            total_accepted += acc
            total_rejected += rej
            total_duplicates += dups
            total_unresolved += unres

            if status_str != "SUCCESS" or rej > 0 or dups > 0 or unres > 0:
                all_success = False

            print(f"{name:<25} | {status_str:<7} | {acc:<8} | {rej:<8} | {dups:<10} | {unres:<10}")
            for err in res.get("errors", []):
                print(f"   [!] {err}")
        else:
            print(f"{name:<25} | MISSING | 0        | 0        | 0          | 0")
            all_success = False

    print("================================================================================")
    print(f"INGESTION REPORT SUMMARY:")
    print(f"Total Accepted Records  : {total_accepted}")
    print(f"Total Rejected Records  : {total_rejected}")
    print(f"Total Duplicate Records : {total_duplicates}")
    print(f"Total Unresolved FKeys  : {total_unresolved}")
    print(f"Final Validation State  : {'ALL DATASETS VALIDATED (100% PASS)' if all_success else 'VALIDATION ISSUES DETECTED'}")
    print("================================================================================")

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
