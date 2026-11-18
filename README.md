# MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem

MSGI One is an enterprise-grade, integrated mobile platform connecting Students, Alumni, Faculty, Recruiters, and Institutional Administrators into a unified ecosystem.

Built as an **Android-first mobile application** powered by **FastAPI, Supabase PostgreSQL, and LangGraph Agentic AI**.

---

## 1. System Architecture Summary

The ecosystem follows a strict **7-Layer Modular Monolith Architecture**:
- **Layer A (Presentation):** React Native, Expo SDK 52+, Expo Router v4 (strict TypeScript).
- **Layer B (Auth & AuthZ):** Supabase Auth + FastAPI JWT RS256 Stateless Verification + Server-side RBAC.
- **Layer C (Business API):** FastAPI 0.115+, Python 3.12, Pydantic v2 domain schemas.
- **Layer D (Persistence):** PostgreSQL 15+ (Supabase), pgvector (HNSW 1536-dim), Row-Level Security.
- **Layer E (Agentic AI):** LangGraph StateGraph, specialized domain agents, human approval gates.
- **Layer F (Realtime):** Supabase Realtime (PostgreSQL CDC WebSockets).
- **Layer G (Observability):** Structured logging, audit trails, and execution trace tables.

---

## 2. Directory Structure

```
msgi-one/
├── apps/
│   └── mobile/                # Expo React Native Android Client
├── services/
│   └── api/                   # FastAPI Backend & LangGraph Agent Engine
├── packages/
│   └── contracts/             # Shared TypeScript & Python Types
├── supabase/
│   ├── migrations/            # Versioned SQL Schema & RLS DDL
│   └── seed/                  # Synthetic, Anonymized Seed Fixtures
├── docs/                      # Phase 0 Architecture Specifications
├── tests/
│   ├── unit/                  # Domain Unit Tests
│   └── integration/           # API & Database Integration Tests
├── scripts/                   # Local Startup & Verification Utilities
├── .github/workflows/         # CI/CD Verification Workflows
├── .env.example               # Safe Environment Template
├── .gitignore
├── AGENTS.md                  # Permanent Engineering Rules
└── README.md
```

---

## 3. Getting Started

### 3.1 Prerequisites
- **Node.js:** v20+ LTS (Tested on v24.21.0)
- **Python:** v3.12+ (Managed via `uv` or standard CPython)
- **Git:** Version 2.40+

### 3.2 Environment Setup
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Populate the `.env` variables with your Supabase project credentials and LLM provider key.

### 3.3 Running the Backend API
```bash
cd services/api
# Using uv (recommended)
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Health Check Endpoint: `http://localhost:8000/api/v1/health`  
Interactive OpenAPI Documentation: `http://localhost:8000/docs`

### 3.4 Running the Mobile App
```bash
cd apps/mobile
npm install
npx expo start --android
```

### 3.5 Running Automated Tests
```bash
# Backend Tests
cd services/api
uv run pytest tests/ -v

# Mobile Type Checking
cd apps/mobile
npx tsc --noEmit
```

---

## 4. Documentation Index

- [PHASE_0_PROJECT_AUDIT.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/PHASE_0_PROJECT_AUDIT.md)
- [TECHNOLOGY_STACK.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/TECHNOLOGY_STACK.md)
- [ARCHITECTURE_DECISIONS.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/ARCHITECTURE_DECISIONS.md)
- [SYSTEM_ARCHITECTURE.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/SYSTEM_ARCHITECTURE.md)
- [MODULE_SPECIFICATIONS.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/MODULE_SPECIFICATIONS.md)
- [MODULE_DEPENDENCY_MATRIX.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/MODULE_DEPENDENCY_MATRIX.md)
- [DATABASE_DESIGN.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/DATABASE_DESIGN.md)
- [DATABASE_ER_DIAGRAM.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/DATABASE_ER_DIAGRAM.md)
- [DATA_DICTIONARY.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/DATA_DICTIONARY.md)
- [ROW_LEVEL_SECURITY_PLAN.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/ROW_LEVEL_SECURITY_PLAN.md)
- [API_CONTRACT.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/API_CONTRACT.md)
- [API_PERMISSION_MATRIX.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/API_PERMISSION_MATRIX.md)
- [AGENTIC_AI_ARCHITECTURE.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/AGENTIC_AI_ARCHITECTURE.md)
- [AGENT_TOOL_CONTRACTS.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/AGENT_TOOL_CONTRACTS.md)
- [AI_SAFETY_AND_APPROVALS.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/AI_SAFETY_AND_APPROVALS.md)
- [END_TO_END_WORKFLOW.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/END_TO_END_WORKFLOW.md)
- [SECURITY_PLAN.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/SECURITY_PLAN.md)
- [TEST_STRATEGY.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/TEST_STRATEGY.md)
- [THREE_DAY_ROADMAP.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/docs/THREE_DAY_ROADMAP.md)
- [AGENTS.md](file:///c:/Users/dharneesh/OneDrive/Documents/msgi-one/AGENTS.md)
