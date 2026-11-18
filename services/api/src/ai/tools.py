"""
MSGI One — AI Agent Tool Registry
Wraps Phase 2 domain services into 10 typed, schema-validated tools.
Principles: Evans Domain Services & Sommerville Traceability.
"""

import csv
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.core.dependencies import AuthenticatedUser
from src.services.alumni_service import search_alumni
from src.services.mentor_service import search_mentors, create_mentor_request
from src.services.jobs_service import search_jobs, submit_job_application
from src.services.events_service import search_events, register_for_event, check_event_capacity
from src.schemas.business import MentorRequestCreate, JobApplicationRequest


# Path to seed CSVs for skill taxonomies and learning resources
_SEED_DIR = Path(__file__).resolve().parents[4] / "supabase" / "seed" / "csv"


def _load_career_role_skills() -> List[Dict[str, Any]]:
    skills_file = _SEED_DIR / "career_role_skills.csv"
    if not skills_file.exists():
        return []
    with open(skills_file, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _load_learning_resources() -> List[Dict[str, Any]]:
    res_file = _SEED_DIR / "learning_resources.csv"
    if not res_file.exists():
        return []
    with open(res_file, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. Alumni Discovery Tool
def search_alumni_network(
    query: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> Dict[str, Any]:
    filters = {}
    if query:
        filters["query"] = query
    if industry:
        filters["industry"] = industry
    if country:
        filters["country"] = country
    filters["verified_only"] = True
    return search_alumni(filters=filters, authenticated_user=authenticated_user)


# 2. Mentor Matching Tool
def find_recommended_mentors(
    student_goal: Optional[str] = None,
    topic: Optional[str] = None,
    country: Optional[str] = None,
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> List[Dict[str, Any]]:
    filters = {}
    if student_goal:
        filters["student_goal"] = student_goal
    if topic:
        filters["topic"] = topic
    if country:
        filters["country"] = country
    results = search_mentors(filters=filters, authenticated_user=authenticated_user)
    return [m.model_dump() for m in results]


# 3. Create Mentor Request Tool (Mutating Action)
def create_mentor_request_tool(
    mentor_user_id: str,
    topic: str,
    message: str,
    authenticated_user: AuthenticatedUser,
) -> Dict[str, Any]:
    req = MentorRequestCreate(
        mentor_user_id=mentor_user_id,
        topic=topic,
        message=message,
    )
    result = create_mentor_request(req, student=authenticated_user)
    return result.model_dump()


# 4. Search Career Opportunities Tool
def search_career_opportunities(
    keyword: Optional[str] = None,
    opportunity_type: Optional[str] = None,
    country: Optional[str] = None,
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> List[Any]:
    filters = {}
    if keyword:
        filters["skill"] = keyword
    if opportunity_type:
        filters["opportunity_type"] = opportunity_type
    if country:
        filters["country"] = country
    return search_jobs(filters=filters, authenticated_user=authenticated_user)


# 5. Submit Job Application Tool (Mutating Action)
def submit_job_application_tool(
    job_id: str,
    cover_note: str,
    authenticated_user: AuthenticatedUser,
) -> Dict[str, Any]:
    req = JobApplicationRequest(cover_note=cover_note)
    result = submit_job_application(job_id=job_id, application_data=req, applicant=authenticated_user)
    return result.model_dump()


# 6. Search Institutional Events Tool
def search_institutional_events(
    topic: Optional[str] = None,
    event_type: Optional[str] = None,
    country: Optional[str] = None,
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> Dict[str, Any]:
    filters = {}
    if topic:
        filters["topic"] = topic
    if event_type:
        filters["event_type"] = event_type
    if country:
        filters["country"] = country
    return search_events(filters=filters, authenticated_user=authenticated_user)


# 7. Register For Event Tool (Mutating Action)
def register_for_event_tool(
    event_id: str,
    authenticated_user: AuthenticatedUser,
) -> Dict[str, Any]:
    result = register_for_event(event_id=event_id, user=authenticated_user)
    return result.model_dump()


# 8. Check Event Capacity Tool
def check_event_capacity_tool(
    event_id: str,
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> Dict[str, Any]:
    return check_event_capacity(event_id=event_id)


# 9. Career Skill Gap Analysis Tool
def analyze_career_skill_gap(
    target_role: str,
    current_skills: List[str],
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> Dict[str, Any]:
    """
    Compares student's baseline skills with canonical career role requirements.
    Computes match percentage, missing skills, and priority weights.
    """
    all_role_skills = _load_career_role_skills()
    matched_role_skills = [
        s for s in all_role_skills
        if s["role_name"].lower() == target_role.lower()
    ]

    if not matched_role_skills:
        # Fallback to AI Engineer if role not matched exactly
        matched_role_skills = [s for s in all_role_skills if s["role_name"] == "AI Engineer"]
        target_role = "AI Engineer"

    current_skills_clean = {s.strip().lower() for s in current_skills}

    covered: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []

    total_weight = 0
    acquired_weight = 0

    for r in matched_role_skills:
        w = int(r.get("importance_weight", 3))
        total_weight += w
        skill_name = r["skill_name"]
        if skill_name.lower() in current_skills_clean:
            acquired_weight += w
            covered.append({
                "skill_name": skill_name,
                "required_level": r["required_level"],
                "importance_weight": w,
                "category": r["category"],
            })
        else:
            missing.append({
                "skill_name": skill_name,
                "required_level": r["required_level"],
                "importance_weight": w,
                "category": r["category"],
            })

    # Sort missing by importance weight descending
    missing.sort(key=lambda x: x["importance_weight"], reverse=True)

    match_percentage = round((acquired_weight / total_weight * 100), 1) if total_weight > 0 else 0.0

    return {
        "target_role": target_role,
        "match_percentage": match_percentage,
        "covered_skills": covered,
        "missing_skills": missing,
        "total_required_skills": len(matched_role_skills),
        "missing_skills_count": len(missing),
    }


# 10. Generate Learning Roadmap Tool
def generate_learning_roadmap(
    missing_skills: List[str],
    authenticated_user: Optional[AuthenticatedUser] = None,
) -> List[Dict[str, Any]]:
    """
    Curates learning resources sequenced by skill importance.
    """
    all_resources = _load_learning_resources()
    missing_lower = {s.strip().lower() for s in missing_skills}

    roadmap_steps: List[Dict[str, Any]] = []
    step_num = 1

    for res in all_resources:
        if res["target_skill"].lower() in missing_lower:
            roadmap_steps.append({
                "step": step_num,
                "skill": res["target_skill"],
                "course_title": res["title"],
                "provider": res["provider"],
                "difficulty": res["difficulty"],
                "duration_hours": float(res["duration_hours"]),
                "url": res["url"],
                "rating": float(res["rating"]),
            })
            step_num += 1

    return roadmap_steps
