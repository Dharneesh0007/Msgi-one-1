# MSGI One — AI Governance, Evaluation & Safety Policy (Phase 12)

Governing References:
- Chip Huyen — *AI Engineering* & *Designing Machine Learning Systems*
- Stuart Russell & Peter Norvig — *Artificial Intelligence: A Modern Approach*, 4th Ed.
- MSGI `AGENTS.md` Rules 7, 8, 9, 14, 15

---

## 1. Mandatory AI Safety Guardrails
1. **Rule 15 (Human-In-The-Loop Approval):** No autonomous tool may send messages, create/reschedule/cancel meetings, send mentorship requests, apply to jobs, or register for events without an authenticated owner's approval decision backed by SHA-256 `args_hash` verification and 15-minute TTL expiration.
2. **Defense-in-Depth PII Sanitization:** Outgoing external LLM prompts pass through `sanitize_prompt_for_privacy()` stripping email addresses, phone numbers, card numbers, and national ID shapes.
3. **Indirect Prompt Injection Neutralization:** Retrieved documents pass `sanitize_retrieved_content()` before synthesis.
4. **Grounded Truthful Refusal:** Unverified institutional facts must never be fabricated; insufficient evidence returns standardized institutional refusal.
5. **Strict RBAC Tool Scoping:** Administrative analytics tools verify `admin`/`faculty`/`superadmin` role prior to any data read.

## 2. Cryptographic Credential Governance
- Vendor LLM API keys (`gemini`, `openai`, `anthropic`, `deepseek`) are stored exclusively encrypted via **AES-256-GCM** with Associated Authenticated Data (`provider:config_id:v<version>`).
- Zero endpoints serialize ciphertext, nonces, or plaintext API keys; admin listings return masked `key_hint` metadata only.

## 3. Release-Blocking AI Evaluation Policy
- Before merging changes to `src/ai/`, the 15-case canonical evaluation suite (`supabase/seed/ai_evaluation_cases.jsonl`) AND `test_phase8_ai_platform.py` must achieve **100% pass rate (0 failures)**.
- Every live invocation logs telemetry (provider, model, prompt/output/thinking tokens, latency, status, error code, USD estimate) into `ai_usage_ledger`.
