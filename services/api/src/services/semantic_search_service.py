"""
MSGI One — Semantic Vector Search Service
Principle: Martin Fowler (Domain Services) & C.J. Date (Relational Theory).
Executes semantic similarity search on alumni profiles using 1536-dim embeddings.
Supports both real PostgreSQL pgvector execution and deterministic synthetic vector ranking.
"""

from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import AuthenticatedUser
from src.schemas.business import AlumniDirectoryItem
from src.ai.provider import provider, cosine_similarity
from src.ai.chunking import serialize_alumni_for_embedding
from src.services.alumni_service import _SYNTHETIC_ALUMNI_STORE
from src.repositories.alumni_repository import AlumniRepository


# Cache of synthetic embeddings for offline/testing mode
_SYNTHETIC_EMBEDDINGS_CACHE: Dict[str, List[float]] = {}


def _get_synthetic_alumni_embedding(alumni_item: Dict[str, Any]) -> List[float]:
    """Retrieve or compute 1536-dim embedding for synthetic alumni record."""
    item_id = alumni_item["id"]
    if item_id not in _SYNTHETIC_EMBEDDINGS_CACHE:
        text_repr = serialize_alumni_for_embedding(alumni_item)
        vec = provider.embed_query(text_repr)
        _SYNTHETIC_EMBEDDINGS_CACHE[item_id] = vec
    return _SYNTHETIC_EMBEDDINGS_CACHE[item_id]


def search_alumni_semantic_sync(
    query_text: str,
    authenticated_user: Optional[AuthenticatedUser] = None,
    limit: int = 10,
    distance_threshold: float = 0.9,
    department: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    verified_only: bool = True,
) -> Dict[str, Any]:
    """
    Synchronous vector similarity search against synthetic/cached alumni profiles.
    Used by LangGraph nodes and offline evaluation harnesses.
    """
    cleaned_query = (query_text or "").strip()
    if not cleaned_query:
        return {
            "items": [],
            "total": 0,
            "query": "",
            "embedding_model": provider.embedding_model,
            "dimensions": provider.embedding_dimensions,
        }

    query_vector = provider.embed_query(cleaned_query)
    user_id = authenticated_user.id if authenticated_user else None

    scored_candidates: List[Tuple[Dict[str, Any], float]] = []

    for item in _SYNTHETIC_ALUMNI_STORE:
        # Pre-retrieval authorization scoping
        is_owner = (user_id is not None and user_id == item["user_id"])
        if not item.get("is_profile_public", True) and not is_owner:
            continue

        if verified_only and not item.get("is_verified", False):
            continue

        # Structured filters
        if department and department.lower() not in item.get("major", "").lower():
            continue
        if industry and industry.lower() not in item.get("industry", "").lower():
            continue
        if country and country.lower() not in item.get("country", "").lower():
            continue

        # Cosine similarity calculation
        doc_vector = _get_synthetic_alumni_embedding(item)
        sim = cosine_similarity(query_vector, doc_vector)
        distance = 1.0 - sim

        if distance <= distance_threshold:
            scored_candidates.append((item, round(sim, 4)))

    # Sort descending by similarity
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    selected = scored_candidates[:limit]

    output_items: List[AlumniDirectoryItem] = []
    for item, sim in selected:
        output_items.append(
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

    return {
        "items": output_items,
        "total": len(output_items),
        "query": cleaned_query,
        "embedding_model": provider.embedding_model,
        "dimensions": provider.embedding_dimensions,
        "execution_mode": "synthetic_vector_cache",
    }


async def search_alumni_semantic(
    query_text: str,
    authenticated_user: Optional[AuthenticatedUser] = None,
    limit: int = 10,
    distance_threshold: float = 0.9,
    department: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    verified_only: bool = True,
    session: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """
    Asynchronous vector similarity search.
    Delegates to PostgreSQL pgvector via AlumniRepository if session is present,
    otherwise falls back to search_alumni_semantic_sync.
    """
    if session is None:
        return search_alumni_semantic_sync(
            query_text=query_text,
            authenticated_user=authenticated_user,
            limit=limit,
            distance_threshold=distance_threshold,
            department=department,
            industry=industry,
            country=country,
            verified_only=verified_only,
        )

    cleaned_query = (query_text or "").strip()
    if not cleaned_query:
        return {
            "items": [],
            "total": 0,
            "query": "",
            "embedding_model": provider.embedding_model,
            "dimensions": provider.embedding_dimensions,
        }

    query_vector = provider.embed_query(cleaned_query)
    user_id = authenticated_user.id if authenticated_user else None

    repo = AlumniRepository(session)
    db_results = await repo.search_semantic(
        query_vector=query_vector,
        limit=limit,
        distance_threshold=distance_threshold,
        department=department,
        industry=industry,
        country=country,
        verified_only=verified_only,
        current_user_id=user_id,
    )

    items: List[AlumniDirectoryItem] = []
    for profile, similarity in db_results:
        user = profile.user
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Verified Alumnus"
        items.append(
            AlumniDirectoryItem(
                id=profile.id,
                user_id=profile.user_id,
                full_name=full_name,
                avatar_url=user.avatar_url,
                graduation_year=profile.graduation_year,
                degree=profile.degree,
                major=profile.major,
                headline=profile.headline,
                current_company=profile.current_company,
                current_title=profile.current_title,
                industry=profile.industry,
                country=None,
                city=None,
                skills=[],
                is_verified=user.is_verified,
                mentor_opt_in=False,
            )
        )

    return {
        "items": items,
        "total": len(items),
        "query": cleaned_query,
        "embedding_model": provider.embedding_model,
        "dimensions": provider.embedding_dimensions,
        "execution_mode": "postgres_pgvector",
    }
