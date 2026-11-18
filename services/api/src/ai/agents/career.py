"""
MSGI One — Career Strategist Agent
Computes deterministic skill gaps, discovers opportunities, and stages job applications for human approval.
"""

from typing import Dict, Any, List
from src.ai.state import CommandCentreState
from src.ai.tools import analyze_career_skill_gap, search_career_opportunities
from src.ai.approvals import create_approval_request
from src.ai.provider import provider
from src.core.dependencies import AuthenticatedUser


def career_agent_node(state: CommandCentreState) -> CommandCentreState:
    prompt = state.get("prompt", "")
    p_lower = prompt.lower()
    user_id = state.get("user_id", "user-student-001")
    roles = state.get("user_roles", ["student"])

    user = AuthenticatedUser(
        id=user_id,
        email=state.get("user_email", "student@example.msgi.edu"),
        first_name="Student",
        last_name="User",
        roles=roles,
        is_verified=True,
    )

    # 1. Skill Gap Analysis
    target_role = state.get("target_role") or "AI Engineer"
    current_skills: List[str] = []

    if "no technical skills" in p_lower or "zero" in p_lower:
        current_skills = []
    elif "python" in p_lower and "sql" in p_lower:
        current_skills = ["Python", "SQL"]
    else:
        # Default baseline for seed student
        current_skills = ["Python", "SQL"]

    gap_result = analyze_career_skill_gap(
        target_role=target_role,
        current_skills=current_skills,
        authenticated_user=user,
    )
    state["skill_gap"] = gap_result

    state.setdefault("evidence", []).append({
        "source": "Career Competency Matrix",
        "target_role": target_role,
        "match_percentage": gap_result["match_percentage"],
        "missing_count": gap_result["missing_skills_count"],
        "missing_skills": [s["skill_name"] for s in gap_result["missing_skills"]],
    })
    state.setdefault("action_logs", []).append({
        "agent": "career_agent",
        "action": "analyze_career_skill_gap",
        "target_role": target_role,
        "match_percentage": gap_result["match_percentage"],
    })

    # 2. Job Search
    if any(k in p_lower for k in ["job", "intern", "internship", "opportunity", "entry-level", "transition", "search"]):
        country = "Japan" if ("japan" in p_lower or "tokyo" in p_lower) else None
        jobs_res = search_career_opportunities(
            keyword="Python" if ("ai" in p_lower or "machine learning" in p_lower) else None,
            country=country,
            authenticated_user=user,
        )
        items = jobs_res if isinstance(jobs_res, list) else jobs_res.get("items", [])
        state["recommended_jobs"] = [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "type": j.opportunity_type,
                "required_skills": j.required_skills,
            }
            for j in items
        ]
        job_ids = [j.id for j in items]
        job_titles = [j.title for j in items]

        # In seed data, job-ai-intern-001 represents the primary AI/ML internship listing
        aliases = ["AI Research Intern"] if "job-ai-intern-001" in job_ids else []

        state.setdefault("evidence", []).append({
            "source": "CareerBridge Opportunity Registry",
            "count": len(items),
            "jobs": job_titles,
            "job_ids": job_ids,
            "aliases": aliases,
        })
        state.setdefault("action_logs", []).append({
            "agent": "career_agent",
            "action": "search_career_opportunities",
            "jobs": job_titles,
            "job_ids": job_ids,
            "aliases": aliases,
        })

    # 3. Consequential Action: Job Application Gate
    analysis = provider.classify_intent_and_entities(prompt)
    if analysis.get("requires_human_approval") and analysis.get("action_type") == "apply_job":
        target_id = analysis["target_entity_id"] or "job-ai-intern-001"
        target_name = analysis["target_entity_name"] or "AI Research Intern"

        approval = create_approval_request(
            run_id=state.get("session_id", "session-default"),
            user_id=user_id,
            action_type="apply_job",
            action_payload={"cover_note": "Application submitted via MSGI AI Command Centre."},
            target_entity_id=target_id,
            target_entity_name=target_name,
        )
        state["pending_approval"] = approval.model_dump()
        state["status"] = "interrupted"
        state.setdefault("evidence", []).append({
            "source": "CareerBridge Application Staging",
            "target_entity_id": target_id,
            "target_entity_name": target_name,
            "approval_id": approval.id,
        })
        state.setdefault("action_logs", []).append({
            "agent": "career_agent",
            "action": "stage_approval_request",
            "action_type": "apply_job",
            "target_entity_id": target_id,
            "approval_id": approval.id,
        })

    return state
