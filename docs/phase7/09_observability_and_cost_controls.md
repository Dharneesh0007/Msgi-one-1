# MSGI ONE — GATE 7.8 OBSERVABILITY, TELEMETRY & COST GOVERNANCE
**Document Version:** 1.0.0  
**Phase:** 7 — Intelligent AI Infrastructure and Verified Integration  
**Governance:** MSGI One Executive Engineering Directive v2.0  
**Authors:** Senior Site Reliability Engineer, AI Systems Architect & Database Architect  
**Status:** **IMPLEMENTED & VERIFIED [V-EXEC]**  

---

## 1. Executive Summary

This document specifies the operational observability, latency metrics, token expenditure accounting, cost governance, circuit breaker architecture, and persistent audit persistence for Gate 7.8.

---

## 2. Token Accounting & Official Pricing Governance

### 2.1 Official Google Gemini Pricing (Verified November 2026 Tiers)
In accordance with Section 9.2 of Executive Directive v2.0, all cost estimations are based strictly on published official pricing:

| Model Tier | Input Cost / 1M Tokens | Output Cost / 1M Tokens | Context Window |
| :--- | :---: | :---: | :---: |
| **`gemini-2.5-flash`** (Text) | **$0.075** | **$0.300** | 1,048,576 tokens |
| **`gemini-embedding-001`** | **$0.020** | N/A | 2,048 tokens |

### 2.2 Mathematical Formulation (`calculate_request_cost`):
$$\text{Cost}_{\text{generative}} = \left(\frac{\text{Prompt Tokens}}{1,000,000} \times 0.075\right) + \left(\frac{\text{Candidate Tokens}}{1,000,000} \times 0.300\right)$$

$$\text{Cost}_{\text{embedding}} = \frac{\text{Tokens}}{1,000,000} \times 0.020$$

---

## 3. Cost & Safety Guardrails (`services/api/src/ai/observability.py`)

1. **Per-Request Token Ceiling:** Configured to `DEFAULT_MAX_REQUEST_TOKENS = 4096`. Prompts or contexts exceeding this ceiling are rejected or truncated before inference.
2. **Maximum Graph Iterations:** Hard cap of 8 graph node transitions prevents infinite routing loops.
3. **Maximum Tool Calls:** Cap of 6 tool invocations per session.
4. **Per-User Usage Accounting:** Tracks cumulative daily tokens per `user_id` to prevent denial-of-wallet exhaustion.

---

## 4. Circuit Breaker & Reliability Architecture

To prevent cascade failures during external Gemini API rate-limiting or provider degradation:
- **Failure Threshold:** 3 consecutive failures transitions circuit state from `CLOSED` to `OPEN`.
- **Open Behavior:** Requests fail fast with `HTTP 503 Service Unavailable` (`CIRCUIT_BREAKER_OPEN`), preserving backend threads and database connections.
- **Reset Cooldown:** 60.0 seconds cooldown before transitioning to `HALF_OPEN`. A single successful probe transitions back to `CLOSED`.

---

## 5. Persistent AI Audit Logging (`public.agent_runs` & `public.agent_actions`)

Every Command Centre interaction generates persistent telemetry records:
- **`public.agent_runs`:** Records `(id, user_id, session_id, prompt_summary, status, total_tokens, latency_ms, estimated_cost_usd)`.
- **`public.agent_actions`:** Records granular node transitions: `(id, run_id, agent_name, action_type, status, latency_ms)`.
- **Zero Sensitive Content:** Passwords, unmasked PII, and raw API secrets are strictly stripped before audit persistence.

**Gate 7.8 Status:** **PASSED [V-EXEC]**
