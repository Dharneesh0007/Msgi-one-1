"""
MSGI One — Phase 4 Extended Schemas
Typed Request & Response Models for Learning Academy, Communities, Admin, Projects, Startups & Impact.
Principles: Pydantic v2 & API Contract Synchronization.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# MODULE 9: LEARNING ACADEMY
class EnrollmentRequest(BaseModel):
    resource_id: str = Field(..., description="Unique courseware resource ID")


class ProgressUpdateRequest(BaseModel):
    progress_percentage: int = Field(..., ge=0, le=100, description="Completed progress between 0 and 100")


# MODULE 10: COMMUNITIES
class MembershipUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(active|rejected)$", description="Approved or rejected status")


# MODULE 12: ADMIN
class VerificationDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$", description="Decision: 'approved' or 'rejected'")
    review_notes: Optional[str] = Field(None, max_length=500, description="Audit review rationale")


# MODULE 8: STARTUPS
class StartupConnectionRequest(BaseModel):
    intent: str = Field("mentorship", description="Intent: 'mentorship', 'talent', or 'collaboration'")
    message: str = Field(..., min_length=5, max_length=1000, description="Introductory message to founder")


# MODULE 11: IMPACT
class VolunteerInterestRequest(BaseModel):
    interest_note: str = Field(..., min_length=5, max_length=1000, description="Volunteering availability and focus")
