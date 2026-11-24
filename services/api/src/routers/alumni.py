"""
MSGI One — Alumni Network API Router
Endpoints: GET /api/v1/alumni, GET /api/v1/alumni/search, GET /api/v1/alumni/{id}
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from src.core.dependencies import AuthenticatedUser, get_current_user, require_verified_alumni
from src.schemas.user import StandardEnvelope
from src.schemas.business import AlumniDirectoryItem, AlumniDetailResponse
from src.services.alumni_service import search_alumni, get_alumni_by_id, _SYNTHETIC_ALUMNI_STORE

router = APIRouter(prefix="/alumni", tags=["Alumni Network"])


class AlumniProfileSelfUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    headline: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = Field(default=None, max_length=2000)
    current_company: Optional[str] = Field(default=None, max_length=150)
    current_title: Optional[str] = Field(default=None, max_length=150)
    industry: Optional[str] = Field(default=None, max_length=100)
    skills: Optional[List[str]] = None
    advisory_topics: Optional[List[str]] = None
    mentor_opt_in: Optional[bool] = None
    is_profile_public: Optional[bool] = None


@router.get(
    "",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Search Alumni Directory",
    description="Multi-parameter search over alumni profiles with FERPA/GDPR contact masking.",
)
@router.get(
    "/search",
    response_model=StandardEnvelope[Dict[str, Any]],
    summary="Search Alumni Directory (Alias)",
    include_in_schema=False,
)
def list_alumni(
    query: Optional[str] = Query(None, description="Free-text search by name, company, skill"),
    department: Optional[str] = Query(None, description="Department or major filter"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    country: Optional[str] = Query(None, description="Country or city filter"),
    company: Optional[str] = Query(None, description="Organization / company filter"),
    title: Optional[str] = Query(None, description="Job title filter"),
    skill: Optional[str] = Query(None, description="Skill filter"),
    graduation_year: Optional[int] = Query(None, description="Graduation year filter"),
    mentor_opt_in: Optional[bool] = Query(None, description="Filter by mentorship availability"),
    verified_only: bool = Query(True, description="Filter for institutional verified status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[Dict[str, Any]]:
    """Search and filter directory records."""
    filters = {
        "query": query,
        "department": department,
        "industry": industry,
        "country": country,
        "company": company,
        "title": title,
        "skill": skill,
        "graduation_year": graduation_year,
        "mentor_opt_in": mentor_opt_in,
        "verified_only": verified_only,
        "page": page,
        "limit": limit,
    }
    result = search_alumni(filters=filters, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=result,
        error=None,
        meta={"filters": {k: v for k, v in filters.items() if v is not None}},
        timestamp=datetime.now(timezone.utc),
    )


@router.patch(
    "/me",
    response_model=StandardEnvelope[AlumniDetailResponse],
    summary="Update Verified Alumni Professional Profile",
)
def update_my_alumni_profile(
    payload: AlumniProfileSelfUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_verified_alumni),
) -> StandardEnvelope[AlumniDetailResponse]:
    existing = next((a for a in _SYNTHETIC_ALUMNI_STORE if a.get("user_id") == current_user.id), None)
    if existing is None:
        existing = {
            "id": f"alumni-{current_user.id}",
            "user_id": current_user.id,
            "full_name": f"{current_user.first_name or 'Verified'} {current_user.last_name or 'Alumnus'}".strip(),
            "avatar_url": current_user.avatar_url,
            "graduation_year": 2021,
            "degree": "B.Tech",
            "major": "Computer Science",
            "headline": "Verified MSGI Alumnus",
            "current_company": None,
            "current_title": None,
            "industry": "Technology",
            "country": "India",
            "city": "Chennai",
            "skills": [],
            "advisory_topics": [],
            "is_verified": True,
            "mentor_opt_in": False,
            "is_profile_public": True,
            "bio": None,
        }
        _SYNTHETIC_ALUMNI_STORE.append(existing)

    for field, val in payload.model_dump(exclude_none=True).items():
        existing[field] = val

    return StandardEnvelope(
        status="success",
        data=AlumniDetailResponse(**{k: existing.get(k) for k in AlumniDetailResponse.model_fields.keys() if k in existing or k in ("bio", "advisory_topics", "linkedin_slug")}),
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/{alumni_id}",
    response_model=StandardEnvelope[AlumniDetailResponse],
    summary="Get Detailed Alumni Profile",
    description="Retrieves public professional biography, skills, and mentoring topics without private contact info.",
)
def get_alumni(
    alumni_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[AlumniDetailResponse]:
    """Retrieve individual profile by ID."""
    result = get_alumni_by_id(alumni_id=alumni_id, authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=result,
        error=None,
        meta={},
        timestamp=datetime.now(timezone.utc),
    )
