"""
MSGI One — API Server Main Entrypoint
FastAPI Modular Monolith Application
Architecture: 7-Layer Architecture (Sommerville Ch. 6, Evans DDD)
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core.config import settings
from src.routers.users import router as users_router
from src.routers.auth import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic AI-Powered Institutional Alumni Ecosystem REST Services",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers ensuring MSGI One Standard Envelope
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats all HTTPExceptions into the MSGI One standard envelope."""
    error_detail = exc.detail
    if isinstance(error_detail, dict):
        code = error_detail.get("code", "ERROR")
        message = error_detail.get("message", "An error occurred.")
        details = error_detail.get("details", [])
    else:
        code = f"HTTP_{exc.status_code}"
        message = str(error_detail)
        details = []

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "data": None,
            "error": {
                "code": code,
                "message": message,
                "details": details,
            },
            "meta": {"path": str(request.url.path)},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic 422 validation errors into MSGI One envelope."""
    errors = []
    for err in exc.errors():
        field_path = " -> ".join([str(loc) for loc in err.get("loc", [])])
        errors.append({"field": field_path, "issue": err.get("msg", "Validation error")})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload failed schema validation.",
                "details": errors,
            },
            "meta": {"path": str(request.url.path)},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Health Check Schemas
class HealthResponseData(BaseModel):
    service: str = "msgi-one-api"
    version: str = "0.1.0"
    environment: str = settings.ENVIRONMENT
    database_status: str = "configured"
    ai_orchestrator_status: str = "ready"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthResponseEnvelope(BaseModel):
    status: str = "success"
    data: HealthResponseData
    error: Any = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@app.get(
    "/health",
    response_model=HealthResponseEnvelope,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Root Service Health Check",
)
@app.get(
    f"{settings.API_V1_STR}/health",
    response_model=HealthResponseEnvelope,
    status_code=status.HTTP_200_OK,
    tags=["System"],
    summary="Versioned Service Health Check",
    description="Returns current service operational status, version, and component health.",
)
def health_check() -> HealthResponseEnvelope:
    """System health check endpoint."""
    return HealthResponseEnvelope(
        status="success",
        data=HealthResponseData(
            service="msgi-one-api",
            version="0.1.0",
            environment=settings.ENVIRONMENT,
            database_status="configured",
            ai_orchestrator_status="ready",
            timestamp=datetime.now(timezone.utc),
        ),
        error=None,
        meta={"phase": "Phase 1 — Application Foundation"},
        timestamp=datetime.now(timezone.utc),
    )


# Mount Versioned API Routers
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)


# Direct /api/v1/me and /api/v1/me/onboard aliases for client convenience
@app.get(
    f"{settings.API_V1_STR}/me",
    tags=["Users & Profiles"],
    summary="Get Current User Profile (Direct Alias)",
    include_in_schema=False,
)
async def direct_get_me(request: Request):
    from src.routers.users import get_my_profile
    from src.core.dependencies import get_current_user
    user = await get_current_user(request.headers.get("Authorization"))
    return await get_my_profile(current_user=user)


@app.patch(
    f"{settings.API_V1_STR}/me",
    tags=["Users & Profiles"],
    summary="Update Current User Profile (Direct Alias)",
    include_in_schema=False,
)
async def direct_patch_me(request: Request):
    from src.routers.users import update_my_profile
    from src.schemas.user import UserUpdateRequest
    from src.core.dependencies import get_current_user
    user = await get_current_user(request.headers.get("Authorization"))
    body = await request.json()
    update_req = UserUpdateRequest(**body)
    return await update_my_profile(update_data=update_req, current_user=user)


@app.get("/", tags=["Root"])
def root():
    """Root redirect / information endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "phase": "Phase 1 — Application Foundation",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
