"""
MSGI One — Declarative SQLAlchemy 2.0 Unified Models Registry
Exports all 55 application models spanning Phases 1 through 4 + Phase 2 Enterprise Ecosystem.
Guarantees clean metadata registration for migrations, reflection, and repository queries.
"""

from src.db.models.base import Base

# Phase 1: Identity, Auth & Profiles (13 models)
from src.db.models.user import (
    Role,
    User,
    UserRole,
    AlumniProfile,
    StudentProfile,
    FacultyProfile,
    RecruiterProfile,
    UserPreference,
    ConsentRecord,
    AlumniLocation,
    Skill,
    UserSkill,
    AuditLog,
)

# Phase 2: Core Business Modules (7 models)
from src.db.models.core import (
    MentorProfile,
    MentorRequest,
    Job,
    JobApplication,
    Event,
    EventRegistration,
    AlumniChapter,
)

# Phase 3: AI Intelligence & Audit Trail (6 models)
from src.db.models.ai import (
    CareerRoleSkill,
    LearningResource,
    StudentSkill,
    AgentRun,
    AgentAction,
    ApprovalRequest,
)

# Phase 4: Extended MVP Modules & Realtime Notifications (12 models)
from src.db.models.extended import (
    CourseEnrollment,
    Community,
    CommunityMembership,
    VerificationRequest,
    AdminAuditLog,
    Project,
    ProjectMember,
    Startup,
    StartupConnectionRequest,
    ImpactProgramme,
    VolunteerInterest,
    Notification,
)

# V2 Phase 2: Enterprise Scheduling, Messaging, WebRTC Rooms, AI Vault, Push, Outbox, Idempotency (17 models)
from src.db.models.enterprise import (
    AlumniAvailability,
    MeetingRequest,
    MeetingSlot,
    Meeting,
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    UserBlock,
    UserReport,
    MeetingRoom,
    MeetingParticipant,
    AIProviderConfig,
    AIUsageLedger,
    PushDeviceToken,
    OutboxEvent,
    IdempotencyKey,
)

__all__ = [
    "Base",
    # Phase 1
    "Role",
    "User",
    "UserRole",
    "AlumniProfile",
    "StudentProfile",
    "FacultyProfile",
    "RecruiterProfile",
    "UserPreference",
    "ConsentRecord",
    "AlumniLocation",
    "Skill",
    "UserSkill",
    "AuditLog",
    # Phase 2
    "MentorProfile",
    "MentorRequest",
    "Job",
    "JobApplication",
    "Event",
    "EventRegistration",
    "AlumniChapter",
    # Phase 3
    "CareerRoleSkill",
    "LearningResource",
    "StudentSkill",
    "AgentRun",
    "AgentAction",
    "ApprovalRequest",
    # Phase 4
    "CourseEnrollment",
    "Community",
    "CommunityMembership",
    "VerificationRequest",
    "AdminAuditLog",
    "Project",
    "ProjectMember",
    "Startup",
    "StartupConnectionRequest",
    "ImpactProgramme",
    "VolunteerInterest",
    "Notification",
    # Enterprise V2 (17 models)
    "AlumniAvailability",
    "MeetingRequest",
    "MeetingSlot",
    "Meeting",
    "Conversation",
    "ConversationParticipant",
    "Message",
    "MessageAttachment",
    "UserBlock",
    "UserReport",
    "MeetingRoom",
    "MeetingParticipant",
    "AIProviderConfig",
    "AIUsageLedger",
    "PushDeviceToken",
    "OutboxEvent",
    "IdempotencyKey",
]
