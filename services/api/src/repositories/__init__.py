"""
MSGI One — Asynchronous Repositories Package Registry
Exports all domain repositories for typed dependency injection in FastAPI routers and services.
Principle: Martin Fowler (Repository Pattern) & Clean Architecture.
"""

from src.repositories.base import BaseRepository
from src.repositories.user_repository import UserRepository
from src.repositories.alumni_repository import AlumniRepository
from src.repositories.jobs_repository import JobsRepository
from src.repositories.mentor_repository import MentorRepository
from src.repositories.events_repository import EventsRepository
from src.repositories.learning_repository import LearningRepository
from src.repositories.community_repository import CommunityRepository
from src.repositories.admin_repository import AdminRepository
from src.repositories.notifications_repository import NotificationsRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "AlumniRepository",
    "JobsRepository",
    "MentorRepository",
    "EventsRepository",
    "LearningRepository",
    "CommunityRepository",
    "AdminRepository",
    "NotificationsRepository",
]
