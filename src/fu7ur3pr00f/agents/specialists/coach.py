"""Coach Agent — Career growth and leadership specialist."""

import logging

from fu7ur3pr00f.agents.blackboard.blackboard import SpecialistFinding
from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import COACH_TOOLS
from fu7ur3pr00f.prompts import load_prompt

logger = logging.getLogger(__name__)


class CoachAgent(BaseAgent):
    """Career growth, promotions, and leadership coaching.

    Specialises in:
    - Promotion strategy (Senior → Staff → Principal)
    - CliftonStrengths-based development planning
    - Leadership and influence building
    - Skill gap analysis for target roles
    """

    @property
    def name(self) -> str:
        return "coach"

    @property
    def description(self) -> str:
        return "Career growth and leadership coach"

    @property
    def system_prompt(self) -> str:
        return load_prompt("specialist_coach")

    @property
    def tools(self) -> list:
        return COACH_TOOLS

    def contribute(
        self,
        blackboard,
        stream_writer=None,
    ) -> SpecialistFinding:
        """Contribute analysis, auto-searching knowledge base if profile is empty.

        When the user profile is empty but knowledge base has data, automatically
        search for the user's identity info before responding.
        """
        # Check if profile is empty and knowledge base might have data
        profile = blackboard.get("profile", {})
        has_profile = bool(profile and profile.get("name"))

        if not has_profile:
            # Auto-search knowledge base for user identity
            try:
                from fu7ur3pr00f.agents.tools.knowledge import search_career_knowledge

                # Search for identity info
                identity_result = search_career_knowledge("my name who am I profile")  # type: ignore[operator]
                if identity_result and "No career data" not in identity_result:
                    # Inject into blackboard context for the LLM to use
                    existing_context = blackboard.get("_kb_context", "")
                    blackboard["_kb_context"] = (
                        existing_context
                        + "\n\n[AUTO-SEARCH RESULT: User identity found in knowledge base]\n"
                        + identity_result[:2000]
                        + "\n[/AUTO-SEARCH RESULT]"
                    )
                    logger.warning(
                        "[coach] Auto-searched knowledge base for identity, found %d chars",
                        len(identity_result),
                    )
            except Exception as e:
                logger.warning("[coach] Auto-search failed: %s", e)

        return super().contribute(blackboard, stream_writer)


__all__ = ["CoachAgent"]
