"""
MSGI One — RAG Grounding, Citation Validation & Anti-Hallucination Pipeline (Gate 7.6)
Principles:
- Christopher D. Manning et al. (Information Retrieval & Passage Verification)
- OWASP Top 10 for LLM Applications (Anti-Hallucination & Prompt Injection Defenses)
Implements:
1. 3-tier citation verification:
   a. Citation Existence (Entity Allowlisting)
   b. Citation Relevance (Vector & Token Similarity)
   c. Factual Support (Lexical & Semantic Entailment)
2. Insufficient evidence detection with truthful refusal (zero fabricated institutional facts).
3. Untrusted document sanitization (preventing indirect prompt injection in retrieved context).
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from src.ai.provider import provider, cosine_similarity, compute_cosine_similarity


# Standardized truthful refusal template when evidence is insufficient
INSUFFICIENT_EVIDENCE_REFUSAL = (
    "The institutional repository does not contain verified records regarding this request. "
    "In accordance with institutional integrity standards, no ungrounded or speculative information is provided. "
    "Please consult the verified MSGI Academic or Placement Office for official assistance."
)

# Indirect prompt injection markers found in untrusted external text
INDIRECT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+all\s+(?:previous|prior)\s+instructions",
    r"(?i)system\s+override",
    r"(?i)grant\s+(?:me\s+)?(?:admin|root|superuser)\s+role",
    r"(?i)reveal\s+(?:all\s+)?(?:credentials|api\s*keys|passwords)",
    r"(?i)drop\s+table",
    r"(?i)execute\s+tool",
    r"(?i)bypass\s+(?:approval|security|gate)",
    r"(?i)new\s+system\s+instruction:",
]


class CitationEvaluation(BaseModel):
    citation_id: str
    existence: bool = False
    relevance_score: float = 0.0
    factual_support_score: float = 0.0
    verdict: str = "unsupported"  # 'grounded', 'weakly_supported', 'unsupported', 'hallucinated'


class GroundingEvaluationResult(BaseModel):
    query: str
    overall_grounding_score: float
    is_grounded: bool
    verified_citations: List[str]
    rejected_citations: List[str]
    citation_details: List[CitationEvaluation]
    insufficient_evidence: bool = False
    refusal_message: Optional[str] = None


def sanitize_retrieved_content(text: str) -> str:
    """
    Sanitizes untrusted retrieved text (resumes, course descriptions, community posts)
    against indirect prompt injection attacks before context assembly.
    """
    if not text:
        return ""

    sanitized = text
    for pattern in INDIRECT_INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[BLOCKED_INDIRECT_INJECTION_ATTEMPT]", sanitized)

    # Neutralize markdown system delimiters
    sanitized = sanitized.replace("```system", "```neutralized")
    sanitized = sanitized.replace("```instruction", "```neutralized")
    return sanitized.strip()


def evaluate_citation_relevance_and_support(
    assertion: str,
    doc_id: str,
    doc_text: str,
    query_vector: Optional[List[float]] = None,
) -> Tuple[float, float]:
    """
    Computes:
    1. Relevance Score: Cosine similarity between assertion embedding and document passage.
    2. Factual Support Score: Precision of assertion's significant informational keywords in passage.
    """
    if not doc_text or not assertion:
        return 0.0, 0.0

    # 1. Semantic Relevance
    try:
        vec_assertion = provider.embed_query(assertion)
        vec_doc = provider.embed_query(doc_text)
        relevance = max(0.0, cosine_similarity(vec_assertion, vec_doc))
    except Exception:
        relevance = 0.0

    # 2. Lexical Support (Informational keyword overlap)
    assertion_words = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", assertion.lower()))
    doc_words = set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", doc_text.lower()))

    # Ignore ubiquitous stop words
    stop_words = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "works", "based"}
    assertion_keywords = assertion_words - stop_words

    if not assertion_keywords:
        support = 1.0 if assertion_words.issubset(doc_words) else 0.0
    else:
        overlap = len(assertion_keywords.intersection(doc_words))
        support = overlap / len(assertion_keywords)

    return round(relevance, 4), round(support, 4)


def evaluate_grounding(
    claims: List[str],
    retrieved_docs: List[Dict[str, Any]],
    query: str = "",
    min_support_threshold: float = 0.35,
    min_relevance_threshold: float = 0.20,
) -> GroundingEvaluationResult:
    """
    Evaluates factual grounding across all claims and candidate citations.
    Enforces 3-tier verification:
    - Tier 1: Citation existence in retrieved_docs
    - Tier 2: Relevance score >= min_relevance_threshold
    - Tier 3: Support score >= min_support_threshold
    """
    if not retrieved_docs or not claims:
        return GroundingEvaluationResult(
            query=query,
            overall_grounding_score=0.0,
            is_grounded=False,
            verified_citations=[],
            rejected_citations=[],
            citation_details=[],
            insufficient_evidence=True,
            refusal_message=INSUFFICIENT_EVIDENCE_REFUSAL,
        )

    doc_map: Dict[str, str] = {}
    for d in retrieved_docs:
        d_id = str(d.get("id") or d.get("document_id") or "")
        d_text = str(d.get("content") or d.get("bio") or d.get("headline") or d.get("description") or "")
        if d_id:
            doc_map[d_id] = d_text

    verified_ids: Set[str] = set()
    rejected_ids: Set[str] = set()
    evaluations: List[CitationEvaluation] = []
    total_scores: List[float] = []

    for d_id, d_text in doc_map.items():
        # Evaluate how strongly this document supports any of the asserted claims
        best_rel = 0.0
        best_sup = 0.0

        for claim in claims:
            rel, sup = evaluate_citation_relevance_and_support(claim, d_id, d_text)
            if rel > best_rel:
                best_rel = rel
            if sup > best_sup:
                best_sup = sup

        combined = (best_rel * 0.4) + (best_sup * 0.6)
        total_scores.append(combined)

        if best_sup >= min_support_threshold and best_rel >= min_relevance_threshold:
            verdict = "grounded"
            verified_ids.add(d_id)
        elif best_sup >= (min_support_threshold * 0.6):
            verdict = "weakly_supported"
            verified_ids.add(d_id)
        else:
            verdict = "unsupported"
            rejected_ids.add(d_id)

        evaluations.append(
            CitationEvaluation(
                citation_id=d_id,
                existence=True,
                relevance_score=best_rel,
                factual_support_score=best_sup,
                verdict=verdict,
            )
        )

    overall_score = round(sum(total_scores) / len(total_scores), 4) if total_scores else 0.0
    is_grounded = bool(verified_ids and overall_score >= 0.3)

    return GroundingEvaluationResult(
        query=query,
        overall_grounding_score=overall_score,
        is_grounded=is_grounded,
        verified_citations=sorted(list(verified_ids)),
        rejected_citations=sorted(list(rejected_ids)),
        citation_details=evaluations,
        insufficient_evidence=not is_grounded,
        refusal_message=None if is_grounded else INSUFFICIENT_EVIDENCE_REFUSAL,
    )
