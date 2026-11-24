# MSGI One — Multi-Provider AI Configuration Guide (Phase 8)

## Supported Providers & Capability Matrix

| Provider | Default Model | Streaming SSE | Tool Calling | Structured JSON | Embeddings (1536-d pgvector) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Google Gemini** (`gemini`) | `gemini-2.5-flash` | Yes | Yes | Yes | Yes (`gemini-embedding-001` / 1536-d L2-norm) |
| **OpenAI** (`openai`) | `gpt-4o-mini` | Yes | Yes | Yes | Yes (1536-d L2-norm) |
| **Anthropic Claude** (`anthropic`) | `claude-3-5-sonnet-latest` | Yes | Yes | Yes | Fallback to Gemini/Deterministic 1536-d |
| **DeepSeek** (`deepseek`) | `deepseek-chat` | Yes | Yes | Yes | Fallback to Gemini/Deterministic 1536-d |
| **Deterministic Engine** | `deterministic-rule-engine` | Yes | Yes | Yes | Yes (reproducible 1536-d L2 projection) |

## Failover, Circuit Breaking & Vector Invariant
- `MultiProviderRouter` routes requests to `is_primary=True`, failing over across `fallback_priority` when upstream providers hit transient `429` or `503` errors or open their circuit breaker.
- Daily & monthly budget caps and RPM limits block overspend cleanly before upstream calls.
- All vector embeddings strictly pass `normalize_l2_vector(..., expected_dim=1536)` to preserve pgvector cosine index geometry (`vector(1536)`).
