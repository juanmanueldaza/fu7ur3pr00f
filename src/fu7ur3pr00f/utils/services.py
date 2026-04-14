"""Shared service accessors with caching.

Provides singleton access to commonly used services to eliminate
repeated instantiation across the codebase.

Usage:
    from fu7ur3pr00f.utils.services import get_knowledge_service, get_profile

    # Cached access — only instantiated once per process
    service = get_knowledge_service()
    profile = get_profile()
"""

from typing import TYPE_CHECKING

from fu7ur3pr00f.container import container

if TYPE_CHECKING:
    from fu7ur3pr00f.memory.profile import UserProfile
    from fu7ur3pr00f.services.knowledge_service import KnowledgeService


def get_knowledge_service() -> "KnowledgeService":
    """Get KnowledgeService instance via the global container."""
    return container.knowledge_service


def get_profile() -> "UserProfile":
    """Get UserProfile instance via the global container."""
    return container.profile


def reload_profile() -> "UserProfile":
    """Reload profile and update cache via the global container."""
    return container.reload_profile()
