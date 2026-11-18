"""
MSGI One — Global Alumni Connect Unit Tests (P1)
Tests: Regional aggregation, privacy threshold suppression (k-anonymity >= 3),
       chapter registry.
"""

import pytest
from src.core.dependencies import AuthenticatedUser
from src.services.global_service import get_aggregated_locations, get_chapters


@pytest.fixture
def member_user():
    return AuthenticatedUser(
        id="member-global-001",
        email="member.global@example.msgi.edu",
        first_name="Daiki",
        last_name="Ito",
        roles=["student"],
        is_verified=True,
    )


def test_locations_aggregation_and_privacy_suppression(member_user):
    """Regional locations with count >= 3 appear; small counts (< 3) are suppressed."""
    locations = get_aggregated_locations(member_user)
    assert len(locations) >= 2

    cities = [loc.city for loc in locations]
    assert "Tokyo" in cities
    assert "Bengaluru" in cities
    assert "San Francisco" in cities

    # 'Kyoto' had count 1, so it must be suppressed for privacy
    assert "Kyoto" not in cities

    for loc in locations:
        assert loc.alumni_count >= 3


def test_chapters_list_returns_active_chapters(member_user):
    """Chapters list returns institutional chapters with lead alumni."""
    chapters = get_chapters()
    assert len(chapters) >= 3
    chapter_cities = [c.city for c in chapters]
    assert "Tokyo" in chapter_cities
    assert "Bengaluru" in chapter_cities
    assert "San Francisco" in chapter_cities
