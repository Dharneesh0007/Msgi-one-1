# MSGI ONE — PHASE 3 INTEGRATION HANDOFF GUIDE
**Handoff Target:** Phase 4 Preparation  
**Module Status:** MSGI AI Command Centre Operational  

---

## 1. CONSUMER INTEGRATION POINTS FOR DOWNSTREAM MODULES

Downstream mobile screens, web portals, and external services can interact with the AI Command Centre via:

1. **Natural-Language Career Assistant:**
   - Call `api.chatWithAI(prompt, sessionId)` in mobile client.
   - Endpoint: `POST /api/v1/ai/chat`
   - Response contains structured `skill_gap`, `learning_roadmap`, `recommended_mentors`, `recommended_jobs`, and `final_summary`.

2. **Consequential Action Approval Workflow:**
   - Listen for `status === "interrupted"` or `pending_approval !== null`.
   - Poll or query `GET /api/v1/ai/approvals/pending` to present user with pending action queue.
   - Submit human decision via `POST /api/v1/ai/approvals/{id}/decision` with body `{"decision": "approved" | "rejected"}`.

3. **Domain Service Tool Reuse:**
   - All 10 tools in `src/ai/tools.py` remain independently callable by subsequent agents, background batch tasks, or mobile controllers.

---

## 2. REPOSITORY & RUNTIME INVARIANTS TO PRESERVE

- **Authentication Source:** `auth.users` via Supabase JWT.
- **Rule 15 Enforcement:** Under no circumstances should auto-approval bypasses be added.
- **Standard Envelope:** All new endpoints must preserve `{ status, data, error, meta, timestamp }`.
- **Database Status:** Cloud PG connectivity remains marked `BLOCKED` until live credentials and network whitelist are provisioned.
