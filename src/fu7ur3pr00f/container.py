"""Lightweight Dependency Injection Container.

Replaces global singletons with a single container that manages service lifetimes.
Provides lazy initialization and reset capabilities for testing.

Usage:
    from fu7ur3pr00f.container import Container

    container = Container.get()
    settings = container.settings
    model_manager = container.model_manager
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fu7ur3pr00f.config import Settings
    from fu7ur3pr00f.llm.model_selection import ModelSelectionManager
    from fu7ur3pr00f.memory.profile import UserProfile
    from fu7ur3pr00f.services.knowledge_service import KnowledgeService


class Container:
    """Application-wide dependency container.

    Singleton pattern with thread-safe initialization.
    Services are lazily created on first access.
    """

    _instance: Container | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize container with empty service caches."""
        self._settings: Settings | None = None
        self._model_manager: ModelSelectionManager | None = None
        self._knowledge_service: KnowledgeService | None = None
        self._profile: UserProfile | None = None

    @classmethod
    def get(cls) -> Container:
        """Get or create the singleton container instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset container singleton (for testing and settings reload)."""
        with cls._lock:
            cls._instance = None

    @property
    def settings(self) -> Settings:
        """Get application settings (singleton from config module)."""
        if self._settings is None:
            # Import here to avoid circular dependency
            from fu7ur3pr00f.config import settings

            self._settings = settings
        return self._settings

    @property
    def model_manager(self) -> ModelSelectionManager:
        """Get model selection manager (lazy singleton)."""
        if self._model_manager is None:
            from fu7ur3pr00f.llm.model_selection import ModelSelectionManager

            self._model_manager = ModelSelectionManager()
        return self._model_manager

    def get_model(
        self, temperature: float | None = None, purpose: str | None = None
    ) -> tuple:
        """Get a configured model for the given purpose.

        Convenience method that delegates to model_manager.

        Returns:
            Tuple of (BaseChatModel, ModelConfig)
        """
        # Import here to avoid circular dependency
        from fu7ur3pr00f.llm.model_selection import get_model

        return get_model(temperature=temperature, purpose=purpose)

    @property
    def knowledge_service(self) -> KnowledgeService:
        """Get knowledge service (lazy singleton)."""
        if self._knowledge_service is None:
            from fu7ur3pr00f.services.knowledge_service import KnowledgeService

            self._knowledge_service = KnowledgeService()
        return self._knowledge_service

    @property
    def profile(self) -> UserProfile:
        """Get user profile (lazy singleton)."""
        if self._profile is None:
            from fu7ur3pr00f.memory.profile import load_profile

            self._profile = load_profile()
        return self._profile

    def reload_profile(self) -> UserProfile:
        """Reload user profile and update cache."""
        from fu7ur3pr00f.memory.profile import load_profile

        self._profile = load_profile()
        return self._profile

    def reset_services(self) -> None:
        """Reset all cached services (for testing and settings reload)."""
        self._model_manager = None
        self._knowledge_service = None
        self._profile = None
        # Note: settings is a module-level singleton, not reset here

    def reset_orchestrator(self) -> None:
        """Reset the orchestrator singleton."""
        from fu7ur3pr00f.agents.specialists.orchestrator import reset_orchestrator

        reset_orchestrator()

    def reset_model_selection_manager(self) -> None:
        """Reset the model selection manager singleton."""
        from fu7ur3pr00f.llm.model_selection import reset_model_selection_manager

        reset_model_selection_manager()
