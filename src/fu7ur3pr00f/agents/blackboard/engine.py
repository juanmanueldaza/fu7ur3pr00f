"""Conversation engine — high-level interface to the session graph.

Wraps the outer conversation graph and provides a simple invoke_turn()
method for the chat client.
"""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from langchain_core.runnables import RunnableConfig

from fu7ur3pr00f.agents.blackboard.blackboard import SpecialistFinding
from fu7ur3pr00f.agents.blackboard.session import make_initial_session
from fu7ur3pr00f.agents.blackboard.streaming import synthesis_token_callback
from fu7ur3pr00f.container import container

logger = logging.getLogger(__name__)


@dataclass
class TurnResult:
    """Result of a single conversation turn."""

    synthesis: dict[str, Any]
    """The synthesis narrative returned to user"""

    specialists: list[str]
    """Specialists that ran"""

    elapsed: float
    """Execution time in seconds"""

    suggested_next: list[str]
    """Suggested follow-ups"""

    cumulative_findings: dict[str, Any]
    """Accumulated findings across conversation"""


class ConversationEngine:
    """High-level interface to conversational blackboard.

    Manages turn-by-turn execution via the outer graph, persisting
    session state across turns via LangGraph checkpointer.

    Callbacks are updated per-turn via a shared mutable dict closed over
    by the compiled graph's nodes. This avoids recompiling on every turn.

    Not safe for concurrent invoke_turn() calls on the same instance.
    If concurrent use is needed, use contextvars.ContextVar instead of
    the shared dict.
    """

    def __init__(self) -> None:
        """Initialize the engine with checkpointer-backed graph compiled once."""
        checkpointer = container.get_checkpointer()
        self._checkpointer = checkpointer
        # Mutable holder — updated per turn, read by nodes at execution time
        self._callbacks: dict[str, Any] = {}
        # Compile once — nodes close over self._callbacks
        self._graph = container.conversation_graph

    def invoke_turn(
        self,
        query: str,
        thread_id: str = "main",
        user_profile: dict[str, Any] | None = None,
        on_specialist_start: Callable[[str], None] | None = None,
        on_specialist_complete: (
            Callable[[str, SpecialistFinding], None] | None
        ) = None,
        on_tool_start: Callable[[str, str, dict], None] | None = None,
        on_tool_result: Callable[[str, str, str], None] | None = None,
        confirm_fn: Callable[[str, str], bool] | None = None,
        on_synthesis_token: Callable[[str], None] | None = None,
    ) -> TurnResult:
        """Execute a single conversation turn.

        Args:
            query: User's question
            thread_id: Conversation thread identifier (determines session)
            user_profile: User's career profile (loaded from disk if not provided)
            on_specialist_start: Called when specialist starts working
            on_specialist_complete: Called when specialist completes
            on_tool_start: Called when a tool is invoked
            on_tool_result: Called when a tool returns a result
            confirm_fn: Human-in-the-loop confirmation for tool interrupts

        Returns:
            TurnResult with synthesis, specialists, elapsed time, suggestions
        """
        # Update callback holder — nodes read this at execution time
        self._callbacks.update(
            {
                "on_specialist_start": on_specialist_start,
                "on_specialist_complete": on_specialist_complete,
                "on_tool_start": on_tool_start,
                "on_tool_result": on_tool_result,
                "confirm_fn": confirm_fn,
            }
        )

        # Set synthesis streaming callback in ContextVar (thread-safe, per-turn)
        stream_token = synthesis_token_callback.set(on_synthesis_token)
        try:
            return self._invoke_turn_inner(query, thread_id, user_profile)
        finally:
            synthesis_token_callback.reset(stream_token)

    def _invoke_turn_inner(
        self,
        query: str,
        thread_id: str,
        user_profile: dict[str, Any] | None,
    ) -> TurnResult:
        if user_profile is None:
            profile = container.profile
            user_profile = {
                "name": profile.name,
                "location": profile.location,
                "current_role": profile.current_role,
                "years_experience": profile.years_experience,
                "technical_skills": profile.technical_skills,
                "target_roles": profile.target_roles,
                "goals": [g.description for g in profile.goals],
                "github_username": profile.github_username,
                "gitlab_username": profile.gitlab_username,
            }

        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        start = time.monotonic()

        # Load existing session or start fresh
        snap = self._graph.get_state(config)
        if snap and snap.values:
            session_state = cast(dict[str, Any], snap.values)
        else:
            session_state = cast(dict[str, Any], make_initial_session(user_profile))

        # Update for this turn
        session_state["current_query"] = query
        session_state["user_profile"] = user_profile

        logger.debug("Turn: %r (thread=%s)", query[:60], thread_id)
        result_state = self._graph.invoke(session_state, config)

        elapsed = time.monotonic() - start

        return TurnResult(
            synthesis=result_state.get("synthesis", {}),
            specialists=result_state.get("routed_specialists", []),
            elapsed=elapsed,
            suggested_next=result_state.get("suggested_next", []),
            cumulative_findings=result_state.get("cumulative_findings", {}),
        )


# Module-level singleton
_engine: ConversationEngine | None = None


def get_conversation_engine() -> ConversationEngine:
    """Get or create the global conversation engine."""
    global _engine
    if _engine is None:
        _engine = ConversationEngine()
    return _engine


def reset_conversation_engine() -> None:
    """Reset the engine singleton and its cached graph via the global container."""
    global _engine
    _engine = None
    container.reset_services()


__all__ = [
    "ConversationEngine",
    "TurnResult",
    "get_conversation_engine",
    "reset_conversation_engine",
]
