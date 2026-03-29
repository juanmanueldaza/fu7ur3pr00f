"""Shared service accessors with caching.

Provides singleton access to commonly used services to eliminate
repeated instantiation across the codebase.

Usage:
    from fu7ur3pr00f.utils.services import get_knowledge_service, get_profile

    # Cached access — only instantiated once per process
    service = get_knowledge_service()
    profile = get_profile()
"""

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fu7ur3pr00f.memory.profile import UserProfile
    from fu7ur3pr00f.services.knowledge_service import KnowledgeService


@lru_cache(maxsize=1)
def get_knowledge_service() -> "KnowledgeService":
    """Get cached KnowledgeService instance.

    Returns the same instance on every call, eliminating
    repeated instantiation across tools and services.

    Returns:
        Singleton KnowledgeService instance
    """
    from fu7ur3pr00f.services.knowledge_service import KnowledgeService

    return KnowledgeService()


@lru_cache(maxsize=1)
def get_profile() -> "UserProfile":
    """Get cached UserProfile instance.

    Returns the same instance on every call, eliminating
    repeated file I/O across tools and services.

    Note: Call reload_profile() after editing profile to invalidate cache.

    Returns:
        Cached UserProfile instance
    """
    from fu7ur3pr00f.memory.profile import load_profile

    return load_profile()


def reload_profile() -> "UserProfile":
    """Reload profile and invalidate cache.

    Call this after editing profile to ensure subsequent
    get_profile() calls return updated data.

    Returns:
        Fresh UserProfile instance (also updates cache)
    """
    from fu7ur3pr00f.memory.profile import load_profile

    get_profile.cache_clear()
    return load_profile()
