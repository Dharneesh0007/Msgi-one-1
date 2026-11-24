# MSGI ONE — PGVECTOR EMBEDDING SPACE & RE-INDEXING STRATEGY

**Document ID:** MSGI-EMB-001  
**Phase:** Phase 2 — Database Engineering & Backend Foundation  

## 1. Current Embedding Contract (Preserved)
- **Vector Column:** `public.alumni_profiles.embedding vector(1536)` (1536 dimensions, L2-normalized via `normalize_l2_vector()`).
- **Index Type:** HNSW (`vector_cosine_ops`) queried via cosine distance `<=>`.
- **Active Space:** `gemini-embedding-001` truncated/configured to 1536 dimensions and unit-normalized.

## 2. Space Isolation Invariant
Incompatible embedding models (e.g., OpenAI `text-embedding-3-small` vs Gemini `gemini-embedding-001`, or unnormalized vs L2-normalized) **must never** be mixed inside the same `vector(1536)` search space. Cosine distance comparisons across different vector spaces yield meaningless rankings.

## 3. Zero-Downtime Re-Indexing Migration Protocol (For Future Model Changes)
1. Add a versioned shadow column (`embedding_v2 vector(1536)`) and metadata column (`embedding_model_version VARCHAR(64)`).
2. Backfill `embedding_v2` asynchronously in bounded batches using the new model, enforcing L2 normalization.
3. Build the new HNSW index concurrently (`CREATE INDEX CONCURRENTLY ... USING hnsw (embedding_v2 vector_cosine_ops)`).
4. Evaluate recall@k and MRR on the offline evaluation dataset before switching application reads.
5. Atomically swap the read target via feature flag / view, then drop the deprecated column in a subsequent authorized migration.
