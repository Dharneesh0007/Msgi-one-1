"""
MSGI One — Learning Academy Domain Service (Module 9)
Manages course catalog, student enrollments, and progress tracking.
Principles: Evans Domain Aggregates & Silberschatz Invariant Enforcement.
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


class LearningResourceItem(BaseModel):
    resource_id: str
    title: str
    provider: str
    target_skill: str
    difficulty: str
    duration_hours: float
    url: str
    rating: float


class CourseEnrollmentItem(BaseModel):
    id: str
    user_id: str
    resource_id: str
    course_title: str
    progress_percentage: int
    status: str  # 'enrolled', 'in_progress', 'completed', 'dropped'
    enrolled_at: str
    completed_at: Optional[str] = None
    updated_at: str


# In-memory store for course enrollments (conforming to public.course_enrollments)
_ENROLLMENTS_STORE: List[Dict[str, Any]] = [
    {
        "id": "enr-seed-001",
        "user_id": "user-student-001",
        "resource_id": "res-py-001",
        "course_title": "Mastering Modern Python 3.12",
        "progress_percentage": 45,
        "status": "in_progress",
        "enrolled_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
]


def _load_all_resources() -> List[LearningResourceItem]:
    csv_file = _SEED_DIR / "learning_resources.csv"
    if not csv_file.exists():
        return []
    items: List[LearningResourceItem] = []
    with open(csv_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(LearningResourceItem(
                resource_id=row["resource_id"],
                title=row["title"],
                provider=row["provider"],
                target_skill=row["target_skill"],
                difficulty=row["difficulty"],
                duration_hours=float(row.get("duration_hours", 0)),
                url=row["url"],
                rating=float(row.get("rating", 4.5)),
            ))
    return items


def list_learning_resources(
    skill: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> List[LearningResourceItem]:
    resources = _load_all_resources()
    if skill:
        s_lower = skill.strip().lower()
        resources = [r for r in resources if s_lower in r.target_skill.lower() or s_lower in r.title.lower()]
    if difficulty:
        d_lower = difficulty.strip().lower()
        resources = [r for r in resources if r.difficulty.lower() == d_lower]
    return resources


def get_learning_resource(resource_id: str) -> LearningResourceItem:
    resources = _load_all_resources()
    res = next((r for r in resources if r.resource_id == resource_id), None)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESOURCE_NOT_FOUND", "message": f"Learning resource '{resource_id}' does not exist."},
        )
    return res


def enroll_in_course(resource_id: str, user: AuthenticatedUser) -> CourseEnrollmentItem:
    """
    Enrolls an authenticated student in an approved learning resource.
    Enforces UNIQUE(user_id, resource_id) to prevent duplicate enrollments.
    """
    resource = get_learning_resource(resource_id)

    # Check for duplicate active enrollment
    for enr in _ENROLLMENTS_STORE:
        if enr["user_id"] == user.id and enr["resource_id"] == resource_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "DUPLICATE_ENROLLMENT", "message": f"You are already enrolled in '{resource.title}'."},
            )

    enr_id = f"enr-{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "id": enr_id,
        "user_id": user.id,
        "resource_id": resource_id,
        "course_title": resource.title,
        "progress_percentage": 0,
        "status": "enrolled",
        "enrolled_at": now_iso,
        "completed_at": None,
        "updated_at": now_iso,
    }
    _ENROLLMENTS_STORE.append(record)

    # Create in-app notification
    create_notification(
        user_id=user.id,
        event_type="course_enrolled",
        entity_id=resource_id,
        title="Course Enrolled",
        message=f"You successfully enrolled in {resource.title}.",
        payload={"resource_id": resource_id, "provider": resource.provider},
    )

    return CourseEnrollmentItem(**record)


def get_my_learning(user: AuthenticatedUser) -> List[CourseEnrollmentItem]:
    user_enrs = [e for e in _ENROLLMENTS_STORE if e["user_id"] == user.id]
    return [CourseEnrollmentItem(**e) for e in user_enrs]


def update_learning_progress(
    enrollment_id: str,
    progress_percentage: int,
    user: AuthenticatedUser,
) -> CourseEnrollmentItem:
    """
    Updates course progress percentage.
    Enforces authorization: Only the enrolled user can modify progress.
    Validates progress boundary: 0 <= progress_percentage <= 100.
    """
    if progress_percentage < 0 or progress_percentage > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PROGRESS", "message": "Progress percentage must be between 0 and 100."},
        )

    enr = next((e for e in _ENROLLMENTS_STORE if e["id"] == enrollment_id), None)
    if not enr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENROLLMENT_NOT_FOUND", "message": f"Enrollment '{enrollment_id}' not found."},
        )

    # Cross-user authorization check
    if enr["user_id"] != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PERMISSION_DENIED", "message": "You cannot alter learning progress for another user."},
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    enr["progress_percentage"] = progress_percentage
    enr["updated_at"] = now_iso

    if progress_percentage == 100:
        enr["status"] = "completed"
        enr["completed_at"] = now_iso
        create_notification(
            user_id=user.id,
            event_type="course_completed",
            entity_id=enr["resource_id"],
            title="Course Milestone Achieved!",
            message=f"Congratulations! You completed {enr['course_title']}.",
            payload={"resource_id": enr["resource_id"]},
        )
    elif progress_percentage > 0:
        enr["status"] = "in_progress"

    return CourseEnrollmentItem(**enr)
