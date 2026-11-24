# MSGI ONE — GATE 7.9 DATASET INVENTORY & GOVERNANCE SPECIFICATION
**Document Version:** 1.0.0  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Authors:** ML Data Architect, Compliance Lead & AI Systems Architect  
**Status:** **APPROVED & AUDITED [V-READ]**  

---

## 1. Executive Summary & Policy Compliance

Under MSGI Engineering Law 8 and Law 9:
- **Zero Fabrication:** No real alumni, faculty, student rosters, personal phone numbers, or institutional secrets have been fabricated.
- **Explicit Synthetic Data:** All test accounts, profiles, and evaluation records are deterministically derived, labeled with `@example.msgi.edu`, and isolated to development environments.

---

## 2. Ingested & Evaluated Datasets Inventory

| Dataset Identifier | Storage Location | Entity Count | Sensitivity | Licensing / Provenance | Purpose |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`career_role_skills`** | `supabase/seed/csv/career_role_skills.csv` | 42 records | Public / Curated | Institutional Curriculum Benchmark | Maps target career roles (AI Engineer, Data Scientist, Product Manager) to competency taxonomies. |
| **`learning_resources`** | `supabase/seed/csv/learning_resources.csv` | 38 records | Public / Curated | Open Educational Repositories | Curated courseware, providers, ratings, durations, and skill mappings. |
| **`synthetic_alumni_directory`** | `_SYNTHETIC_ALUMNI_STORE` / SQL Seeds | 6 verified profiles | Synthetic Test | Deterministic MIT-equivalent test accounts | Benchmark profiles for semantic vector retrieval, FERPA masking, and filtering. |
| **`ai_evaluation_cases`** | `supabase/seed/ai_evaluation_cases.jsonl` | 24 cases | Synthetic Test | Antigravity QA Suite | Benchmark evaluation suite covering routing, skill gap, and injection attacks. |
| **`qa_security_cases`** | `supabase/seed/qa_security_cases.jsonl` | 18 cases | Synthetic Test | Antigravity Security Suite | Prompt injection, role tampering, and cross-user authorization test fixtures. |

---

## 3. Data Schema & Record Definition

Every evaluation fixture in MSGI One conforms to a strict JSONL/CSV contract:
```json
{
  "case_id": "eval-rag-001",
  "use_case": "alumni_discovery",
  "user_role": "student",
  "tenant_scope": "msgi_main",
  "query": "Find verified alumni working in Artificial Intelligence in Japan",
  "expected_behavior": "ROUTE_ALUMNI",
  "reference_answer": "Kenji Sato, Staff AI Engineer at Rakuten Symphony in Tokyo, Japan.",
  "reference_document_ids": ["alumni-kenji-sato"],
  "allowed_document_ids": ["alumni-kenji-sato", "alumni-yuki-tanaka"],
  "expected_refusal": false,
  "sensitivity_class": "institutional_public"
}
```

**Gate 7.9 Dataset Inventory Status:** **APPROVED [V-READ]**
