"""
MSGI One — Alumni Discovery Domain Service
Implements: Search, filtering, privacy masking (FERPA/GDPR compliance).
Provides Phase 3 Tool Contract: search_alumni(filters, authenticated_user)
"""

from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import AlumniDirectoryItem, AlumniDetailResponse

# In-memory development repository populated with synthetic seed data
_SYNTHETIC_ALUMNI_STORE: List[Dict[str, Any]] = [
    {
        "id": "alumni-kenji-sato",
        "user_id": "user-kenji-001",
        "full_name": "Kenji Sato",
        "avatar_url": None,
        "graduation_year": 2021,
        "degree": "B.Tech",
        "major": "Information Technology",
        "headline": "Staff AI Engineer at Rakuten Symphony",
        "current_company": "Rakuten Symphony",
        "current_title": "Staff AI Engineer",
        "industry": "Artificial Intelligence",
        "country": "Japan",
        "city": "Tokyo",
        "skills": ["Python", "Machine Learning", "PyTorch", "FastAPI", "Distributed Systems"],
        "is_verified": True,
        "mentor_opt_in": True,
        "is_profile_public": True,
        "bio": "Specialising in distributed deep learning infrastructure and large language model serving.",
        "advisory_topics": ["AI Career Pathways", "Transitioning to Industry in Japan", "Graduate Studies"],
    },
    {
        "id": "alumni-ananya-sharma",
        "user_id": "user-ananya-002",
        "full_name": "Ananya Sharma",
        "avatar_url": None,
        "graduation_year": 2019,
        "degree": "B.Tech",
        "major": "Computer Science",
        "headline": "Senior Product Manager at Microsoft",
        "current_company": "Microsoft",
        "current_title": "Senior Product Manager",
        "industry": "Cloud Computing",
        "country": "India",
        "city": "Bengaluru",
        "skills": ["Product Strategy", "Cloud Architecture", "Azure", "AI Ops", "Agile"],
        "is_verified": True,
        "mentor_opt_in": True,
        "is_profile_public": True,
        "bio": "Guiding next-generation engineers in transitioning from code to technical product ownership.",
        "advisory_topics": ["Product Management", "Enterprise Cloud Strategy", "Resume Review"],
    },
    {
        "id": "alumni-david-chen",
        "user_id": "user-david-003",
        "full_name": "David Chen",
        "avatar_url": None,
        "graduation_year": 2022,
        "degree": "B.Tech",
        "major": "Information Technology",
        "headline": "Founding Robotics Engineer at Stealth Robotics",
        "current_company": "Stealth Robotics",
        "current_title": "Robotics Engineer",
        "industry": "Artificial Intelligence",
        "country": "United States",
        "city": "San Francisco",
        "skills": ["Python", "ROS 2", "Embedded C++", "Computer Vision", "Machine Learning"],
        "is_verified": True,
        "mentor_opt_in": False,
        "is_profile_public": True,
        "bio": "Autonomous mobile robotics navigation and visual SLAM pipeline developer.",
        "advisory_topics": [],
    },
    {
        "id": "alumni-yuki-tanaka",
        "user_id": "user-yuki-004",
        "full_name": "Yuki Tanaka",
        "avatar_url": None,
        "graduation_year": 2020,
        "degree": "B.Tech",
        "major": "Information Technology",
        "headline": "Full-Stack Tech Lead at Mercari",
        "current_company": "Mercari",
        "current_title": "Tech Lead",
        "industry": "E-Commerce",
        "country": "Japan",
        "city": "Tokyo",
        "skills": ["Go", "TypeScript", "Microservices", "GCP", "Kubernetes"],
        "is_verified": True,
        "mentor_opt_in": True,
        "is_profile_public": True,
        "bio": "High-throughput marketplace architectures and backend developer enablement.",
        "advisory_topics": ["Backend Engineering in Tokyo", "Microservices Patterns"],
    },
    {
        "id": "alumni-unverified-test",
        "user_id": "user-unverified-005",
        "full_name": "Unverified Alumnus",
        "avatar_url": None,
        "graduation_year": 2023,
        "degree": "B.Tech",
        "major": "Information Technology",
        "headline": "Software Intern",
        "current_company": "Startup",
        "current_title": "Intern",
        "industry": "Technology",
        "country": "India",
        "city": "Chennai",
        "skills": ["Java"],
        "is_verified": False,
        "mentor_opt_in": False,
        "is_profile_public": True,
    },
    {
        "id": "alumni-private-test",
        "user_id": "user-private-006",
        "full_name": "Private Alumnus",
        "avatar_url": None,
        "graduation_year": 2018,
        "degree": "B.Tech",
        "major": "Information Technology",
        "headline": "Confidential Staff",
        "current_company": "Defense Tech",
        "current_title": "Researcher",
        "industry": "Security",
        "country": "Japan",
        "city": "Tokyo",
        "skills": ["Cryptography"],
        "is_verified": True,
        "mentor_opt_in": False,
        "is_profile_public": False,  # Opted out of public directory
    },
]


def search_alumni(
    filters: Dict[str, Any],
    authenticated_user: AuthenticatedUser,
) -> Dict[str, Any]:
    """
    Core Domain Service & Phase 3 Tool Contract.
    Searches alumni directory using deterministic multi-parameter filtering,
    privacy enforcement, and pagination.
    """
    query = (filters.get("query") or "").strip().lower()
    department = (filters.get("department") or "").strip().lower()
    industry = (filters.get("industry") or "").strip().lower()
    country = (filters.get("country") or "").strip().lower()
    skill = (filters.get("skill") or "").strip().lower()
    graduation_year = filters.get("graduation_year")
    verified_only = filters.get("verified_only", True)
    page = max(1, int(filters.get("page", 1)))
    limit = min(50, max(1, int(filters.get("limit", 20))))

    filtered: List[AlumniDirectoryItem] = []

    for item in _SYNTHETIC_ALUMNI_STORE:
        # Privacy guard: Hide profiles that have opted out of public directory
        if not item.get("is_profile_public", True):
            continue

        # Verification check
        if verified_only and not item.get("is_verified", False):
            continue

        # Free-text search
        if query:
            searchable = f"{item['full_name']} {item.get('headline', '')} {item.get('current_company', '')} {' '.join(item.get('skills', []))}".lower()
            if query not in searchable:
                continue

        # Structured filters
        if department and department not in item.get("major", "").lower():
            continue

        if industry and industry not in item.get("industry", "").lower():
            continue

        if country and country not in item.get("country", "").lower():
            continue

        if graduation_year and int(graduation_year) != item.get("graduation_year"):
            continue

        if skill:
            has_skill = any(skill in s.lower() for s in item.get("skills", []))
            if not has_skill:
                continue

        # Return privacy-masked DTO (no emails, phone numbers, or exact residential coordinates)
        filtered.append(
            AlumniDirectoryItem(
                id=item["id"],
                user_id=item["user_id"],
                full_name=item["full_name"],
                avatar_url=item.get("avatar_url"),
                graduation_year=item["graduation_year"],
                degree=item["degree"],
                major=item["major"],
                headline=item.get("headline"),
                current_company=item.get("current_company"),
                current_title=item.get("current_title"),
                industry=item.get("industry"),
                country=item.get("country"),
                city=item.get("city"),
                skills=item.get("skills", []),
                is_verified=item.get("is_verified", False),
                mentor_opt_in=item.get("mentor_opt_in", False),
            )
        )

    total_records = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_items = filtered[start_idx:end_idx]

    return {
        "items": paginated_items,
        "total": total_records,
        "page": page,
        "limit": limit,
        "total_pages": (total_records + limit - 1) // limit if total_records > 0 else 0,
    }


def get_alumni_by_id(
    alumni_id: str,
    authenticated_user: AuthenticatedUser,
) -> AlumniDetailResponse:
    """Retrieve individual alumni profile with public details."""
    match = next((item for item in _SYNTHETIC_ALUMNI_STORE if item["id"] == alumni_id), None)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ENTITY_NOT_FOUND", "message": f"Alumni with ID '{alumni_id}' was not found."},
        )

    if not match.get("is_profile_public", True) and authenticated_user.id != match["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PROFILE_PRIVATE", "message": "This alumni profile is private."},
        )

    return AlumniDetailResponse(
        id=match["id"],
        user_id=match["user_id"],
        full_name=match["full_name"],
        avatar_url=match.get("avatar_url"),
        graduation_year=match["graduation_year"],
        degree=match["degree"],
        major=match["major"],
        headline=match.get("headline"),
        current_company=match.get("current_company"),
        current_title=match.get("current_title"),
        industry=match.get("industry"),
        country=match.get("country"),
        city=match.get("city"),
        skills=match.get("skills", []),
        is_verified=match.get("is_verified", False),
        mentor_opt_in=match.get("mentor_opt_in", False),
        bio=match.get("bio"),
        advisory_topics=match.get("advisory_topics", []),
    )
