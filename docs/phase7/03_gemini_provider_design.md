# MSGI ONE — GATE 7.2 LIVE GEMINI MODEL PROVIDER DESIGN (REVISED)
**Document Version:** 2.0.0 (Remediated via Executive Correction Addendum)  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Author:** Principal AI Systems Architect & AI Security Lead  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Status:** **REMEDIATED & IMPLEMENTATION-READY**  

---

## 1. Executive Overview

This revised specification establishes the corrected architectural foundation for MSGI One's Gemini AI integration, addressing the model lifecycle and access-control findings outlined in the Phase 7 Engineering Correction Addendum.

In accordance with Directive v2.0 and the engineering principles of Stuart Russell & Peter Norvig (*Artificial Intelligence: A Modern Approach*) and Martin Kleppmann (*Designing Data-Intensive Applications*), the AI provider layer enforces:
1. Genuine asynchronous Gemini SDK inference with strict non-fallback guarantees in live mode.
2. Verified model lifecycle compliance (retiring deprecated models).
3. Exact 1536-dimensional vector schema compatibility without silent truncation or padding.
4. Structural response validation via Pydantic v2 combined with algorithmic citation verification.
5. Explicit data minimization and FERPA-compliant privacy sanitization.

---

## 2. Updated Model Lifecycle & Selection

### 2.1 Generative Model Selection: `gemini-2.5-flash`
- **Primary Model ID:** `gemini-2.5-flash` (configurable via `GEMINI_MODEL`).
- **Retired Models:** `gemini-1.5-flash` has been removed as an assumed fallback; it is not utilized unless independently verified as active in the host environment.
- **Model Capabilities:**
  - Sub-second time-to-first-token (TTFT) optimized for conversational interfaces on mobile and web.
  - Native structured output parsing using `response_schema` and Pydantic v2.
  - Function-calling tool execution conforming to modern tool orchestration standards.
  - 1M+ token context window supporting rich institutional retrieval context.

### 2.2 Embedding Model Selection: `gemini-embedding-001`
- **Primary Model ID:** `gemini-embedding-001` (configurable via `GEMINI_EMBEDDING_MODEL`).
- **Retired Model:** `text-embedding-004` was permanently shut down on January 14, 2026, and has been completely removed from codebase and documentation.
- **Dimensionality Matching & Matryoshka Representation:**
  - The canonical database schema defines `public.alumni_profiles.embedding` as `vector(1536)`.
  - `gemini-embedding-001` supports flexible output dimensionality via Matryoshka representation learning.
  - By passing `output_dimensionality=1536` in `types.EmbedContentConfig`, the model directly generates native 1536-dimensional normalized vectors.
  - **Invariant:** Zero silent padding, zero truncating, and zero schema drift. Output dimensions match the PostgreSQL table definition natively.
- **Task Types:** `RETRIEVAL_DOCUMENT` (for catalog indexing) and `RETRIEVAL_QUERY` (for user search queries).

---

## 3. Strict Provider Boundaries & Failure Behavior

### 3.1 Prohibition of Silent Mock Fallback
Per Correction 3.3, `AI_PROVIDER=gemini` must never silently substitute mock or deterministic responses:
- If `GEMINI_API_KEY` is missing, unconfigured, or set to placeholder, the provider **fails fast** with `GeminiAuthError`.
- If upstream Gemini returns an HTTP 429 quota exhaustion, 503 outage, or timeout, the provider raises a typed domain exception (`GeminiQuotaError`, `GeminiServerOutageError`, `GeminiTimeoutError`).
- In live mode, failures are reported transparently in the API error envelope (`status: "error"`, `code: "UPSTREAM_PROVIDER_ERROR"`).

### 3.2 Explicitly Labeled Offline Mode
`AI_PROVIDER=deterministic` is preserved strictly for local unit testing and continuous integration:
- Computes deterministic intent extraction and unit-normalized 1536-dim pseudo-vectors from SHA-256 hashes.
- Always tagged in the response payload metadata: `meta={"execution_mode": "sandboxed_deterministic"}`.

---

## 4. Citation Grounding & Hallucination Mitigation

### 4.1 Structural Validation vs. Factual Grounding
Pydantic schema validation ensures syntactical structure and data typing; it **does not** prevent factual hallucinations or fabricated entity references.

### 4.2 Algorithmic Citation Verification
To prevent ungrounded claims, model outputs are subjected to post-generation verification:
```python
def verify_source_citations(citations: List[str], context_docs: Optional[List[Dict[str, Any]]]) -> List[str]:
    """Filters model citations to ensure they strictly exist in retrieved context."""
    if not context_docs or not citations:
        return []
    valid_ids: Set[str] = {str(d.get("id")) for d in context_docs if d.get("id")}
    return [c for c in citations if c in valid_ids]
```
Any citation ID emitted by the LLM that does not match an actual retrieved document ID in `context_docs` is filtered out.

### 4.3 Uncalibrated Model Confidence
Self-reported model confidence scores (e.g. `uncalibrated_confidence: float`) are explicitly treated as subjective model heuristics rather than calibrated mathematical probabilities. They are documented as uncalibrated telemetry.

---

## 5. Privacy Sanitization & External Data Controls

Before any user query or profile context is transmitted to the Gemini API:
1. `sanitize_prompt_for_privacy(prompt)` strips sensitive telephone numbers, national IDs, and exact street addresses.
2. User identity is restricted to opaque UUIDs (`user.id`) and academic role (`user.roles`).
3. Private contact info (FERPA-protected phone, email, physical address) is never transmitted.
4. Server-side API keys remain strictly confined to the backend environment.

---

## 6. Acceptance Criteria

- [x] Deprecated `text-embedding-004` removed; `gemini-embedding-001` configured with `output_dimensionality=1536`.
- [x] Assumed `gemini-1.5-flash` fallback removed.
- [x] Silent deterministic fallback in `AI_PROVIDER=gemini` mode prohibited; fails fast with `GeminiAuthError`.
- [x] Citation verification against retrieved document IDs implemented.
- [x] Privacy sanitization implemented.
- [x] 14/14 unit and integration tests passing in `test_gemini_provider.py`.
