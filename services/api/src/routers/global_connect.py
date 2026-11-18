"""
MSGI One — Global Alumni Connect API Router (P1)
Endpoints: GET /api/v1/global/locations, GET /api/v1/global/chapters
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.schemas.user import StandardEnvelope
from src.schemas.business import LocationAggregationItem, ChapterResponse
from src.services.global_service import get_aggregated_locations, get_chapters

router = APIRouter(prefix="/global", tags=["Global Alumni Connect"])


@router.get(
    "/locations",
    response_model=StandardEnvelope[List[LocationAggregationItem]],
    summary="Get Aggregated Alumni Locations",
    description="Returns city and country distribution of consented alumni. Suppresses small counts (< 3) to protect privacy.",
)
def list_locations(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[LocationAggregationItem]]:
    locations = get_aggregated_locations(authenticated_user=current_user)
    return StandardEnvelope(
        status="success",
        data=locations,
        error=None,
        meta={"total": len(locations)},
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/chapters",
    response_model=StandardEnvelope[List[ChapterResponse]],
    summary="List Institutional Alumni Chapters",
)
def list_chapters(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StandardEnvelope[List[ChapterResponse]]:
    chapters = get_chapters()
    return StandardEnvelope(
        status="success",
        data=chapters,
        error=None,
        meta={"total": len(chapters)},
        timestamp=datetime.now(timezone.utc),
    )
