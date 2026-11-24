"""
MSGI One — Multi-Provider AI Abstraction, Failover Router & Cost Ledger (Phase 8)
Principles:
- Clean Architecture (Martin): Vendor-agnostic inference ports with replaceable adapters.
- AI Engineering (Huyen): Capabilities registry, circuit breaking, retry backoff,
  priority failover, budget enforcement, and uniform usage telemetry ledger.
- Preserves 1536-dim L2-normalized pgvector embedding space invariant.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from src.ai.observability import CircuitBreaker, calculate_request_cost
from src.ai.provider import normalize_l2_vector, sanitize_prompt_for_privacy
from src.ai.vault import (
    ProviderConfigRecord,
    decrypt_provider_key_for_runtime,
    list_provider_configs,
    redact_key_fragments,
    update_verification_status,
)
from src.core.security import SlidingWindowRateLimiter


# Pricing per 1M tokens (USD estimates for institutional budget governance)
PROVIDER_MODEL_PRICING_PER_MILLION: Dict[str, Dict[str, float]] = {
    "gemini": {"input": 0.30, "output": 2.50},
    "openai": {"input": 0.15, "output": 0.60},
    "anthropic": {"input": 3.00, "output": 15.00},
    "deepseek": {"input": 0.27, "output": 1.10},
    "deterministic": {"input": 0.0, "output": 0.0},
}


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: str
    supports_streaming: bool
    supports_tools: bool
    supports_structured_json: bool
    supports_embeddings: bool
    embedding_dimensions: int
    max_context_tokens: int


PROVIDER_CAPABILITIES: Dict[str, ProviderCapabilities] = {
    "gemini": ProviderCapabilities("gemini", True, True, True, True, 1536, 1_000_000),
    "openai": ProviderCapabilities("openai", True, True, True, True, 1536, 128_000),
    "anthropic": ProviderCapabilities("anthropic", True, True, True, False, 1536, 200_000),
    "deepseek": ProviderCapabilities("deepseek", True, True, True, False, 1536, 64_000),
    "deterministic": ProviderCapabilities("deterministic", True, True, True, True, 1536, 16_000),
}


class ClassifiedProviderError(Exception):
    def __init__(self, message: str, error_code: str, retryable: bool = False, status_code: Optional[int] = None):
        super().__init__(redact_key_fragments(message))
        self.error_code = error_code
        self.retryable = retryable
        self.status_code = status_code


class ProviderCompletionResult(BaseModel):
    provider: str
    model_id: str
    content: str
    prompt_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    failover_from: Optional[str] = None


class ProviderHealthResult(BaseModel):
    config_id: str
    provider: str
    model_id: str
    healthy: bool
    status: str  # 'verified', 'failed'
    latency_ms: int
    message: str


class UsageLedgerRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_config_id: Optional[str] = None
    provider: str
    model_id: str
    user_id: Optional[str] = None
    run_id: Optional[str] = None
    prompt_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    status: str = "completed"
    error_code: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


_USAGE_LEDGER_STORE: List[UsageLedgerRecord] = []
_PROVIDER_BREAKERS: Dict[str, CircuitBreaker] = {}
_PROVIDER_RATE_LIMITERS: Dict[str, SlidingWindowRateLimiter] = {}


def clear_multi_provider_state_for_tests() -> None:
    _USAGE_LEDGER_STORE.clear()
    _PROVIDER_BREAKERS.clear()
    _PROVIDER_RATE_LIMITERS.clear()


def estimate_provider_cost_usd(
    provider: str,
    prompt_tokens: int,
    output_tokens: int,
    thinking_tokens: int = 0,
    model_id: str = "",
) -> float:
    if provider == "gemini":
        return calculate_request_cost(
            prompt_tokens=prompt_tokens,
            candidate_tokens=output_tokens,
            thinking_tokens=thinking_tokens,
            model_id=model_id or "gemini-2.5-flash",
        )
    rates = PROVIDER_MODEL_PRICING_PER_MILLION.get(provider, {"input": 0.5, "output": 1.5})
    in_cost = (prompt_tokens / 1_000_000.0) * rates["input"]
    out_cost = ((output_tokens + thinking_tokens) / 1_000_000.0) * rates["output"]
    return round(in_cost + out_cost, 6)


def _classify_http_failure(provider: str, status_code: int, body_text: str) -> ClassifiedProviderError:
    safe_body = redact_key_fragments(body_text[:240])
    if status_code in (401, 403):
        return ClassifiedProviderError(
            f"{provider} authentication rejected ({status_code}): {safe_body}",
            error_code="PROVIDER_AUTH_ERROR",
            retryable=False,
            status_code=status_code,
        )
    if status_code == 429:
        return ClassifiedProviderError(
            f"{provider} rate limit / quota exceeded (429): {safe_body}",
            error_code="PROVIDER_RATE_LIMIT",
            retryable=True,
            status_code=429,
        )
    if status_code >= 500:
        return ClassifiedProviderError(
            f"{provider} upstream unavailable ({status_code}): {safe_body}",
            error_code="PROVIDER_SERVER_ERROR",
            retryable=True,
            status_code=status_code,
        )
    return ClassifiedProviderError(
        f"{provider} request error ({status_code}): {safe_body}",
        error_code="PROVIDER_BAD_REQUEST",
        retryable=False,
        status_code=status_code,
    )


class BaseProviderAdapter(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def complete(
        self,
        *,
        api_key: str,
        model_id: str,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ProviderCompletionResult:
        pass

    async def stream(
        self,
        *,
        api_key: str,
        model_id: str,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> AsyncIterator[str]:
        res = await self.complete(
            api_key=api_key,
            model_id=model_id,
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            http_client=http_client,
        )
        words = res.content.split(" ")
        for idx, w in enumerate(words):
            yield w if idx == 0 else f" {w}"

    @abstractmethod
    async def health_check(
        self,
        *,
        api_key: str,
        model_id: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Tuple[bool, str]:
        pass


from typing import Tuple


class OpenAICompatibleAdapter(BaseProviderAdapter):
    """Shared async HTTP adapter for OpenAI and DeepSeek chat-completions APIs."""

    def __init__(self, provider_name: str, base_url: str, default_model: str):
        self.provider_name = provider_name
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    async def complete(
        self,
        *,
        api_key: str,
        model_id: str,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ProviderCompletionResult:
        t0 = time.perf_counter()
        sanitized_prompt = sanitize_prompt_for_privacy(prompt)
        target_model = model_id or self.default_model
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": sanitized_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(timeout=20.0)
        try:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            if resp.status_code >= 400:
                raise _classify_http_failure(self.provider_name, resp.status_code, resp.text)
            body = resp.json()
            text = (body.get("choices") or [{}])[0].get("message", {}).get("content", "")
            usage = body.get("usage") or {}
            p_tok = int(usage.get("prompt_tokens") or max(len(sanitized_prompt.split()) * 2, 10))
            o_tok = int(usage.get("completion_tokens") or max(len(text.split()) * 2, 10))
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return ProviderCompletionResult(
                provider=self.provider_name,
                model_id=target_model,
                content=text,
                prompt_tokens=p_tok,
                output_tokens=o_tok,
                total_tokens=p_tok + o_tok,
                estimated_cost_usd=estimate_provider_cost_usd(self.provider_name, p_tok, o_tok, 0, target_model),
                latency_ms=elapsed_ms,
            )
        except httpx.TimeoutException as exc:
            raise ClassifiedProviderError(
                f"{self.provider_name} timed out: {exc}",
                error_code="PROVIDER_TIMEOUT",
                retryable=True,
                status_code=504,
            ) from exc
        finally:
            if owns_client:
                await client.aclose()

    async def health_check(
        self,
        *,
        api_key: str,
        model_id: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Tuple[bool, str]:
        headers = {"Authorization": f"Bearer {api_key}"}
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(timeout=10.0)
        try:
            resp = await client.get(f"{self.base_url}/models", headers=headers)
            if resp.status_code >= 400:
                err = _classify_http_failure(self.provider_name, resp.status_code, resp.text)
                return False, str(err)
            return True, f"{self.provider_name} endpoint verified ({model_id})."
        except Exception as exc:
            return False, redact_key_fragments(f"{self.provider_name} connection error: {exc}")
        finally:
            if owns_client:
                await client.aclose()


class AnthropicAdapter(BaseProviderAdapter):
    """Official Anthropic Messages API HTTP adapter."""
    provider_name = "anthropic"
    base_url = "https://api.anthropic.com/v1"

    async def complete(
        self,
        *,
        api_key: str,
        model_id: str,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ProviderCompletionResult:
        t0 = time.perf_counter()
        sanitized_prompt = sanitize_prompt_for_privacy(prompt)
        target_model = model_id or "claude-3-5-sonnet-latest"
        payload = {
            "model": target_model,
            "system": system_instruction,
            "messages": [{"role": "user", "content": sanitized_prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(timeout=20.0)
        try:
            resp = await client.post(f"{self.base_url}/messages", json=payload, headers=headers)
            if resp.status_code >= 400:
                raise _classify_http_failure("anthropic", resp.status_code, resp.text)
            body = resp.json()
            blocks = body.get("content") or []
            text = "".join(b.get("text", "") for b in blocks if isinstance(b, dict))
            usage = body.get("usage") or {}
            p_tok = int(usage.get("input_tokens") or max(len(sanitized_prompt.split()) * 2, 10))
            o_tok = int(usage.get("output_tokens") or max(len(text.split()) * 2, 10))
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return ProviderCompletionResult(
                provider="anthropic",
                model_id=target_model,
                content=text,
                prompt_tokens=p_tok,
                output_tokens=o_tok,
                total_tokens=p_tok + o_tok,
                estimated_cost_usd=estimate_provider_cost_usd("anthropic", p_tok, o_tok, 0, target_model),
                latency_ms=elapsed_ms,
            )
        except httpx.TimeoutException as exc:
            raise ClassifiedProviderError(
                f"anthropic timed out: {exc}",
                error_code="PROVIDER_TIMEOUT",
                retryable=True,
                status_code=504,
            ) from exc
        finally:
            if owns_client:
                await client.aclose()

    async def health_check(
        self,
        *,
        api_key: str,
        model_id: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Tuple[bool, str]:
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(timeout=10.0)
        try:
            resp = await client.get(f"{self.base_url}/models", headers=headers)
            if resp.status_code >= 400:
                err = _classify_http_failure("anthropic", resp.status_code, resp.text)
                return False, str(err)
            return True, f"Anthropic endpoint verified ({model_id})."
        except Exception as exc:
            return False, redact_key_fragments(f"anthropic connection error: {exc}")
        finally:
            if owns_client:
                await client.aclose()


class GeminiHTTPAdapter(BaseProviderAdapter):
    """Gemini REST/SDK adapter supporting explicit per-request vault keys."""
    provider_name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def complete(
        self,
        *,
        api_key: str,
        model_id: str,
        prompt: str,
        system_instruction: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> ProviderCompletionResult:
        t0 = time.perf_counter()
        sanitized_prompt = sanitize_prompt_for_privacy(prompt)
        target_model = model_id or "gemini-2.5-flash"
        url = f"{self.base_url}/models/{target_model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": sanitized_prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(timeout=20.0)
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code >= 400:
                raise _classify_http_failure("gemini", resp.status_code, resp.text)
            body = resp.json()
            candidates = body.get("candidates") or [{}]
            parts = ((candidates[0].get("content") or {}).get("parts")) or []
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
            usage = body.get("usageMetadata") or {}
            p_tok = int(usage.get("promptTokenCount") or max(len(sanitized_prompt.split()) * 2, 10))
            o_tok = int(usage.get("candidatesTokenCount") or max(len(text.split()) * 2, 10))
            t_tok = int(usage.get("thoughtsTokenCount") or 0)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            return ProviderCompletionResult(
                provider="gemini",
                model_id=target_model,
                content=text,
                prompt_tokens=p_tok,
                output_tokens=o_tok,
                thinking_tokens=t_tok,
                total_tokens=p_tok + o_tok + t_tok,
                estimated_cost_usd=estimate_provider_cost_usd("gemini", p_tok, o_tok, t_tok, target_model),
                latency_ms=elapsed_ms,
            )
        except httpx.TimeoutException as exc:
            raise ClassifiedProviderError(
                f"gemini timed out: {exc}",
                error_code="PROVIDER_TIMEOUT",
                retryable=True,
                status_code=504,
            ) from exc
        finally:
            if owns_client:
                await client.aclose()

    async def health_check(
        self,
        *,
        api_key: str,
        model_id: str,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> Tuple[bool, str]:
        url = f"{self.base_url}/models/{model_id or 'gemini-2.5-flash'}"
        headers = {"x-goog-api-key": api_key}
        owns_client = http_client is None
        client = http_client or httpx.AsyncClient(timeout=10.0)
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code >= 400:
                err = _classify_http_failure("gemini", resp.status_code, resp.text)
                return False, str(err)
            return True, f"Gemini model verified ({model_id})."
        except Exception as exc:
            return False, redact_key_fragments(f"gemini connection error: {exc}")
        finally:
            if owns_client:
                await client.aclose()


_ADAPTERS: Dict[str, BaseProviderAdapter] = {
    "gemini": GeminiHTTPAdapter(),
    "openai": OpenAICompatibleAdapter("openai", "https://api.openai.com/v1", "gpt-4o-mini"),
    "anthropic": AnthropicAdapter(),
    "deepseek": OpenAICompatibleAdapter("deepseek", "https://api.deepseek.com", "deepseek-chat"),
}


def get_provider_adapter(provider: str) -> BaseProviderAdapter:
    if provider not in _ADAPTERS:
        raise ValueError(f"No adapter registered for provider '{provider}'.")
    return _ADAPTERS[provider]


def _get_breaker(config_id: str) -> CircuitBreaker:
    if config_id not in _PROVIDER_BREAKERS:
        _PROVIDER_BREAKERS[config_id] = CircuitBreaker(failure_threshold=2, reset_timeout=30.0)
    return _PROVIDER_BREAKERS[config_id]


def _current_spend_for_config(config_id: str) -> Tuple[float, float]:
    now_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_month = datetime.now(timezone.utc).strftime("%Y-%m")
    daily = 0.0
    monthly = 0.0
    for rec in _USAGE_LEDGER_STORE:
        if rec.provider_config_id == config_id and rec.status == "completed":
            if rec.created_at.startswith(now_month):
                monthly += rec.estimated_cost_usd
            if rec.created_at.startswith(now_day):
                daily += rec.estimated_cost_usd
    return round(daily, 6), round(monthly, 6)


def record_usage_ledger(entry: UsageLedgerRecord) -> UsageLedgerRecord:
    _USAGE_LEDGER_STORE.append(entry)
    return entry


def get_usage_summary() -> Dict[str, Any]:
    by_provider: Dict[str, Dict[str, Any]] = {}
    total_cost = 0.0
    total_tokens = 0
    total_requests = len(_USAGE_LEDGER_STORE)
    failed_requests = 0

    for rec in _USAGE_LEDGER_STORE:
        total_cost += rec.estimated_cost_usd
        total_tokens += rec.total_tokens
        if rec.status != "completed":
            failed_requests += 1
        bucket = by_provider.setdefault(
            rec.provider,
            {"provider": rec.provider, "requests": 0, "failures": 0, "total_tokens": 0, "total_cost_usd": 0.0},
        )
        bucket["requests"] += 1
        if rec.status != "completed":
            bucket["failures"] += 1
        bucket["total_tokens"] += rec.total_tokens
        bucket["total_cost_usd"] = round(bucket["total_cost_usd"] + rec.estimated_cost_usd, 6)

    return {
        "total_requests": total_requests,
        "failed_requests": failed_requests,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 6),
        "by_provider": list(by_provider.values()),
        "recent_entries": [r.model_dump() for r in reversed(_USAGE_LEDGER_STORE[-50:])],
    }


async def verify_vault_provider(
    config: ProviderConfigRecord,
    http_client: Optional[httpx.AsyncClient] = None,
    master_key: Optional[str] = None,
) -> ProviderHealthResult:
    t0 = time.perf_counter()
    adapter = get_provider_adapter(config.provider)
    try:
        api_key = decrypt_provider_key_for_runtime(config, master_key=master_key)
        healthy, msg = await adapter.health_check(api_key=api_key, model_id=config.model_id, http_client=http_client)
    except Exception as exc:
        healthy = False
        msg = redact_key_fragments(str(exc))
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    status_val = "verified" if healthy else "failed"
    update_verification_status(config.id, status_val, None if healthy else msg)
    return ProviderHealthResult(
        config_id=config.id,
        provider=config.provider,
        model_id=config.model_id,
        healthy=healthy,
        status=status_val,
        latency_ms=elapsed_ms,
        message=msg,
    )


async def execute_with_failover(
    *,
    prompt: str,
    system_instruction: str,
    user_id: Optional[str] = None,
    run_id: Optional[str] = None,
    preferred_config_id: Optional[str] = None,
    http_client: Optional[httpx.AsyncClient] = None,
    master_key: Optional[str] = None,
    max_retries_per_provider: int = 1,
) -> ProviderCompletionResult:
    """
    Executes LLM completion across admin-configured providers in priority order
    with RPM limiting, budget checks, circuit breaking, bounded backoff, and ledger recording.
    """
    # Prioritize live vault providers over deterministic fallback regardless of AI_PROVIDER env.
    configs = list_provider_configs(include_disabled=False)
    deterministic_configs = [c for c in configs if c.provider == "deterministic"]
    non_deterministic = [c for c in configs if c.provider != "deterministic"]
    if non_deterministic:
        configs = non_deterministic + deterministic_configs
    else:
        configs = deterministic_configs
    if preferred_config_id:
        configs.sort(key=lambda c: (0 if c.id == preferred_config_id else 1, 0 if c.is_primary else 1, c.fallback_priority))

    first_failed_provider: Optional[str] = None
    last_error: Optional[str] = None

    for cfg in configs:
        breaker = _get_breaker(cfg.id)
        if not breaker.can_execute():
            first_failed_provider = first_failed_provider or cfg.provider
            last_error = f"Circuit breaker open for {cfg.provider}"
            continue

        # Budget enforcement
        daily_spend, monthly_spend = _current_spend_for_config(cfg.id)
        if cfg.daily_budget_usd is not None and daily_spend >= cfg.daily_budget_usd:
            first_failed_provider = first_failed_provider or cfg.provider
            last_error = "PROVIDER_DAILY_BUDGET_EXCEEDED"
            record_usage_ledger(
                UsageLedgerRecord(
                    provider_config_id=cfg.id,
                    provider=cfg.provider,
                    model_id=cfg.model_id,
                    user_id=user_id,
                    run_id=run_id,
                    status="budget_blocked",
                    error_code="PROVIDER_DAILY_BUDGET_EXCEEDED",
                )
            )
            continue
        if cfg.monthly_budget_usd is not None and monthly_spend >= cfg.monthly_budget_usd:
            first_failed_provider = first_failed_provider or cfg.provider
            last_error = "PROVIDER_MONTHLY_BUDGET_EXCEEDED"
            record_usage_ledger(
                UsageLedgerRecord(
                    provider_config_id=cfg.id,
                    provider=cfg.provider,
                    model_id=cfg.model_id,
                    user_id=user_id,
                    run_id=run_id,
                    status="budget_blocked",
                    error_code="PROVIDER_MONTHLY_BUDGET_EXCEEDED",
                )
            )
            continue

        # Per-provider RPM check
        rpm = cfg.requests_per_minute_limit or 60
        limiter = _PROVIDER_RATE_LIMITERS.get(cfg.id)
        if limiter is None or limiter.max_requests != rpm:
            limiter = SlidingWindowRateLimiter(max_requests=rpm, window_seconds=60)
            _PROVIDER_RATE_LIMITERS[cfg.id] = limiter
        if not limiter.check(f"provider:{cfg.id}"):
            first_failed_provider = first_failed_provider or cfg.provider
            last_error = "PROVIDER_RPM_LIMIT"
            continue

        adapter = get_provider_adapter(cfg.provider)
        api_key = decrypt_provider_key_for_runtime(cfg, master_key=master_key)

        for attempt in range(max_retries_per_provider + 1):
            try:
                res = await adapter.complete(
                    api_key=api_key,
                    model_id=cfg.model_id,
                    prompt=prompt,
                    system_instruction=system_instruction,
                    http_client=http_client,
                )
                breaker.record_success()
                res.failover_from = first_failed_provider
                record_usage_ledger(
                    UsageLedgerRecord(
                        provider_config_id=cfg.id,
                        provider=cfg.provider,
                        model_id=res.model_id,
                        user_id=user_id,
                        run_id=run_id,
                        prompt_tokens=res.prompt_tokens,
                        output_tokens=res.output_tokens,
                        thinking_tokens=res.thinking_tokens,
                        total_tokens=res.total_tokens,
                        estimated_cost_usd=res.estimated_cost_usd,
                        latency_ms=res.latency_ms,
                        status="completed",
                    )
                )
                return res
            except ClassifiedProviderError as exc:
                last_error = exc.error_code
                record_usage_ledger(
                    UsageLedgerRecord(
                        provider_config_id=cfg.id,
                        provider=cfg.provider,
                        model_id=cfg.model_id,
                        user_id=user_id,
                        run_id=run_id,
                        status="failed",
                        error_code=exc.error_code,
                    )
                )
                if exc.retryable and attempt < max_retries_per_provider:
                    await asyncio.sleep(0.02 * (2 ** attempt))
                    continue
                breaker.record_failure()
                first_failed_provider = first_failed_provider or cfg.provider
                break

    raise ClassifiedProviderError(
        last_error or "No enabled AI provider available.",
        error_code=last_error or "NO_PROVIDER_AVAILABLE",
        retryable=False,
        status_code=503,
    )


def ensure_pgvector_1536(vector: List[float]) -> List[float]:
    """Enforces 1536-dimensional L2-normalized invariant regardless of embedding provider."""
    return normalize_l2_vector(vector, expected_dim=1536)
