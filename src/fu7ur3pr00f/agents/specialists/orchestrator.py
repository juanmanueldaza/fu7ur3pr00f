"""Orchestrator — routes queries to specialists via the blackboard pattern.

Thin wrapper that coordinates RoutingService and BlackboardFactory.
All queries run through the blackboard pattern.

Usage (from the chat client):
    orchestrator = get_orchestrator()
    result = orchestrator.route(user_input)  # RoutingResult
    executor = orchestrator.get_executor(result.specialists)
    blackboard = executor.execute(query=..., user_profile=..., callbacks=...)
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from fu7ur3pr00f.agents.specialists.routing import RoutingResult

from fu7ur3pr00f.agents.blackboard.executor import BlackboardExecutor
from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.container import container

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Orchestrates query routing and blackboard execution.

    Delegates to RoutingService for specialist selection and
    BlackboardFactory for executor creation.

    Usage:
        orchestrator = get_orchestrator()
        result = orchestrator.route(query)
        executor = orchestrator.get_executor(result.specialists)
    """

    def __init__(self) -> None:
        self._routing = container.routing_service
        self._factory = container.blackboard_factory

    def route(
        self,
        query: str,
        conversation_history: Sequence[Any] | None = None,
        turn_type: str | None = None,
    ) -> list[str]:
        """Route query to one or more specialists.

        Uses LLM-based semantic routing with keyword fallback.
        Returns a list of specialist names (backward-compatible API).

        Args:
            query: User's query
            conversation_history: Prior turns (optional, for context-aware routing)
            turn_type: Turn classification (optional, from turn_classifier)

        Returns:
            List of specialist names to handle the query
        """
        result = self._routing.route(query, conversation_history, turn_type)
        return result.specialists

    def route_with_result(
        self,
        query: str,
        conversation_history: Sequence[Any] | None = None,
        turn_type: str | None = None,
    ) -> RoutingResult:
        """Route query and return full RoutingResult with metadata.

        Use this when you need routing method and confidence information.

        Args:
            query: User's query
            conversation_history: Prior turns (optional)
            turn_type: Turn classification (optional)

        Returns:
            RoutingResult with specialists, method, and confidence
        """
        return self._routing.route(query, conversation_history, turn_type)

    def get_executor(
        self,
        specialist_names: list[str] | None = None,
        max_iterations: int = 1,
        strategy: str = "linear",
    ) -> BlackboardExecutor:
        """Get a BlackboardExecutor with the requested specialists.

        Args:
            specialist_names: Which specialists to include (from route()).
                If None, includes all specialists.
            max_iterations: Maximum blackboard iterations (default 1)
            strategy: Scheduling strategy (default "linear")

        Returns:
            Executor ready to run blackboard-based analysis
        """
        return self._factory.create_executor(
            specialist_names=specialist_names,
            max_iterations=max_iterations,
            strategy=strategy,
        )

    def get_specialist(self, name: str) -> BaseAgent:
        """Return the specialist agent object by name."""
        return self._routing.get_specialist(name)

    def list_agents(self) -> list[dict[str, str]]:
        """List all available specialists."""
        return self._routing.list_agents()

    def get_model_name(self, specialist_name: str | None = None) -> str | None:
        """Return the model description used by specialists."""
        try:
            _, config = container.get_model(purpose="agent")
            return config.description
        except Exception:
            logger.warning(
                "get_model_name() failed for %s",
                specialist_name,
                exc_info=True,
            )
            return None

    def reset(self) -> None:
        """Reset orchestrator state (delegates to routing and factory)."""
        self._routing.reset()
        logger.debug("Orchestrator.reset() called")


# ── Module-level singleton ────────────────────────────────────────────────────

_orchestrator: OrchestratorAgent | None = None
_orchestrator_lock = __import__("threading").Lock()


def get_orchestrator() -> OrchestratorAgent:
    """Get the orchestrator from the global container."""
    return container.orchestrator


def reset_orchestrator() -> None:
    """Reset the orchestrator via the global container."""
    container.reset_services()


__all__ = [
    "OrchestratorAgent",
    "get_orchestrator",
    "reset_orchestrator",
]
