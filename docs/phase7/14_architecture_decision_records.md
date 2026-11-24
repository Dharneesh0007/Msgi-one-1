# MSGI ONE — PHASE 7 ARCHITECTURE DECISION RECORDS (ADR-06 TO ADR-10)
**Document Version:** 1.0.0  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Status:** **APPROVED & AUDITED**  

---

## ADR-06: Official Google GenAI SDK and Gemini 2.5 Inference Model Selection

### Context
Phase 3 implemented deterministic keyword heuristics. Phase 7 requires authentic artificial intelligence inference. Google Cloud released the modern `google-genai` Python SDK (v3.5.0), replacing the legacy `google-generativeai` package. Model lifecycles require selecting actively maintained models.

### Decision
1. Adopt the official `google-genai` SDK (v3.5.0).
2. Designate `gemini-2.5-flash` as the primary production generative model.
3. Remove unconfirmed assumptions regarding `gemini-1.5-flash`.
4. Make model identifiers configurable via `GEMINI_MODEL`.

### Consequences
- **Positive:** Sub-second latency, native Pydantic v2 structured outputs, native tool calling, 1M+ token context window.
- **Negative:** Requires external network access and valid `GEMINI_API_KEY` for live execution.

---

## ADR-07: Gemini-Embedding-001 with Explicit L2 Normalization and 1536-Dimensional Schema Compatibility

### Context
`text-embedding-004` was shut down on January 14, 2026. Furthermore, `public.alumni_profiles.embedding` is declared in the PostgreSQL schema as `vector(1536)`. Using a standard 768-dim model without Matryoshka learning would cause dimension mismatch or require silent vector padding. Additionally, Matryoshka embeddings requested at custom target dimensions cannot be assumed to be automatically unit-normalized; cosine distance indexing in pgvector (`<=>`) requires strictly L2-normalized unit vectors.

### Decision
1. Select `gemini-embedding-001` as the official text retrieval embedding model.
2. Request `output_dimensionality=1536` via `EmbedContentConfig` to generate 1536-dimensional representation vectors.
3. Apply explicit, consistent L2 vector normalization in Python (`normalize_l2_vector`) across both query and document embeddings:
   $$v_{norm} = \frac{v}{\|v\|_2} = \frac{v}{\sqrt{\sum_{i=1}^n v_i^2}}$$
4. Validate that output vectors contain exactly 1536 dimensions and reject degenerate, zero-length, or non-finite (NaN/Inf) vectors with `GeminiSchemaError`.
5. Explicitly prohibit silent vector padding or dimension truncation.
6. Record embedding metadata: `model_id="gemini-embedding-001"`, `dimensions=1536`, `version="v1"`, `normalization="L2"`.

### Consequences
- **Positive:** Perfect alignment with `public.alumni_profiles.embedding vector(1536)` without requiring destructive remote schema migrations. Mathematically sound cosine similarity calculations via dot product.
- **Negative:** Requires explicit L2 normalization computation in application memory for every embedding generation.

---

## ADR-08: Prohibition of Silent Deterministic / Seed-Data Fallback in Production

### Context
Earlier architecture documents proposed falling back to cached seed-data CSV files or deterministic mock responses when PostgreSQL or Gemini were unavailable. This violates Law 20 ("Stop and Report Blockers Rather Than Inventing Success").

### Decision
1. When `AI_PROVIDER=gemini`, the system must never silently fall back to deterministic mocks. If credentials or upstream services fail, raise explicit domain exceptions (`GeminiAuthError`, `GeminiQuotaError`, `GeminiServerOutageError`).
2. In production AI tools, database disconnection must raise `OperationalError` or `DatabaseUnavailableError`. Production operations must never use stale disk CSVs as authoritative data.
3. `AI_PROVIDER=deterministic` is retained strictly for isolated unit testing and CI/CD, always tagged as `meta={"execution_mode": "sandboxed_deterministic"}`.

### Consequences
- **Positive:** Eliminates fabricated success reporting; ensures total audit transparency and data integrity.
- **Negative:** Service outages result in transparent client-facing errors rather than synthetic responses.

---

## ADR-09: Mandatory Application-Layer Authorization & RLS Enforcement on `user_skills`

### Context
Audit of `supabase/migrations/20261118000001_initial_identity_schema.sql` revealed that `public.user_skills` was omitted from RLS enablement. Furthermore, the backend connection role `postgres` possesses `rolbypassrls = True`.

### Decision
1. Prepare local patch migration `20261121000002_user_skills_rls_patch.sql` providing owner-scoped policies (`user_id = auth.uid()`) for SELECT, INSERT, UPDATE, DELETE.
2. Validate RLS enforcement empirically within transactional rollbacks.
3. Block direct AI tool retrieval from `public.user_skills` until verified, routing student skill queries through `public.student_skills` (which already has RLS enabled).
4. Strictly enforce authorization in FastAPI application code (`user_id` filtering and JWT claims) because backend role `postgres` bypasses database RLS.

### Consequences
- **Positive:** Closes the direct PostgREST client exposure on `user_skills` while ensuring AI retrieval cannot access unauthorized records.
- **Negative:** Remote schema update requires explicit project owner approval prior to execution.

---

## ADR-10: Citation Grounding Verification and Uncalibrated Model Confidence

### Context
Generative models can hallucinate entity identifiers and factual claims even when constrained by Pydantic JSON schemas. Additionally, self-reported LLM confidence scores are uncalibrated heuristics.

### Decision
1. Implement algorithmic citation verification in Python: all model-generated citation IDs must be cross-checked against actual retrieved document IDs (`context_docs`). Unmatched citations are filtered out.
2. Label model confidence scores as `uncalibrated_confidence`, documenting that they represent model self-assessment rather than calibrated posterior probabilities.
3. Apply FERPA privacy sanitization (`sanitize_prompt_for_privacy`) to redact phone numbers, SSNs, and addresses before LLM invocation.

### Consequences
- **Positive:** Prevents fabricated citations from reaching students; maintains strict regulatory compliance.
- **Negative:** Requires context tracking through all generation stages.

---

## ADR-11: pgvector Vector Indexing Strategy (Exact Scan vs HNSW)

### Status: ACCEPTED
**Date:** 2026-11-21  
**Decision Maker:** Database Architect & Principal AI Systems Architect  

### Context
pgvector 0.8.2 supports exact sequential scanning, IVFFlat, and HNSW (Hierarchical Navigable Small World) index graphs for 1536-dimensional vectors. Approximate indexes introduce recall degradation (Recall@10 drops to 0.90–0.98) and significant index build overhead. For institutional alumni directories (< 10,000 profiles), exact vector scan delivers < 2.5ms latency on PostgreSQL 17 with 100% recall.

### Decision
Use exact sequential vector scan (`ORDER BY embedding <=> :query_vector LIMIT :k`) as the primary search engine for collections under 10,000 profiles. Pre-retrieval SQL filtering (`visibility IN ('public', 'institutional')`, `is_verified = TRUE`, `is_active = TRUE`) executes in the same relational plan. Prepare HNSW index DDL (`USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)`) to be deployed when collection exceeds 10,000 vectors.

### Consequences
- **Positive:** 100% mathematical precision and recall guarantee; zero index re-clustering or build maintenance.
- **Positive:** Relational predicates filter candidate rows before distance computation.
- **Negative:** Sub-linear scaling kicks in only when HNSW is activated at scale.

---

## ADR-12: Three-Tier Factual Grounding & Anti-Hallucination Guardrails

### Status: ACCEPTED
**Date:** 2026-11-21  
**Decision Maker:** ML Evaluation Lead & AI Security Architect  

### Context
Simple citation allowlisting verifies only that a cited identifier belongs to the retrieved evidence set (Existence). It does not guarantee that the passage is semantically relevant to the assertion (Relevance) or that the text actually supports the claim (Factual Support).

### Decision
Implement a 3-tier grounding evaluation pipeline in `src/ai/rag.py`:
1. **Tier 1 (Existence):** Allowlist check.
2. **Tier 2 (Relevance):** Cosine similarity between claim embedding and passage text ($\ge 0.20$).
3. **Tier 3 (Factual Support):** Informational keyword precision and token overlap ($\ge 0.35$).
If retrieved evidence is empty or unsupported, output standardized institutional refusal (`INSUFFICIENT_EVIDENCE_REFUSAL`) with zero fabricated facts or citations.

### Consequences
- **Positive:** Mathematically and lexically distinguishes supported facts from hallucinated assertions.
- **Positive:** Zero fabricated institutional facts or phantom faculty/alumni records.
- **Negative:** Adds ~10–25ms of evaluation processing per response.

