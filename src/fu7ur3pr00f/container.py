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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fu7ur3pr00f.config import Settings
    from fu7ur3pr00f.llm.model_selection import ModelSelectionManager
    from fu7ur3pr00f.memory.profile import UserProfile
    from fu7ur3pr00f.services.knowledge_service import KnowledgeService
    from fu7ur3pr00f.agents.specialists.orchestrator import OrchestratorAgent
    from fu7ur3pr00f.agents.specialists.blackboard_factory import BlackboardFactory
    from fu7ur3pr00f.agents.specialists.routing import RoutingService
    from fu7ur3pr00f.utils import security


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
        self._conversation_graph: Any | None = None
        self._orchestrator: OrchestratorAgent | None = None
        self._blackboard_factory: BlackboardFactory | None = None
        self._routing_service: RoutingService | None = None
        self._security_utils: Any | None = None

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

    def get_model(self, temperature: float | None = None, purpose: str | None = None) -> tuple:
        """Get a configured model for the given purpose.

        Convenience method that delegates to model_manager.

        Returns:
            Tuple of (BaseChatModel, ModelConfig)
        """
        # Import here to avoid circular dependency
        from fu7ur3pr00f.llm.model_selection import get_model

        return get_model(temperature=temperature, purpose=purpose)

    def load_prompt(self, prompt_name: str) -> Any:
        """Load a prompt from the assets directory.

        Convenience method that delegates to the prompts module.
        """
        from fu7ur3pr00f.prompts import load_prompt

        return load_prompt(prompt_name)

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
        self._conversation_graph = None
        self._orchestrator = None
        self._blackboard_factory = None
        self._routing_service = None
        self._security_utils = None
        # Note: settings is a module-level singleton, not reset here

    def reset_orchestrator(self) -> None:
        """Reset the orchestrator singleton."""
        from fu7ur3pr00f.agents.specialists.orchestrator import reset_orchestrator

        reset_orchestrator()

    def reset_model_selection_manager(self) -> None:
        """Reset the model selection manager singleton."""
        from fu7ur3pr00f.llm.model_selection import reset_model_selection_manager

        reset_model_selection_manager()

    @property
    def conversation_graph(self) -> Any:
        """Get the compiled conversation graph (lazy singleton)."""
        if self._conversation_graph is None:
            from fu7ur3pr00f.agents.blackboard.conversation_graph import build_conversation_graph

            self._conversation_graph = build_conversation_graph()
        return self._conversation_graph

    @property
    def orchestrator(self) -> OrchestratorAgent:
        """Get the orchestrator agent (lazy singleton)."""
        if self._orchestrator is None:
            from fu7ur3pr00f.agents.specialists.orchestrator import OrchestratorAgent

            self._orchestrator = OrchestratorAgent()
        return self._orchestrator

    @property
    def blackboard_factory(self) -> BlackboardFactory:
        """Get the blackboard factory (lazy singleton)."""
        if self._blackboard_factory is None:
            from fu7ur3pr00f.agents.specialists.blackboard_factory import BlackboardFactory

            self._blackboard_factory = BlackboardFactory()
        return self._blackboard_factory

    @property
    def routing_service(self) -> RoutingService:
        """Get the routing service (lazy singleton)."""
        if self._routing_service is None:
            from fu7ur3pr00f.agents.specialists.routing import RoutingService

            self._routing_service = RoutingService()
        return self._routing_service

    @property
    def security_utils(self) -> Any:
        """Get security utility functions."""
        if self._security_utils is None:
            from fu7ur3pr00f.utils import security

            self._security_utils = security
        return self._security_utils

    def get_specialist(self, name: str) -> Any:
        """Get a specific specialist agent by name via the factory."""
        return self.blackboard_factory.get_specialist(name)

    def get_data_dir(self) -> Any:
        """Get the application data directory."""
        from fu7ur3pr00f.memory.checkpointer import get_data_dir

        return get_data_dir()

    def get_checkpointer(self) -> Any:
        """Get the configured session checkpointer."""
        from fu7ur3pr00f.memory.checkpointer import get_checkpointer

        return get_checkpointer()


container = Container.get()
