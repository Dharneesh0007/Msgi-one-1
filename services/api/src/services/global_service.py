"""
MSGI One — Global Alumni Connect Domain Service (P1)
Implements: Regional location aggregation, privacy threshold suppression (k-anonymity >= 3),
            and institutional alumni chapters.
"""

from typing import Dict, List, Any
from src.core.dependencies import AuthenticatedUser
from src.schemas.business import LocationAggregationItem, ChapterResponse

# In-memory development store for global chapters
_CHAPTERS_STORE: List[Dict[str, Any]] = [
    {
        "id": "chap-tokyo-001",
        "name": "MSGI Greater Tokyo Alumni Chapter",
        "city": "Tokyo",
        "country": "Japan",
        "region": "Asia-Pacific",
        "lead_alumni_name": "Kenji Sato",
        "description": "Connecting tech alumni, researchers, and entrepreneurs across Kanto.",
        "member_count": 340,
    },
    {
        "id": "chap-bengaluru-002",
        "name": "MSGI Bengaluru Innovation Chapter",
        "city": "Bengaluru",
        "country": "India",
        "region": "South Asia",
        "lead_alumni_name": "Ananya Sharma",
        "description": "Fostering enterprise software leadership and mentorship.",
        "member_count": 620,
    },
    {
        "id": "chap-bay-area-003",
        "name": "MSGI Bay Area Tech Chapter",
        "city": "San Francisco",
        "country": "United States",
        "region": "North America",
        "lead_alumni_name": "David Chen",
        "description": "Connecting alumni across Silicon Valley robotics, AI, and venture.",
        "member_count": 180,
    },
    {
        "id": "chap-london-004",
        "name": "MSGI London Chapter",
        "city": "London",
        "country": "United Kingdom",
        "region": "Europe",
        "lead_alumni_name": "Vikram Seth",
        "description": "Fintech and global business alumni in the UK.",
        "member_count": 95,
    },
]

# Raw consented location records
_CONSENTED_LOCATIONS: List[Dict[str, str]] = [
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Tokyo", "country": "Japan"},
    {"city": "Bengaluru", "country": "India"},
    {"city": "Bengaluru", "country": "India"},
    {"city": "Bengaluru", "country": "India"},
    {"city": "San Francisco", "country": "United States"},
    {"city": "San Francisco", "country": "United States"},
    {"city": "San Francisco", "country": "United States"},
    {"city": "Kyoto", "country": "Japan"}, # Count = 1 (will be suppressed)
]


def get_aggregated_locations(authenticated_user: AuthenticatedUser) -> List[LocationAggregationItem]:
    """
    Retrieves regional alumni distribution.
    Enforces privacy rule: Suppresses locations with count < 3 to prevent individual deanonymization.
    Never exposes exact residential coordinates.
    """
    counts: Dict[str, int] = {}
    for loc in _CONSENTED_LOCATIONS:
        key = f"{loc['country']}:{loc['city']}"
        counts[key] = counts.get(key, 0) + 1

    active_chapter_cities = {f"{c['country']}:{c['city']}" for c in _CHAPTERS_STORE}

    results: List[LocationAggregationItem] = []
    for key, count in counts.items():
        if count < 3:
            # Privacy suppression
            continue
        country, city = key.split(":")
        results.append(
            LocationAggregationItem(
                country=country,
                city=city,
                alumni_count=count,
                is_active_chapter=key in active_chapter_cities,
            )
        )

    results.sort(key=lambda x: x.alumni_count, reverse=True)
    return results


def get_chapters() -> List[ChapterResponse]:
    """Retrieve verified institutional alumni chapters."""
    return [ChapterResponse(**c) for c in _CHAPTERS_STORE]
