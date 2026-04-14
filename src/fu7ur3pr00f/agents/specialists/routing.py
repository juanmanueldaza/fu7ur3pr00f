"""Routing service — routes queries to specialists via semantic or keyword matching.

Provides LLM-based semantic routing with keyword fallback for determining
which specialist agents should handle a user query.

Usage:
    routing = get_routing_service()
    specialists = routing.route(query, conversation_history, turn_type)
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, cast

from fu7ur3pr00f._config import load_config
from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.container import container

logger = logging.getLogger(__name__)

_SPECIALIST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "coach": (
        "promotion",
        "promoted",
        "staff engineer",
        "principal",
        "leadership",
        "manager",
        "grow",
        "career",
    ),
    "learning": (
        "learn",
        "learning",
        "study",
        "course",
        "roadmap",
        "practice",
        "skill",
        "training",
    ),
    "jobs": (
        "job",
        "jobs",
        "hiring",
        "salary",
        "compensation",
        "interview",
        "offer",
        "remote",
        "position",
    ),
    "code": (
        "github",
        "gitlab",
        "repository",
        "repo",
        "portfolio",
        "open source",
        "oss",
        "project",
    ),
    "founder": (
        "startup",
        "founder",
        "saas",
        "business",
        "mvp",
        "bootstrapp",
        "fundraising",
        "venture",
    ),
    "prea_proxy": (
        "prea",
        "external agent",
        "interop",
        "a2a",
    ),
}
_MULTI_SPECIALIST_KEYWORDS = tuple(load_config("routing_keywords"))


@dataclass
class RoutingResult:
    """Result of routing decision."""

    specialists: list[str]
    method: str  # "llm", "keyword", "follow_up"
    confidence: float


class RoutingService:
    """Routes user queries to specialist agents.

    Primary routing uses LLM-based semantic understanding; keyword scoring
    is the deterministic fallback when the LLM is unavailable.

    Usage:
        routing = get_routing_service()
        result = routing.route(user_query)
        # result.specialists contains list of specialist names
    """

    def __init__(self) -> None:
        self._specialists: dict[str, BaseAgent] = {}
        self._initialized = False

    def _ensure_specialists(self) -> None:
        """Deferred initialization of specialist agents to break circular "
        "dependencies."""
        if self._initialized:
            return
        from fu7ur3pr00f.agents.specialists import (
            CoachAgent,
            CodeAgent,
            FounderAgent,
            JobsAgent,
            LearningAgent,
        )

        # Default specialists
        self._specialists = {
            "coach": CoachAgent(),
            "learning": LearningAgent(),
            "jobs": JobsAgent(),
            "code": CodeAgent(),
            "founder": FounderAgent(),
        }

        # Register PREA proxy only when an A2A agent key is configured. This
        # keeps tests deterministic when A2A integration isn't enabled.
        try:
            if getattr(container.settings, "a2a_agent_key", ""):
                from fu7ur3pr00f.agents.specialists import A2AProxyAgent

                self._specialists["prea_proxy"] = A2AProxyAgent()
        except (ImportError, AttributeError) as exc:
            # Log and continue — routing should remain usable without A2A
            logger.debug("A2A proxy not registered: %s", exc)
        self._initialized = True

    def route(
        self,
        query: str,
        conversation_history: Sequence[Any] | None = None,
        turn_type: str | None = None,
    ) -> RoutingResult:
        """Route query to one or more specialists via LLM.

        Args:
            query: User's query
            conversation_history: Prior turns (optional, for context-aware routing)
            turn_type: Turn classification (optional, from turn_classifier)

        Returns:
            RoutingResult with specialist names and routing method used
        """
        self._ensure_specialists()
        # Context-aware routing: reuse previous specialists for follow-ups
        if turn_type == "follow_up" and conversation_history:
            last_turn = conversation_history[-1]
            prev_specialists = last_turn.get("specialist_names", [])
            if prev_specialists:
                logger.debug(
                    "route(%r) → %s (follow_up, reusing previous)",
                    query[:60],
                    prev_specialists,
                )
                return RoutingResult(
                    specialists=prev_specialists,
                    method="follow_up",
                    confidence=1.0,
                )

        try:
            result = self._route_with_llm(query, conversation_history, turn_type)
            logger.debug("route_llm(%r) → %s", query[:60], result)
            return RoutingResult(specialists=result, method="llm", confidence=0.9)
        except Exception:
            logger.warning(
                "LLM routing failed for %r, using keyword fallback",
                query[:60],
                exc_info=True,
            )
            specialists = self._route_with_keywords(query)
            return RoutingResult(
                specialists=specialists,
                method="keyword",
                confidence=0.6 if specialists != ["coach"] else 0.5,
            )

    def _route_with_llm(
        self,
        query: str,
        conversation_history: Sequence[Any] | None = None,
        turn_type: str | None = None,
    ) -> list[str]:
        """Route using LLM-based semantic understanding.

        Parses specialist descriptions and selects 1-4 specialists via
        structured output (Pydantic model).
        """
        self._ensure_specialists()
        from langchain_core.messages import HumanMessage

        from fu7ur3pr00f.agents.specialists.routing_schema import RoutingDecision
        from fu7ur3pr00f.prompts import load_prompt

        # Build context from conversation history
        context = "No prior context."
        if turn_type in ("steer", "workflow_step") and conversation_history:
            recent = conversation_history[-3:]
            context_lines = [f"- {t.get('query', '')[:80]}" for t in recent]
            context = "\n".join(context_lines)

        prompt_template = load_prompt("route_specialists")
        prompt = prompt_template.format(
            query=query,
            context=context,
        )

        model, _ = container.get_model(purpose="summary", temperature=0.0)
        router = model.with_structured_output(RoutingDecision)
        result = cast(RoutingDecision, router.invoke([HumanMessage(content=prompt)]))

        # Validate names against known specialists
        valid = [name for name in result.specialists if name in self._specialists]
        return valid or ["coach"]

    def _route_with_keywords(self, query: str) -> list[str]:
        """Route using deterministic keyword scoring.

        Keeps routing useful when the LLM is unavailable, which is common in
        local development and CI runs.
        """
        lowered = query.lower()
        scores: dict[str, int] = {}

        for specialist, keywords in _SPECIALIST_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in lowered)
            if score:
                scores[specialist] = score

        if not scores:
            return ["coach"]

        ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        top_score = ordered[0][1]
        selected = [name for name, score in ordered if score == top_score]

        if any(keyword in lowered for keyword in _MULTI_SPECIALIST_KEYWORDS):
            return selected[: min(len(selected), 3)]

        return [selected[0]]

    def get_specialist(self, name: str) -> BaseAgent:
        """Return the specialist agent object by name."""
        self._ensure_specialists()
        return self._specialists.get(name, self._specialists["coach"])

    def list_agents(self) -> list[dict[str, str]]:
        """List all available specialists."""
        self._ensure_specialists()
        return [
            {"name": a.name, "description": a.description}
            for a in self._specialists.values()
        ]

    def reset(self) -> None:
        """Reset routing state (no-op for stateless routing)."""
        logger.debug("RoutingService.reset() called (no-op)")


# ── Module-level singleton ────────────────────────────────────────────────────

# The RoutingService is now managed by the fu7ur3pr00f.container.container singleton.
# get_routing_service and reset_routing_service are kept for backward compatibility.


def get_routing_service() -> RoutingService:
    """Get the routing service from the global container."""
    return container.routing_service


def reset_routing_service() -> None:
    """Reset the routing service via the global container."""
    container.reset_services()
