# MSGI ONE — PERMANENT AGENT INSTRUCTIONS & ENGINEERING RULES

**Project Title:** MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem  
**Target Environment:** Google Antigravity IDE  
**Enforcement Level:** MANDATORY ACROSS ALL PHASES  

---

Every AI agent, subagent, and human engineer operating on the MSGI One repository must adhere strictly to these 20 permanent engineering laws:

1. **Always Inspect the Repository Before Editing:** Never assume directory contents or file state. Inspect files and check existing implementations before creating or modifying code.
2. **Preserve Working Code and Existing Functionality:** Do not break, overwrite, or refactor working endpoints, models, or screens without explicit authorization and backward-compatibility preservation.
3. **Never Create Duplicate Systems:** All 12 modules must share the central identity system (`users`, `user_roles`), the shared database schema, and the single authentication provider (Supabase Auth). Never create duplicate user tables, alternate JWT handlers, or parallel auth flows.
4. **Maintain Shared Database and API Contracts:** All database entities and endpoints must conform strictly to `docs/DATABASE_DESIGN.md` and `docs/API_CONTRACT.md`. Any contract modification requires an updated ADR and schema migration.
5. **Follow the Approved Architecture:** Adhere strictly to the 7-layer architecture (Layers A through G) documented in `docs/SYSTEM_ARCHITECTURE.md`.
6. **Use Modular, Typed, and Maintainable Code:** Enforce strict typing in TypeScript (`strict: true`) and Python (Pydantic v2, SQLAlchemy 2.0 type annotations). Write modular domain services with low coupling and high cohesion.
7. **Do Not Hardcode Secrets:** Never hardcode API keys, service role tokens, passwords, or private connection strings. Store secrets strictly in environment variables loaded via `.env` templates.
8. **Do Not Fabricate Institutional Data:** Never invent real institutional alumni, student rosters, faculty identities, or personal phone numbers.
9. **Use Synthetic Seed Data Only When Clearly Labelled:** All seed data must be explicitly synthetic, deterministic, and labeled with `@example.msgi.edu` email domains (`supabase/seed/00001_synthetic_seed.sql`).
10. **Never Claim an API or Feature Works Without Testing It:** No feature may be reported as working without actual terminal execution evidence (curl, test runner logs, or browser/mobile verification).
11. **Write and Run Relevant Tests:** Every phase must implement and pass its required unit, integration, and API contract tests before requesting phase sign-off.
12. **Validate Cross-Module Integration:** Verify that consumer modules correctly interact with upstream domain services and shared database entities without foreign key violations.
13. **Request Approval Before Destructive Actions:** Never execute destructive SQL migrations (`DROP TABLE`, `TRUNCATE`), delete user files, or reset Git branches without explicit human approval.
14. **Log Important AI Workflow Actions:** All LangGraph agent runs, tool invocations, token metrics, and latency must be logged in `public.agent_runs` and `public.agent_actions`.
15. **Require Human Approval for Consequential Actions:** Autonomous agents must never send emails, dispatch mentorship requests, apply to jobs, alter institutional records, or charge funds without explicit human-in-the-loop approval.
16. **Keep Phase Completion Reports Evidence-Based:** Every phase completion report must cite exact commands executed, test outputs, file diffs, and verification metrics.
17. **Use Current Official Tool Documentation:** Use official commands and API references for Expo SDK 52+, React Native, FastAPI, SQLAlchemy 2.0, Supabase, and LangGraph.
18. **Apply the Documented Engineering Principles:** Ground architecture decisions in the international textbook standards of Pressman & Maxim, Silberschatz, Kleppmann, Sommerville, and Evans.
19. **Keep Environment and Deployment Instructions Updated:** Whenever dependencies or environment variables change, update `README.md`, `docs/TECHNOLOGY_STACK.md`, and `.env.example`.
20. **Stop and Report Blockers Rather Than Inventing Success:** If an environment dependency, permission check, or external service is unavailable, mark it `BLOCKED` or `NOT VERIFIED`, explain why, and request guidance. Never pretend a blocked task succeeded.
