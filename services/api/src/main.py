"""
MSGI One — API Server Main Entrypoint
FastAPI Modular Monolith Application
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="MSGI One API",
    description="Agentic AI-Powered Institutional Alumni Ecosystem REST Services",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponseData(BaseModel):
    service: str = "msgi-one-api"
    version: str = "0.1.0"
    environment: str = "development"
    database_status: str = "configured"
    ai_orchestrator_status: str = "ready"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StandardResponse(BaseModel):
    status: str = "success"
    data: HealthResponseData
    error: Any = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@app.get(
    "/api/v1/health",
    response_model=StandardResponse,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Service Health Check",
    description="Returns current service operational status, version, and component health.",
)
async def health_check() -> StandardResponse:
    """System health check endpoint."""
    return StandardResponse(
        status="success",
        data=HealthResponseData(
            service="msgi-one-api",
            version="0.1.0",
            environment="development",
            database_status="configured",
            ai_orchestrator_status="ready",
            timestamp=datetime.now(timezone.utc),
        ),
        error=None,
        meta={"phase": "Phase 0 — Foundation & Architecture Lock"},
        timestamp=datetime.now(timezone.utc),
    )


@app.get("/", tags=["Root"])
async def root():
    """Root redirect / information endpoint."""
    return {
        "project": "MSGI One — Agentic AI-Powered Institutional Alumni Ecosystem",
        "phase": "Phase 0 — Complete",
        "documentation": "/docs",
        "health": "/api/v1/health",
    }
