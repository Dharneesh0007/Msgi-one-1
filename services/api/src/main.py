"""
MSGI One — API Server Main Entrypoint
FastAPI Modular Monolith Application
Architecture: 7-Layer Architecture (Sommerville Ch. 6, Evans DDD)
"""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.dependencies import get_current_user
from src.schemas.user import UserUpdateRequest, UserOnboardingRequest
from src.routers.users import router as users_router
from src.routers.auth import router as auth_router
from src.routers.alumni import router as alumni_router
from src.routers.jobs import router as jobs_router
from src.routers.mentors import router as mentors_router
from src.routers.events import router as events_router
from src.routers.global_connect import router as global_router
from src.routers.ai import router as ai_router
from src.routers.learning import router as learning_router
from src.routers.communities import router as communities_router
from src.routers.admin import router as admin_router
from src.routers.notifications import router as notifications_router
from src.routers.extended import router as extended_router
from src.routers.verifications import router as verifications_router
from src.routers.scheduling import router as scheduling_router
from src.routers.messaging import router as messaging_router
from src.routers.ws_chat import router as ws_chat_router
from src.routers.rooms import router as rooms_router

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


# Normalization Middleware for Client Build Compatibility
@app.middleware("http")
async def normalize_api_v1_prefix_middleware(request: Request, call_next):
    """
    Seamlessly normalizes double-prefixed paths (e.g. /api/v1/api/v1/alumni -> /api/v1/alumni)
    arising when clients configured with base URL 'https://host/api/v1' invoke '/api/v1/...'.
    Ensures zero disruption to frozen Android baseline builds.
    """
    path = request.scope.get("path", "")
    if path.startswith("/api/v1/api/v1/"):
        request.scope["path"] = path[7:]  # strips '/api/v1' leaving '/api/v1/...'
        if "raw_path" in request.scope:
            request.scope["raw_path"] = request.scope["path"].encode("ascii")
    elif path == "/api/v1/api/v1":
        request.scope["path"] = "/api/v1"
        if "raw_path" in request.scope:
            request.scope["raw_path"] = request.scope["path"].encode("ascii")
    return await call_next(request)


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
        meta={"phase": "Phase 4 — Extended MVP, Realtime and Android Release Preparation"},
        timestamp=datetime.now(timezone.utc),
    )


# Mount Versioned API Routers across both /api/v1 and /api/v1/api/v1 prefixes
# to ensure zero disruption for frozen client builds.
API_PREFIXES = [settings.API_V1_STR, f"{settings.API_V1_STR}{settings.API_V1_STR}"]

for pfx in API_PREFIXES:
    is_primary = (pfx == settings.API_V1_STR)
    app.include_router(users_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(auth_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(alumni_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(jobs_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(mentors_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(events_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(global_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(ai_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(learning_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(communities_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(admin_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(notifications_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(extended_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(verifications_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(scheduling_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(messaging_router, prefix=pfx, include_in_schema=is_primary)
    app.include_router(rooms_router, prefix=pfx, include_in_schema=is_primary)

# Real-time WebSocket endpoint (/ws/chat)
app.include_router(ws_chat_router)


# Direct /me and convenience aliases for primary prefix (/api/v1) and double prefix (/api/v1/api/v1)
@app.get(f"{settings.API_V1_STR}/me", tags=["Users & Profiles"], summary="Get Current User Profile (Direct Alias)")
@app.get(f"{settings.API_V1_STR}{settings.API_V1_STR}/me", tags=["Users & Profiles"], include_in_schema=False)
def direct_get_me(current_user=Depends(get_current_user)):
    from src.routers.users import get_my_profile
    return get_my_profile(current_user=current_user)


@app.patch(f"{settings.API_V1_STR}/me", tags=["Users & Profiles"], summary="Update Current User Profile (Direct Alias)")
@app.patch(f"{settings.API_V1_STR}{settings.API_V1_STR}/me", tags=["Users & Profiles"], include_in_schema=False)
def direct_patch_me(update_data: UserUpdateRequest, current_user=Depends(get_current_user)):
    from src.routers.users import update_my_profile
    return update_my_profile(update_data=update_data, current_user=current_user)


@app.post(f"{settings.API_V1_STR}/me/onboard", tags=["Users & Profiles"], summary="Complete Profile Onboarding (Direct Alias)")
@app.post(f"{settings.API_V1_STR}{settings.API_V1_STR}/me/onboard", tags=["Users & Profiles"], include_in_schema=False)
def direct_onboard_me(onboarding_data: UserOnboardingRequest, current_user=Depends(get_current_user)):
    from src.routers.users import complete_onboarding
    return complete_onboarding(onboarding_data=onboarding_data, current_user=current_user)


@app.get(f"{settings.API_V1_STR}/me/learning", tags=["Learning Academy"], summary="Get My Learning Registrations (Direct Alias)")
@app.get(f"{settings.API_V1_STR}{settings.API_V1_STR}/me/learning", tags=["Learning Academy"], include_in_schema=False)
def direct_get_my_learning(current_user=Depends(get_current_user)):
    from src.services.learning_service import get_my_learning
    from src.schemas.user import StandardEnvelope
    items = get_my_learning(user=current_user)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@app.get(f"{settings.API_V1_STR}/me/communities", tags=["Communities & Groups"], summary="Get My Community Memberships (Direct Alias)")
@app.get(f"{settings.API_V1_STR}{settings.API_V1_STR}/me/communities", tags=["Communities & Groups"], include_in_schema=False)
def direct_get_my_communities(current_user=Depends(get_current_user)):
    from src.services.community_service import get_my_communities
    from src.schemas.user import StandardEnvelope
    items = get_my_communities(user=current_user)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@app.get(f"{settings.API_V1_STR}/me/notifications", tags=["Notifications"], summary="Get My Notifications (Direct Alias)")
@app.get(f"{settings.API_V1_STR}{settings.API_V1_STR}/me/notifications", tags=["Notifications"], include_in_schema=False)
def direct_get_my_notifications(current_user=Depends(get_current_user)):
    from src.services.notifications_service import get_my_notifications
    from src.schemas.user import StandardEnvelope
    items = get_my_notifications(user=current_user)
    return StandardEnvelope(status="success", data=items, timestamp=datetime.now(timezone.utc))


@app.get("/", tags=["Root"])
def root():
    """Root redirect / information endpoint."""
    return {
        "project": settings.PROJECT_NAME,
        "phase": "Phase 4 — Extended MVP, Realtime and Android Release Preparation",
        "documentation": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
