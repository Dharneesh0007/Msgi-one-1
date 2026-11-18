"""
MSGI One — Alumni Network API Router
Endpoints: GET /api/v1/alumni, GET /api/v1/alumni/search, GET /api/v1/alumni/{id}
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.business import AlumniDirectoryItem, AlumniDetailResponse
from src.services.alumni_service import search_alumni, get_alumni_by_id

router = APIRouter(prefix="/alumni", tags=["Alumni Network"])


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
    country: Optional[str] = Query(None, description="Country filter"),
    skill: Optional[str] = Query(None, description="Skill filter"),
    graduation_year: Optional[int] = Query(None, description="Graduation year filter"),
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
        "skill": skill,
        "graduation_year": graduation_year,
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
