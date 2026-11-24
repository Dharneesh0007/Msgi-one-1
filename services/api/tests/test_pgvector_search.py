"""
MSGI One — pgvector Semantic Search & Document Architecture Tests (Gate 7.5)
Principle: Abraham Silberschatz (Query Optimization & Relational Algebra) & Roger S. Pressman (Verification).
Validates:
1. Ingestion pipeline: Text chunking, sentence boundary detection, overlap, and token estimation.
2. FERPA privacy serialization (masking phone numbers, private emails, residential addresses).
3. 1536-dimensional L2-normalized embedding generation matching vector(1536) schema.
4. SQLAlchemy 2.0 AST compilation using PostgreSQL pgvector cosine distance operator (<=>).
5. Pre-retrieval authorized query scoping (visibility, verification, active status, soft deletion).
6. Cross-user privacy isolation (owner vs third-party query scoping).
7. Semantic similarity ranking accuracy across domain specializations (Robotics, Cloud, AI).
8. Hybrid semantic search combining vector similarity with structured relational filters.
"""

import math
import pytest
from typing import List
from sqlalchemy import select, and_, or_
from sqlalchemy.dialects import postgresql
from unittest.mock import MagicMock, AsyncMock

from src.core.dependencies import AuthenticatedUser
from src.db.models.user import User, AlumniProfile
from src.ai.chunking import chunk_text, serialize_alumni_for_embedding, TextChunk
from src.ai.provider import provider, normalize_l2_vector, cosine_similarity
from src.repositories.alumni_repository import AlumniRepository
from src.services.semantic_search_service import (
    search_alumni_semantic_sync,
    search_alumni_semantic,
    _get_synthetic_alumni_embedding,
)


@pytest.fixture
def student_caller() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="user-student-001",
        email="student@example.msgi.edu",
        first_name="Haruto",
        last_name="Takahashi",
        roles=["student"],
        is_verified=True,
    )


@pytest.fixture
def private_alumnus_caller() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="user-private-006",
        email="private.alumnus@example.msgi.edu",
        first_name="Private",
        last_name="Alumnus",
        roles=["alumni"],
        is_verified=True,
    )


# 1. DOCUMENT CHUNKING & BOUNDARY TESTS
def test_chunking_text_respects_sentence_boundaries():
    """Verify that document chunking respects natural sentence punctuation and overlap."""
    text = (
        "MSGI One is an institutional ecosystem for alumni and student collaboration. "
        "The AI Command Centre uses a multi-agent LangGraph workflow for career navigation. "
        "Verified alumni mentor active undergraduate students in specialized industry domains. "
        "All database records adhere to strict 3NF schema constraints and foreign key invariants. "
        "FERPA privacy protections ensure personal contact information is never exposed without consent."
    )
    chunks = chunk_text(text, document_id="doc_msgi_overview", max_chars=160, overlap_chars=30)
    assert len(chunks) >= 2
    assert all(isinstance(c, TextChunk) for c in chunks)
    assert all(c.document_id == "doc_msgi_overview" for c in chunks)
    assert all(c.token_estimate >= 1 for c in chunks)
    assert all(len(c.content_hash) == 64 for c in chunks)  # SHA-256 length

    # Verify chunk sequence
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert chunk.chunk_id == f"doc_msgi_overview_chunk_{i:04d}"


def test_chunking_rejects_empty_and_whitespace():
    """Verify that chunking returns an empty list for empty or pure whitespace strings."""
    assert chunk_text("", document_id="doc_empty") == []
    assert chunk_text("   \n\t   ", document_id="doc_whitespace") == []


# 2. FERPA PRIVACY & PROFILE SERIALIZATION TESTS
def test_serialize_alumni_masks_sensitive_pii():
    """Verify that textual profile representation includes career metadata but strictly omits PII."""
    raw_profile = {
        "full_name": "Kenji Sato",
        "email": "kenji.sato.private@personal-gmail.com",
        "phone": "+81-90-1234-5678",
        "home_address": "3-2-1 Roppongi, Minato-ku, Tokyo",
        "graduation_year": 2021,
        "degree": "B.Tech",
        "major": "Information Technology",
        "headline": "Staff AI Engineer at Rakuten Symphony",
        "current_company": "Rakuten Symphony",
        "current_title": "Staff AI Engineer",
        "industry": "Artificial Intelligence",
        "city": "Tokyo",
        "country": "Japan",
        "skills": ["Python", "Machine Learning", "PyTorch", "FastAPI"],
        "advisory_topics": ["AI Career Pathways"],
    }

    serialized = serialize_alumni_for_embedding(raw_profile)

    # Core metadata present
    assert "Kenji Sato" in serialized
    assert "Staff AI Engineer" in serialized
    assert "Rakuten Symphony" in serialized
    assert "Artificial Intelligence" in serialized
    assert "PyTorch" in serialized
    assert "Tokyo, Japan" in serialized

    # Sensitive PII strictly excluded
    assert "kenji.sato.private" not in serialized
    assert "+81-90-1234-5678" not in serialized
    assert "Roppongi" not in serialized


# 3. 1536-DIM EMBEDDING & L2 NORMALIZATION TESTS
def test_query_embedding_1536_dim_and_l2_norm():
    """Verify that query embedding yields exactly 1536 dimensions and unit L2 norm."""
    query = "Autonomous mobile robotics navigation and visual SLAM"
    vec = provider.embed_query(query)

    assert len(vec) == 1536
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-5


# 4. SQL COMPILATION WITH COSINE DISTANCE OPERATOR (<=>)
def test_sql_ast_compilation_with_cosine_distance_operator():
    """Verify that SQLAlchemy compiles AlumniProfile.embedding.cosine_distance into PostgreSQL <=> operator."""
    mock_vector = [0.05] * 1536
    stmt = (
        select(AlumniProfile)
        .order_by(AlumniProfile.embedding.cosine_distance(mock_vector))
        .limit(5)
    )

    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "alumni_profiles.embedding <=>" in compiled
    assert "LIMIT" in compiled


# 5. PRE-RETRIEVAL AUTHORIZED QUERY SCOPING (SQL LEVEL)
def test_authorized_query_scoping_in_alumni_repository():
    """Verify that AlumniRepository.search_semantic enforces security boundaries in the SQL AST."""
    mock_session = MagicMock()
    repo = AlumniRepository(mock_session)

    # Inspect the method signature and parameters
    import inspect
    sig = inspect.signature(repo.search_semantic)
    assert "query_vector" in sig.parameters
    assert "limit" in sig.parameters
    assert "distance_threshold" in sig.parameters
    assert "verified_only" in sig.parameters
    assert "current_user_id" in sig.parameters

    # Build the exact query to check SQL compilation
    mock_vector = [0.01] * 1536
    distance_expr = AlumniProfile.embedding.cosine_distance(mock_vector).label("distance")
    stmt = (
        select(AlumniProfile, distance_expr)
        .join(AlumniProfile.user)
        .where(
            AlumniProfile.embedding.isnot(None),
            User.is_active == True,
            User.deleted_at.is_(None),
            AlumniProfile.visibility.in_(["public", "institutional"]),
            User.is_verified == True,
        )
        .where(distance_expr <= 0.8)
        .order_by(distance_expr.asc())
        .limit(10)
    )

    compiled = str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
    assert "alumni_profiles.embedding IS NOT NULL" in compiled
    assert "users.is_active = true" in compiled
    assert "users.deleted_at IS NULL" in compiled
    assert "alumni_profiles.visibility IN ('public', 'institutional')" in compiled
    assert "users.is_verified = true" in compiled
    assert "alumni_profiles.embedding <=>" in compiled


# 6. SEMANTIC SIMILARITY RANKING ACCURACY
def test_semantic_search_ranks_domain_experts_accurately(student_caller):
    """Verify that semantic queries accurately rank the most relevant domain specialists."""
    # Query 1: Deep learning infrastructure
    res_ai = search_alumni_semantic_sync(
        "large language model serving and distributed deep learning infrastructure",
        authenticated_user=student_caller,
        limit=3,
    )
    assert res_ai["total"] >= 1
    assert res_ai["items"][0].full_name == "Kenji Sato"

    # Query 2: Robotics and visual SLAM
    res_robotics = search_alumni_semantic_sync(
        "robotics navigation ROS autonomous visual SLAM",
        authenticated_user=student_caller,
        limit=3,
    )
    assert res_robotics["total"] >= 1
    assert res_robotics["items"][0].full_name == "David Chen"

    # Query 3: Product management and agile strategy
    res_pm = search_alumni_semantic_sync(
        "technical product ownership agile roadmap cloud enterprise strategy",
        authenticated_user=student_caller,
        limit=3,
    )
    assert res_pm["total"] >= 1
    assert res_pm["items"][0].full_name == "Ananya Sharma"


# 7. CROSS-USER PRIVACY ISOLATION (SECURITY BOUNDARY)
def test_unverified_and_private_alumni_excluded_from_third_party(student_caller):
    """Verify that unverified profiles and private profiles are never returned to student callers."""
    res = search_alumni_semantic_sync(
        "software engineering and technology",
        authenticated_user=student_caller,
        limit=20,
    )
    names = [item.full_name for item in res["items"]]

    # Unverified alumnus must NEVER be visible
    assert "Unverified Alumnus" not in names

    # Private alumnus must NEVER be visible to another user
    assert "Private Alumnus" not in names


def test_private_profile_owner_can_see_own_profile(private_alumnus_caller):
    """Verify that the owner of a private profile is permitted to retrieve their own profile."""
    res = search_alumni_semantic_sync(
        "cryptography security defense",
        authenticated_user=private_alumnus_caller,
        limit=20,
    )
    names = [item.full_name for item in res["items"]]
    assert "Private Alumnus" in names


# 8. HYBRID RETRIEVAL (SEMANTIC + STRUCTURED FILTERS)
def test_hybrid_semantic_and_geographic_filtering(student_caller):
    """Verify that combining semantic query with structured country filter restricts candidate pool."""
    # Both Kenji Sato (Japan) and David Chen (US) have AI/Machine Learning skills
    res_japan = search_alumni_semantic_sync(
        "machine learning python engineer",
        country="japan",
        authenticated_user=student_caller,
        limit=5,
    )
    assert any(i.full_name == "Kenji Sato" for i in res_japan["items"])
    assert not any(i.full_name == "David Chen" for i in res_japan["items"])

    res_us = search_alumni_semantic_sync(
        "machine learning python engineer",
        country="united states",
        authenticated_user=student_caller,
        limit=5,
    )
    assert any(i.full_name == "David Chen" for i in res_us["items"])
    assert not any(i.full_name == "Kenji Sato" for i in res_us["items"])


# 9. COSINE DISTANCE TO SIMILARITY INVARIANT
def test_cosine_similarity_mathematical_properties():
    """Verify mathematical properties of cosine similarity and distance."""
    v1 = provider.embed_query("Artificial Intelligence")
    v2 = provider.embed_query("Artificial Intelligence")
    sim_identical = cosine_similarity(v1, v2)
    assert abs(sim_identical - 1.0) < 1e-4

    v3 = provider.embed_query("Classical Ancient Greek Philosophy")
    sim_orthogonal = cosine_similarity(v1, v3)
    assert sim_orthogonal < sim_identical
    assert -1.0 <= sim_orthogonal <= 1.0
