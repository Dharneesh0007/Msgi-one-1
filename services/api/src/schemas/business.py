"""
MSGI One — Phase 2 Business Module Pydantic v2 Schemas
Covers: Alumni Network, CareerBridge, MentorMatch, Events, and Global Connect.
Enforces strict validation, standard envelopes, and FERPA/GDPR compliance.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# =====================================================================
# 1. ALUMNI NETWORK SCHEMAS
# =====================================================================

class AlumniDirectoryItem(BaseModel):
    """Privacy-safe directory listing item."""
    id: str
    user_id: str
    full_name: str
    avatar_url: Optional[str] = None
    graduation_year: int
    degree: str
    major: str
    headline: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    is_verified: bool = True
    mentor_opt_in: bool = False


class AlumniDetailResponse(AlumniDirectoryItem):
    """Detailed profile view without exposing private contact info."""
    bio: Optional[str] = None
    advisory_topics: List[str] = Field(default_factory=list)
    linkedin_slug: Optional[str] = None


# =====================================================================
# 2. CAREERBRIDGE (JOBS & APPLICATIONS) SCHEMAS
# =====================================================================

class SkillOverlapResult(BaseModel):
    """Deterministic skill match analysis."""
    match_percentage: int
    matched_skills: List[str]
    missing_skills: List[str]


class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    location: str
    country: str
    opportunity_type: str  # full_time, internship, contract, part_time
    workplace_type: str    # remote, hybrid, onsite
    description: str
    requirements: List[str]
    required_skills: List[str]
    application_deadline: Optional[datetime] = None
    is_active: bool
    is_verified_listing: bool
    alumni_referral_available: bool = False
    alumni_count_at_company: int = 0
    skill_overlap: Optional[SkillOverlapResult] = None
    created_at: datetime


class JobCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=3, max_length=255)
    company: str = Field(..., min_length=2, max_length=255)
    location: str = Field(..., min_length=2, max_length=255)
    country: str = Field(default="Global")
    opportunity_type: str = Field(default="full_time")
    workplace_type: str = Field(default="hybrid")
    description: str = Field(..., min_length=20)
    requirements: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    application_deadline: Optional[datetime] = None


class JobApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resume_url: Optional[str] = None
    cover_note: Optional[str] = Field(None, max_length=2000)


class JobApplicationResponse(BaseModel):
    id: str
    job_id: str
    job_title: str
    company: str
    applicant_id: str
    status: str  # submitted, under_review, interviewing, accepted, rejected, withdrawn
    cover_note: Optional[str] = None
    submitted_at: datetime


# =====================================================================
# 3. MENTORMATCH SCHEMAS
# =====================================================================

class MentorProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    headline: str
    current_company: str
    current_title: str
    country: str
    advisory_topics: List[str]
    is_accepting_requests: bool
    max_active_mentees: int
    current_active_mentees: int
    available_slots: int
    match_score: Optional[int] = None  # Deterministic score based on student career goal


class MentorRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mentor_id: str
    topic: str = Field(..., min_length=2, max_length=100)
    career_goal: str = Field(..., min_length=5, max_length=500)
    message: Optional[str] = Field(None, max_length=1000)


class MentorRequestStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str = Field(..., pattern="^(accepted|rejected|completed|cancelled|clarification_requested)$")
    mentor_notes: Optional[str] = Field(None, max_length=1000)


class MentorRequestResponse(BaseModel):
    id: str
    mentor_id: str
    mentor_name: str
    mentor_company: str
    student_id: str
    student_name: str
    topic: str
    career_goal: str
    message: Optional[str] = None
    status: str  # pending, accepted, rejected, completed, cancelled
    mentor_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# =====================================================================
# 4. EVENTS AND REUNIONS SCHEMAS
# =====================================================================

class EventResponse(BaseModel):
    id: str
    title: str
    event_type: str  # webinar, reunion, workshop, career_fair, conference
    description: str
    location: str
    is_virtual: bool
    meeting_url: Optional[str] = None
    start_time: datetime
    end_time: datetime
    max_capacity: int
    current_registrations: int
    available_seats: int
    is_published: bool
    is_registered: bool = False
    organizer_name: str


class EventCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(..., min_length=3, max_length=255)
    event_type: str = Field(default="webinar")
    description: str = Field(..., min_length=10)
    location: str = Field(..., min_length=2, max_length=255)
    is_virtual: bool = True
    meeting_url: Optional[str] = None
    start_time: datetime
    end_time: datetime
    max_capacity: int = Field(default=100, gt=0)


class EventRegistrationResponse(BaseModel):
    id: str
    event_id: str
    event_title: str
    user_id: str
    status: str  # confirmed, attended, cancelled
    ticket_code: str
    registered_at: datetime


# =====================================================================
# 5. GLOBAL ALUMNI CONNECT SCHEMAS (P1)
# =====================================================================

class LocationAggregationItem(BaseModel):
    """Aggregated regional count; suppresses counts < 3 for privacy."""
    country: str
    city: str
    alumni_count: int
    is_active_chapter: bool = False


class ChapterResponse(BaseModel):
    id: str
    name: str
    city: str
    country: str
    region: str
    lead_alumni_name: Optional[str] = None
    description: Optional[str] = None
    member_count: int = 0
