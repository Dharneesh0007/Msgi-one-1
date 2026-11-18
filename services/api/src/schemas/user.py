"""
MSGI One — User & API Response Pydantic v2 Schemas
Adheres strictly to the MSGI One Standard API Envelope and docs/API_CONTRACT.md.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ApiErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ApiError(BaseModel):
    code: str
    message: str
    details: List[ApiErrorDetail] = Field(default_factory=list)


class StandardEnvelope(BaseModel, Generic[T]):
    """MSGI One Standard API Envelope."""
    status: str = "success"
    data: Optional[T] = None
    error: Optional[ApiError] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserPreferencesSchema(BaseModel):
    theme: str = "system"
    push_notifications_enabled: bool = True
    email_digests_enabled: bool = True

    model_config = ConfigDict(from_attributes=True)


class StudentProfileSummary(BaseModel):
    roll_number: Optional[str] = None
    enrollment_year: Optional[int] = None
    expected_graduation_year: Optional[int] = None
    department: Optional[str] = None
    degree_program: Optional[str] = None
    career_interests: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AlumniProfileSummary(BaseModel):
    graduation_year: Optional[int] = None
    degree: Optional[str] = None
    major: Optional[str] = None
    headline: Optional[str] = None
    bio: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    industry: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    """Current authenticated user detailed profile response."""
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    requested_role: str = "student"
    is_verified: bool = False
    is_active: bool = True
    roles: List[str] = Field(default_factory=list)
    preferences: UserPreferencesSchema = Field(default_factory=UserPreferencesSchema)
    student_profile: Optional[StudentProfileSummary] = None
    alumni_profile: Optional[AlumniProfileSummary] = None
    is_profile_complete: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """
    Fields that an authenticated user is permitted to update for themselves.
    CRITICAL: Does NOT allow updating roles, is_verified, or is_admin!
    """
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    preferences: Optional[UserPreferencesSchema] = None

    model_config = ConfigDict(extra="forbid")


class UserOnboardingRequest(BaseModel):
    """Initial profile onboarding request submitted when user completes profile."""
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    requested_role: Optional[str] = Field(default="student")
    department: Optional[str] = Field(default=None, max_length=100)
    graduation_year: Optional[int] = Field(default=None, ge=1950, le=2035)

    model_config = ConfigDict(extra="forbid")


class PublicUserProfileResponse(BaseModel):
    """
    Public directory profile response.
    Masks private contact info (email, phone, CGPA) in compliance with FERPA/GDPR.
    """
    id: str
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    is_verified: bool = False
    headline: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
