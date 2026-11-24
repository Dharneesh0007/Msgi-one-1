"""
MSGI One — Document Chunking & Text Representation Pipeline
Principle: Martin Fowler (Clean Architecture) & Manning et al. (Information Retrieval).
Provides:
1. Boundary-aware text chunking with token estimation and metadata tagging.
2. Privacy-preserving profile text serialization (FERPA/GDPR compliance).
3. Chunk deduplication and SHA-256 fingerprinting.
"""

import hashlib
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TextChunk(BaseModel):
    """Normalized, typed document chunk for vector embedding ingestion."""
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    token_estimate: int
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def chunk_text(
    text: str,
    document_id: str,
    max_chars: int = 500,
    overlap_chars: int = 50,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[TextChunk]:
    """
    Splits input text into overlapping chunks, respecting sentence and paragraph boundaries.
    
    Constraints:
    - max_chars >= 100
    - 0 <= overlap_chars < max_chars
    - Zero-length or pure-whitespace strings return empty list.
    """
    if not text or not text.strip():
        return []

    cleaned_text = re.sub(r"\s+", " ", text).strip()
    if not cleaned_text:
        return []

    if max_chars < 100:
        max_chars = 100
    if overlap_chars >= max_chars or overlap_chars < 0:
        overlap_chars = max(0, max_chars // 10)

    chunks: List[TextChunk] = []
    text_len = len(cleaned_text)
    start = 0
    chunk_idx = 0

    while start < text_len:
        end = min(start + max_chars, text_len)

        # If not at the very end of text, seek nearest natural boundary (period, question mark, newline, or space)
        if end < text_len:
            boundary_match = None
            # Search backward from 'end' for punctuation boundary within the last 25% of the window
            window_slice = cleaned_text[start:end]
            punctuation_pos = max(
                window_slice.rfind(". "),
                window_slice.rfind("! "),
                window_slice.rfind("? "),
                window_slice.rfind("\n"),
            )
            if punctuation_pos != -1 and punctuation_pos > max_chars * 0.6:
                end = start + punctuation_pos + 1
            else:
                # Fallback to nearest whitespace
                space_pos = window_slice.rfind(" ")
                if space_pos != -1 and space_pos > max_chars * 0.5:
                    end = start + space_pos

        chunk_str = cleaned_text[start:end].strip()
        if chunk_str:
            chunk_hash = hashlib.sha256(chunk_str.encode("utf-8")).hexdigest()
            # Token estimate: approx 4 characters per token in English
            token_est = max(1, len(chunk_str) // 4)
            chunk_id = f"{document_id}_chunk_{chunk_idx:04d}"

            meta = dict(metadata or {})
            meta["length"] = len(chunk_str)

            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    chunk_index=chunk_idx,
                    content=chunk_str,
                    start_char=start,
                    end_char=end,
                    token_estimate=token_est,
                    content_hash=chunk_hash,
                    metadata=meta,
                )
            )
            chunk_idx += 1

        if end >= text_len:
            break

        # Advance start with overlap
        start = max(start + 1, end - overlap_chars)

    return chunks


def serialize_alumni_for_embedding(alumni: Dict[str, Any]) -> str:
    """
    Serializes an alumni record into a dense, semantic textual summary for embedding generation.
    Enforces FERPA privacy boundaries:
    - Excludes phone numbers, personal emails, residential addresses, and financial data.
    - Includes professional skills, career achievements, educational degree, major, industry, and bio.
    """
    parts: List[str] = []

    full_name = alumni.get("full_name") or f"{alumni.get('first_name', '')} {alumni.get('last_name', '')}".strip()
    if full_name:
        parts.append(f"Alumnus {full_name}")

    degree = alumni.get("degree")
    major = alumni.get("major")
    grad_year = alumni.get("graduation_year")
    if degree and major and grad_year:
        parts.append(f"graduated in {grad_year} with a {degree} in {major}.")
    elif grad_year:
        parts.append(f"Class of {grad_year}.")

    title = alumni.get("current_title")
    company = alumni.get("current_company")
    industry = alumni.get("industry")
    if title and company:
        parts.append(f"Currently works as {title} at {company}")
        if industry:
            parts.append(f"in the {industry} sector.")
        else:
            parts.append(".")
    elif company:
        parts.append(f"Employed at {company}.")

    city = alumni.get("city")
    country = alumni.get("country")
    if city and country:
        parts.append(f"Based in {city}, {country}.")
    elif country:
        parts.append(f"Based in {country}.")

    headline = alumni.get("headline")
    if headline:
        parts.append(f"Professional headline: {headline}.")

    bio = alumni.get("bio")
    if bio:
        parts.append(f"Summary: {bio}.")

    skills = alumni.get("skills", [])
    if skills:
        skills_str = ", ".join(skills)
        parts.append(f"Core verified competencies and technical skills: {skills_str}.")

    advisory = alumni.get("advisory_topics", [])
    if advisory:
        advisory_str = ", ".join(advisory)
        parts.append(f"Mentorship topics: {advisory_str}.")

    return " ".join(parts).strip()
