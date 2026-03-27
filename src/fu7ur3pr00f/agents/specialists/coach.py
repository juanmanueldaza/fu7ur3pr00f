"""Coach Agent — Career growth and leadership specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import COACH_TOOLS


class CoachAgent(BaseAgent):
    """Career growth, promotions, and leadership coaching.

    Specialises in:
    - Promotion strategy (Senior → Staff → Principal)
    - CliftonStrengths-based development planning
    - Leadership and influence building
    - Skill gap analysis for target roles
    """

    KEYWORDS = frozenset(
        {
            "promotion",
            "promoted",
            "leadership",
            "lead",
            "manager",
            "staff",
            "principal",
            "senior",
            "career growth",
            "career path",
            "influence",
            "office politics",
            "cliftonstrengths",
            "strengths",
            "coaching",
            "mentor",
            "mentoring",
            "visibility",
            "impact",
            "advice",
            "strategy",
            "next step",
        }
    )

    @property
    def name(self) -> str:
        return "coach"

    @property
    def description(self) -> str:
        return "Career growth and leadership coach"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a senior career coach for software engineers.\n\n"
            "Focus:\n"
            "- Promotion strategy (IC track: Senior → Staff → Principal)\n"
            "- CliftonStrengths-based coaching when data is available\n"
            "- Leadership development and influence building\n"
            "- Concrete skill gap analysis against the user's target role\n\n"
            "Always: search the knowledge base first, reference the user's actual "
            "experience and strengths, give specific action plans with timelines. "
            "Be direct about gaps — don't just affirm what's already strong."
        )

    @property
    def tools(self) -> list:
        return COACH_TOOLS


__all__ = ["CoachAgent"]
