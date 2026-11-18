# MSGI ONE — PHASE 3 HUMAN APPROVAL & ERROR RECOVERY
**Principles Applied:**
- Rule 15 of `AGENTS.md`: Mandatory human approval for consequential actions.
- Martin Kleppmann: Fault tolerance, idempotent retries, state machine consistency.
- Abraham Silberschatz: Transaction isolation and authorization enforcement.

---

## 1. RULE 15 ENFORCEMENT PROTOCOL

Under no circumstances is an AI agent permitted to unilaterally execute consequential institutional mutations:
1. `submit_job_application` (CareerBridge)
2. `create_mentor_request` (MentorMatch)
3. `register_for_event` (Events & Reunions)

### Interruption Sequence:
1. When a user prompt requests a consequential mutation (e.g. "Apply to the AI Research Intern position"), the domain agent detects the action type.
2. The agent stages an `ApprovalRequestRecord` with a deterministic `idempotency_key = sha256(user_id:action_type:target_entity_id)`.
3. The workflow pauses execution (`state["status"] = "interrupted"`), returning the pending approval payload in the API response.
4. The mobile UI displays the **Human-In-The-Loop Confirmation Modal** with action type, entity name, and risk warning.
5. Execution resumes ONLY when the user clicks **"Confirm & Execute"** (`POST /api/v1/ai/approvals/{id}/decision` with `decision: "approved"`).
6. If the user clicks **"Reject / Cancel"**, the request is marked `status = "rejected"`, and the mutation is aborted without executing the underlying tool.

---

## 2. CROSS-USER AUTHORIZATION DEFENSE

All approval decision endpoints enforce strict user ownership:
```python
if record.user_id != user.id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "PERMISSION_DENIED", "message": "Cannot decide an approval request owned by another user."}
    )
```
Verified via test `test_cross_user_approval_tampering_is_forbidden` in `tests/test_ai_command_centre.py`.

---

## 3. IDEMPOTENT EXECUTION & RECOVERY

- Every approval request is assigned a unique idempotency key based on user and target entity.
- If a client resubmits an approval decision due to network interruption or duplicate click, the engine checks:
  ```python
  if record.status in ("approved", "rejected"):
      return record
  ```
  This guarantees that mutations (such as event registrations or mentor requests) are never dispatched more than once.

---

## 4. PROVIDER FAILURE & OFFLINE RESILIENCE

If an external LLM provider API (e.g. Gemini or OpenAI) fails, times out, or has no configured API key:
1. The AI engine automatically switches to the built-in **Deterministic Semantic Engine**.
2. All 10 domain tools remain fully queryable.
3. Zero crashes or unhandled 500 errors occur.
4. Response latency stays under 20ms.
