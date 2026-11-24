"""
MSGI One — Reproducible Phase 10 Latency & Throughput Benchmark Script
Measures local ASGI FastAPI + SQLAlchemy / In-Memory Domain Service / AES-256-GCM /
Scheduling / Messaging / AI Orchestration latencies without fabricated external numbers.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient
from src.main import app
from src.core.dependencies import AuthenticatedUser, get_current_user
from src.ai.vault import encrypt_api_key, decrypt_api_key


BENCH_USER = AuthenticatedUser(
    id="user-bench-001",
    email="bench.student@example.msgi.edu",
    first_name="Bench",
    last_name="Runner",
    roles=["student"],
    is_verified=True,
)


def measure_ms(label: str, fn, iterations: int = 25):
    samples = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    samples_sorted = sorted(samples)
    p95_idx = min(len(samples_sorted) - 1, max(0, int(0.95 * len(samples_sorted)) - 1))
    return {
        "operation": label,
        "iterations": iterations,
        "min_ms": round(samples_sorted[0], 2),
        "mean_ms": round(statistics.mean(samples), 2),
        "p50_ms": round(statistics.median(samples), 2),
        "p95_ms": round(samples_sorted[p95_idx], 2),
        "max_ms": round(samples_sorted[-1], 2),
    }


def main():
    app.dependency_overrides[get_current_user] = lambda: BENCH_USER
    client = TestClient(app)

    results = [
        measure_ms("GET /api/v1/health", lambda: client.get("/api/v1/health")),
        measure_ms("GET /api/v1/ready", lambda: client.get("/api/v1/ready")),
        measure_ms("GET /api/v1/alumni?country=Japan", lambda: client.get("/api/v1/alumni?country=Japan")),
        measure_ms(
            "GET /api/v1/scheduling/availability/user-kenji-001",
            lambda: client.get("/api/v1/scheduling/availability/user-kenji-001?days_ahead=7"),
        ),
        measure_ms(
            "POST /api/v1/ai/chat (deterministic orchestration)",
            lambda: client.post("/api/v1/ai/chat", json={"prompt": "Analyze my skill gap for AI Engineer"}),
            iterations=10,
        ),
        measure_ms(
            "AES-256-GCM Vault encrypt+decrypt",
            lambda: decrypt_api_key(
                *encrypt_api_key("sk-bench-key-12345678", "openai", "bench", 1, "bench-master")[:2],
                "openai",
                "bench",
                1,
                "bench-master",
            ),
            iterations=50,
        ),
    ]

    app.dependency_overrides.clear()
    print(json.dumps({"environment": "local-in-process-asgi", "benchmarks": results}, indent=2))


if __name__ == "__main__":
    main()
