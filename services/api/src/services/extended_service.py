"""
MSGI One — Extended P1 Services: Collaboration, Startups & Social Impact
Modules:
  - Module 7: Collaboration & Innovation Hub
  - Module 8: Startup Ecosystem
  - Module 11: Giving and Social Impact (Volunteering only, NO live payment processing)
Principles: Evans Bounded Contexts & Sommerville Traceability.
"""

import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from src.core.dependencies import AuthenticatedUser
from src.services.notifications_service import create_notification


# Path to seed CSVs
_SEED_DIR = Path(__file__).resolve().parents[4] / "supabase" / "seed" / "csv"
if not _SEED_DIR.exists():
    for p in Path(__file__).resolve().parents:
        if (p / "supabase" / "seed" / "csv").exists():
            _SEED_DIR = p / "supabase" / "seed" / "csv"
            break


# -----------------------------------------------------------------------------
# MODULE 7: COLLABORATION & INNOVATION HUB
# -----------------------------------------------------------------------------

class ProjectItem(BaseModel):
    id: str
    title: str
    description: str
    owner_id: str
    owner_name: str
    required_skills: List[str]
    status: str
    member_count: int
    created_at: str
    is_member: bool = False


class ProjectMemberItem(BaseModel):
    id: str
    project_id: str
    project_title: str
    user_id: str
    role: str
    status: str
    created_at: str


def _load_all_projects() -> List[Dict[str, Any]]:
    csv_file = _SEED_DIR / "projects.csv"
    if not csv_file.exists():
        return [
            {
                "id": "proj-agentic-001",
                "title": "Autonomous Agricultural Drone Perception Pipeline",
                "description": "Multi-spectral computer vision models for automated crop yield estimation and pest detection.",
                "owner_id": "user-kenji-001",
                "owner_name": "Kenji Sato",
                "required_skills": ["Python", "PyTorch", "ROS 2", "Edge AI"],
                "status": "active",
                "member_count": 4,
                "created_at": "2026-09-10T00:00:00Z",
            },
            {
                "id": "proj-health-002",
                "title": "Decentralized Clinical Trial Data Exchange",
                "description": "Privacy-preserving zero-knowledge verification for multi-institutional health analytics.",
                "owner_id": "user-ananya-002",
                "owner_name": "Ananya Sharma",
                "required_skills": ["TypeScript", "FastAPI", "Cryptography"],
                "status": "active",
                "member_count": 3,
                "created_at": "2026-10-01T00:00:00Z",
            },
        ]
    results = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            results.append({
                "id": row["project_id"],
                "title": row["title"],
                "description": row["description"],
                "owner_id": row["owner_id"],
                "owner_name": row["owner_name"],
                "required_skills": [s.strip() for s in row.get("required_skills", "").split(";") if s.strip()],
                "status": row["status"],
                "member_count": int(row.get("member_count", 1)),
                "created_at": row["created_at"],
            })
    return results


_PROJECTS_STORE: List[Dict[str, Any]] = _load_all_projects()

_PROJECT_MEMBERS_STORE: List[Dict[str, Any]] = [
    {
        "id": "pm-001",
        "project_id": "proj-agentic-001",
        "project_title": "Autonomous Agricultural Drone Perception Pipeline",
        "user_id": "user-kenji-001",
        "role": "owner",
        "status": "active",
        "created_at": "2026-09-10T00:00:00Z",
    }
]


def list_projects(skill: Optional[str] = None, user: Optional[AuthenticatedUser] = None) -> List[ProjectItem]:
    user_id = user.id if user else None
    results: List[ProjectItem] = []
    for p in _PROJECTS_STORE:
        if skill:
            s_lower = skill.strip().lower()
            if not any(s_lower in rs.lower() for rs in p["required_skills"]):
                continue
        is_mem = any(m["project_id"] == p["id"] and m["user_id"] == user_id for m in _PROJECT_MEMBERS_STORE)
        results.append(ProjectItem(**p, is_member=is_mem))
    return results


def get_project_by_id(project_id: str, user: AuthenticatedUser) -> ProjectItem:
    p = next((x for x in _PROJECTS_STORE if x["id"] == project_id), None)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": f"Project '{project_id}' not found."},
        )
    is_mem = any(m["project_id"] == p["id"] and m["user_id"] == user.id for m in _PROJECT_MEMBERS_STORE)
    return ProjectItem(**p, is_member=is_mem)


def join_project_request(project_id: str, user: AuthenticatedUser) -> ProjectMemberItem:
    p = get_project_by_id(project_id, user)
    existing = next((m for m in _PROJECT_MEMBERS_STORE if m["project_id"] == project_id and m["user_id"] == user.id), None)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_PROJECT_REQUEST", "message": "You have already applied or joined this project."},
        )

    pm_id = f"pm-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": pm_id,
        "project_id": project_id,
        "project_title": p.title,
        "user_id": user.id,
        "role": "applicant",
        "status": "pending",
        "created_at": now_iso,
    }
    _PROJECT_MEMBERS_STORE.append(record)

    # Notify project owner
    create_notification(
        user_id=p.owner_id,
        event_type="project_join_requested",
        entity_id=project_id,
        title="Project Collaboration Request",
        message=f"{user.first_name} requested to join {p.title}.",
        payload={"project_id": project_id, "applicant_id": user.id},
    )

    return ProjectMemberItem(**record)


def get_my_projects(user: AuthenticatedUser) -> List[ProjectMemberItem]:
    user_pms = [m for m in _PROJECT_MEMBERS_STORE if m["user_id"] == user.id]
    return [ProjectMemberItem(**m) for m in user_pms]


# -----------------------------------------------------------------------------
# MODULE 8: STARTUP ECOSYSTEM
# -----------------------------------------------------------------------------

class StartupItem(BaseModel):
    id: str
    name: str
    founder_id: str
    founder_name: str
    industry: str
    stage: str
    tagline: str
    website_url: Optional[str] = None
    seeking_mentors: bool
    seeking_talent: bool
    is_verified: bool
    created_at: str


class StartupConnectionItem(BaseModel):
    id: str
    startup_id: str
    startup_name: str
    user_id: str
    intent: str
    message: str
    status: str
    created_at: str


def _load_all_startups() -> List[Dict[str, Any]]:
    csv_file = _SEED_DIR / "startups.csv"
    if not csv_file.exists():
        return [
            {
                "id": "start-neural-001",
                "name": "NeuralFlow Dynamics",
                "founder_id": "user-kenji-001",
                "founder_name": "Kenji Sato",
                "industry": "Artificial Intelligence",
                "stage": "seed",
                "tagline": "Real-time robotics inference acceleration using customized compiler toolchains.",
                "website_url": "https://neuralflow.example.msgi.edu",
                "seeking_mentors": True,
                "seeking_talent": True,
                "is_verified": True,
                "created_at": "2026-08-01T00:00:00Z",
            },
            {
                "id": "start-agri-002",
                "name": "VerdantSense Systems",
                "founder_id": "user-ananya-002",
                "founder_name": "Ananya Sharma",
                "industry": "CleanTech / AgTech",
                "stage": "early",
                "tagline": "Precision satellite soil telemetry for regenerative farming collectives.",
                "website_url": "https://verdantsense.example.msgi.edu",
                "seeking_mentors": True,
                "seeking_talent": False,
                "is_verified": True,
                "created_at": "2026-09-01T00:00:00Z",
            },
        ]
    results = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            results.append({
                "id": row["startup_id"],
                "name": row["name"],
                "founder_id": row["founder_id"],
                "founder_name": row["founder_name"],
                "industry": row["industry"],
                "stage": row["stage"],
                "tagline": row["tagline"],
                "website_url": row.get("website_url"),
                "seeking_mentors": row.get("seeking_mentors", "").strip().lower() == "true",
                "seeking_talent": row.get("seeking_talent", "").strip().lower() == "true",
                "is_verified": row.get("is_verified", "").strip().lower() == "true",
                "created_at": row["created_at"],
            })
    return results


_STARTUPS_STORE: List[Dict[str, Any]] = _load_all_startups()

_STARTUP_CONNECTIONS_STORE: List[Dict[str, Any]] = []


def list_startups(industry: Optional[str] = None, stage: Optional[str] = None) -> List[StartupItem]:
    res: List[StartupItem] = []
    for s in _STARTUPS_STORE:
        if industry and industry.lower() != s["industry"].lower():
            continue
        if stage and stage.lower() != s["stage"].lower():
            continue
        res.append(StartupItem(**s))
    return res


def get_startup_by_id(startup_id: str) -> StartupItem:
    s = next((x for x in _STARTUPS_STORE if x["id"] == startup_id), None)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "STARTUP_NOT_FOUND", "message": f"Startup '{startup_id}' not found."},
        )
    return StartupItem(**s)


def create_startup_connection(
    startup_id: str,
    intent: str,
    message: str,
    user: AuthenticatedUser,
) -> StartupConnectionItem:
    s = get_startup_by_id(startup_id)
    existing = next((c for c in _STARTUP_CONNECTIONS_STORE if c["startup_id"] == startup_id and c["user_id"] == user.id), None)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_CONNECTION_REQUEST", "message": "You have already requested an introduction to this startup."},
        )

    conn_id = f"conn-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": conn_id,
        "startup_id": startup_id,
        "startup_name": s.name,
        "user_id": user.id,
        "intent": intent,
        "message": message,
        "status": "pending",
        "created_at": now_iso,
    }
    _STARTUP_CONNECTIONS_STORE.append(record)

    # Notify founder
    create_notification(
        user_id=s.founder_id,
        event_type="startup_connection_requested",
        entity_id=startup_id,
        title="Startup Connection Request",
        message=f"{user.first_name} requested an introduction regarding {intent} for {s.name}.",
        payload={"startup_id": startup_id, "intent": intent},
    )

    return StartupConnectionItem(**record)


# -----------------------------------------------------------------------------
# MODULE 11: GIVING AND SOCIAL IMPACT (VOLUNTEERING ONLY — NO LIVE PAYMENTS)
# -----------------------------------------------------------------------------

class ImpactProgrammeItem(BaseModel):
    id: str
    title: str
    description: str
    coordinator_name: str
    programme_type: str
    target_volunteers: int
    current_volunteers: int
    is_active: bool
    created_at: str
    is_registered: bool = False


class VolunteerInterestItem(BaseModel):
    id: str
    programme_id: str
    programme_title: str
    user_id: str
    interest_note: str
    status: str
    created_at: str


def _load_all_impact_programmes() -> List[Dict[str, Any]]:
    csv_file = _SEED_DIR / "impact_programmes.csv"
    if not csv_file.exists():
        return [
            {
                "id": "impact-stem-001",
                "title": "MSGI STEM Youth Outreach & Coding Mentorship",
                "description": "Alumni-led weekend computational thinking and Python workshops for underprivileged high school students.",
                "coordinator_name": "MSGI Community Foundation",
                "programme_type": "volunteering",
                "target_volunteers": 25,
                "current_volunteers": 14,
                "is_active": True,
                "created_at": "2026-08-15T00:00:00Z",
            },
            {
                "id": "impact-sustain-002",
                "title": "Green Campus Solar & Urban Reforestation Drive",
                "description": "Collaborative biodiversity and clean energy auditing drive across institutional campus sites.",
                "coordinator_name": "MSGI Sustainability Office",
                "programme_type": "volunteering",
                "target_volunteers": 50,
                "current_volunteers": 38,
                "is_active": True,
                "created_at": "2026-09-01T00:00:00Z",
            },
        ]
    results = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            results.append({
                "id": row["programme_id"],
                "title": row["title"],
                "description": row["description"],
                "coordinator_name": row["coordinator_name"],
                "programme_type": row["programme_type"],
                "target_volunteers": int(row.get("target_volunteers", 20)),
                "current_volunteers": int(row.get("current_volunteers", 0)),
                "is_active": row.get("is_active", "").strip().lower() == "true",
                "created_at": row["created_at"],
            })
    return results


_IMPACT_PROGRAMMES_STORE: List[Dict[str, Any]] = _load_all_impact_programmes()

_VOLUNTEER_INTERESTS_STORE: List[Dict[str, Any]] = []


def list_impact_programmes(user: Optional[AuthenticatedUser] = None) -> List[ImpactProgrammeItem]:
    user_id = user.id if user else None
    results: List[ImpactProgrammeItem] = []
    for prog in _IMPACT_PROGRAMMES_STORE:
        is_reg = any(v["programme_id"] == prog["id"] and v["user_id"] == user_id for v in _VOLUNTEER_INTERESTS_STORE)
        results.append(ImpactProgrammeItem(**prog, is_registered=is_reg))
    return results


def get_impact_programme(programme_id: str, user: Optional[AuthenticatedUser] = None) -> ImpactProgrammeItem:
    prog = next((p for p in _IMPACT_PROGRAMMES_STORE if p["id"] == programme_id), None)
    if not prog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROGRAMME_NOT_FOUND", "message": f"Impact programme '{programme_id}' not found."},
        )
    user_id = user.id if user else None
    is_reg = any(v["programme_id"] == prog["id"] and v["user_id"] == user_id for v in _VOLUNTEER_INTERESTS_STORE)
    return ImpactProgrammeItem(**prog, is_registered=is_reg)


def register_volunteer_interest(
    programme_id: str,
    interest_note: str,
    user: AuthenticatedUser,
) -> VolunteerInterestItem:
    prog = get_impact_programme(programme_id, user)
    existing = next((v for v in _VOLUNTEER_INTERESTS_STORE if v["programme_id"] == programme_id and v["user_id"] == user.id), None)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "DUPLICATE_VOLUNTEER_REGISTRATION", "message": "You have already registered interest for this programme."},
        )

    vol_id = f"vol-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": vol_id,
        "programme_id": programme_id,
        "programme_title": prog.title,
        "user_id": user.id,
        "interest_note": interest_note,
        "status": "registered",
        "created_at": now_iso,
    }
    _VOLUNTEER_INTERESTS_STORE.append(record)

    # Increment volunteer count
    raw_prog = next((p for p in _IMPACT_PROGRAMMES_STORE if p["id"] == programme_id), None)
    if raw_prog:
        raw_prog["current_volunteers"] += 1

    create_notification(
        user_id=user.id,
        event_type="volunteering_registered",
        entity_id=programme_id,
        title="Volunteering Confirmed",
        message=f"You successfully registered interest for {prog.title}.",
        payload={"programme_id": programme_id},
    )

    return VolunteerInterestItem(**record)
