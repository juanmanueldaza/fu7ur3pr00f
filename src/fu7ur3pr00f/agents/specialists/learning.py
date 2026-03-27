"""Learning Agent — Skill development and expertise building specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import LEARNING_TOOLS


class LearningAgent(BaseAgent):
    """Skill development, learning roadmaps, and expertise building.

    Specialises in:
    - Personalised learning roadmaps for target roles
    - Identifying the highest-leverage skills to learn next
    - Technology trend analysis (what the market values)
    - Building expertise through teaching (blogs, talks, OSS)
    """

    KEYWORDS = frozenset(
        {
            "learning",
            "study",
            "learn",
            "skills",
            "courses",
            "certification",
            "expert",
            "authority",
            "teaching",
            "conference",
            "talk",
            "blog",
            "write",
            "publish",
            "training",
            "tutorial",
            "practice",
            "improve",
            "master",
            "specialize",
            "roadmap",
            "curriculum",
            "knowledge",
        }
    )

    @property
    def name(self) -> str:
        return "learning"

    @property
    def description(self) -> str:
        return "Skill development and expertise building"

    @property
    def system_prompt(self) -> str:
        return (
            "You are an expert learning strategist for software developers.\n\n"
            "Focus:\n"
            "- Designing personalised learning roadmaps based on the user's goals\n"
            "- Identifying highest-leverage skills using market trend data\n"
            "- Recommending specific resources (courses, books, projects, talks)\n"
            "- Building public expertise through teaching and contribution\n\n"
            "Always: check tech trends and market data, compare current skills against "
            "requirements for the target role, give concrete timelines "
            "(1 month / 3 months / 6 months), and suggest demonstrable outputs."
        )

    @property
    def tools(self) -> list:
        return LEARNING_TOOLS


__all__ = ["LearningAgent"]
