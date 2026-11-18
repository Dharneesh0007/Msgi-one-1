# MSGI One — Phase 0 Project Audit & Environment Inspection Report

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Phase:** Phase 0 — Project Foundation and Architecture Lock  
**Author:** Principal Software Architect, Senior Full-Stack Engineer, Database Architect, Mobile Application Engineer, AI Systems Architect, DevSecOps Engineer & Technical QA Lead  
**Audit Date:** November 18, 2026  
**Status:** COMPLETE (Evidence-Based)

---

## 1. Executive Summary

This audit was conducted directly within the host development environment (`C:\Users\dharneesh\OneDrive\Documents`) to inspect existing codebase artifacts, active background processes, dependencies, runtime engines, and configuration files prior to initiating Phase 0 architectural lock.

The inspection verified that **no prior MSGI One implementation, starter template, database schema, or backend service existed in the workspace**. An external directory `C:\alumni app` was detected in the IDE recent documents metadata; physical inspection revealed a single 0-byte uninitialized file (`Alumni app`) created on 2026-11-18 at 18:31. The workspace directory `C:\Users\dharneesh\OneDrive\Documents` is a shared user storage location containing unrelated projects (`smart-queue-system`, `course_planner`, `SmartRide`, `SmartOrderScheduler`) and personal files.

To prevent collision, preserve existing user projects, and maintain strict version control, an isolated, production-grade monorepo structure has been initialized at `msgi-one/`.

---

## 2. Existing Workspace Inspection & Evidence

### 2.1 Tooling & Runtime Environment Checks

All checks were executed via standard terminal commands inside the Windows PowerShell environment.

| Runtime / Tool | Verified Version | Executable Path | Status | Evidence / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Node.js** | `v24.21.0` | System PATH | **VERIFIED** | High-performance current LTS runtime |
| **npm** | `11.19.0` | System PATH | **VERIFIED** | Default Node package manager |
| **pnpm** | Not installed / Not in PATH | N/A | **ABSENT** | Will use `npm` or configure `pnpm` with bypass sandbox policy as needed |
| **Python** | `Python 3.12.13` | `C:\Users\dharneesh\AppData\Roaming\uv\python\cpython-3.12-windows-x86_64-none\python.exe` | **VERIFIED** | Windows Store execution alias was inactive; verified standalone CPython 3.12 managed via `uv` |
| **uv (Package Manager)**| `0.11.21` | `C:\Users\dharneesh\.local\bin\uv.exe` | **VERIFIED** | Lightning-fast Python package resolver and virtualenv manager |
| **Git** | `2.55.0.windows.3`| System PATH | **VERIFIED** | Git version control active |
| **Global npm Packages** | `@google/gemini-cli@0.64.0` | `AppData\Roaming\npm` | **VERIFIED** | Global AI CLI tooling present |

### 2.2 Directory Scan Results

1. **Current Working Directory (`C:\Users\dharneesh\OneDrive\Documents`):**
   - No Git repository existed at the root level (`fatal: not a git repository`).
   - Unrelated folders present: `.vscode`, `APPS`, `course_planner`, `Custom Office Templates`, `Gaming IDeas`, `Hogwarts Legacy`, `Mission Planner`, `My Games`, `OPPs with JAVA`, `Rainmeter`, `Rockstar Games`, `smart-queue-system`, `SmartOrderScheduler`, `SmartRide`, `WB Games`.
   - General `package.json` in root: Contains Next.js, React 19, ioredis, FingerprintJS from an independent session. Must NOT be modified or coupled with MSGI One.

2. **External Directory `C:\alumni app`:**
   - Path exists: Contains a single file `Alumni app` (0 bytes, created 18-11-2026 18:31).
   - Contains no source code, git history, or configuration.

---

## 3. Audit Findings Categorisation

### 3.1 Existing Project Structure
- Prior MSGI One structure: **None (Fresh Greenfield Start).**
- Monorepo directory created: `msgi-one/` with subtrees `apps/mobile/`, `services/api/`, `packages/contracts/`, `supabase/migrations/`, `supabase/seed/`, `docs/`, `tests/`, `scripts/`, `.github/workflows/`.

### 3.2 Reusable Components
- No domain-specific code from prior MSGI iterations exists.
- The system benefits from a zero-legacy state: no deprecated dependencies, zero architectural debt, and no conflicting authentication layers to reconcile.

### 3.3 Missing Components
Prior to Phase 0 execution, all 12 modules, authentication glue, API routers, database schemas, and AI agent graphs were absent:
- Frontend mobile app shell (Expo/React Native/TypeScript).
- Backend API service (FastAPI/Pydantic/SQLAlchemy).
- Database migrations and RLS policies (PostgreSQL/Supabase).
- Agentic workflow graph (LangGraph).
- Standardized API contracts and data dictionary.

### 3.4 Compatibility Issues
1. **Windows Pathing & PowerShell Execution:** Execution of shell scripts and virtualenvs requires explicit quoting and raw string pathing (e.g. `uv.exe` pathing).
2. **Windows App Execution Aliases:** Windows redirects bare `python` calls to the Microsoft Store unless configured. All backend commands must reference the verified `uv` toolchain or the direct Python 3.12 executable.
3. **OneDrive Folder Sync:** Developing inside an active OneDrive folder can create filesystem file-lock issues during high-frequency compilation or `node_modules` indexing. Git initialization inside `msgi-one/` must rigorously exclude `node_modules`, `.venv`, and temporary artifacts via `.gitignore`.

### 3.5 Security Concerns
- User root directory contains uncommitted personal files. All MSGI One operations must remain strictly scoped within `msgi-one/`.
- No sensitive keys or production credentials may be committed or generated as dummy values in production configurations.
- Student and alumni data require separation between public directory listings and sensitive PII (contact details, GPA, financial records).

### 3.6 Technical Debt
- Because this is a fresh build under a strict 3-day MVP timeline, the greatest risk is **accidental architecture sprawl** (e.g. microservices, distributed queues, prematurely complex event streams).
- A **modular monolith** with clean bounded contexts (Domain-Driven Design) is required to avoid distributed transaction overhead.

---

## 4. Recommended Actions for Phase 0

1. **Establish Isolated Repository:** Initialize a dedicated Git repository at `msgi-one/` with a comprehensive `.gitignore` preventing accidental check-in of personal documents, `.venv`, or `node_modules`.
2. **Lock Technology Stack:** Formally select Expo Router (v4) + React Native + TypeScript for mobile, FastAPI + SQLAlchemy 2.0 + Pydantic v2 for backend, Supabase PostgreSQL + RLS + pgvector for persistence, and LangGraph for agentic AI orchestration.
3. **Standardize Layered Architecture:** Codify Layers A through G to ensure strict decoupling between Presentation, Auth, Business API, Persistence, AI Agents, Realtime, and Observability.
4. **Define Full Database Schema & RLS:** Create 3NF-compliant relational schemas covering all 12 modules with explicit foreign keys, indexes, and row-level security policies.
5. **Establish API Contracts & OpenAPI Specifications:** Define versioned REST contracts (`/api/v1/*`) with strict Pydantic schemas and standard response envelopes before writing any endpoint implementation.
6. **Formulate Agentic AI Safety & Approval Gates:** Mandate human-in-the-loop gates for consequential actions (mentorship requests, alumni outreach, job applications, institutional record updates, donations).
7. **Formulate Realistic 3-Day Roadmap:** Classify all module features into P0 (Essential MVP), P1 (Time-Permitting), and P2 (Post-MVP), ensuring a verified working app is delivered by Day 3.

---

## 5. Open Questions & Prerequisites

| Item | Question / Dependency | Status | Mitigation / Path Forward |
| :--- | :--- | :--- | :--- |
| **Supabase Project** | Hosted cloud project vs local Supabase CLI? | Required for Phase 1 | Standardize on PostgreSQL connection strings and Supabase Auth client; provide local migration DDL scripts ready for either hosted or local CLI. |
| **LLM Provider API Key** | Target model provider (Gemini / Anthropic / OpenAI)? | Required for Phase 3 | Abstract LLM client using LangChain/LangGraph interface; default to Gemini 1.5/2.0 Flash via standard env variable `GEMINI_API_KEY`. |
| **Expo EAS Account** | EAS project credentials for Android build? | Required for Day 3 | Local build script fallback (`npx expo run:android` / prebuild APK) alongside EAS configuration in `app.json`. |
| **Institutional Seed Data** | Availability of real institutional rosters? | Policy Locked | Strictly forbid real student/alumni PII; use synthetically generated, clearly labeled realistic seed datasets. |

---

## 6. Audit Sign-Off

The workspace audit is complete, verified, and backed by terminal command execution. Greenfield initialization inside `msgi-one/` is approved.
