"""Founder Agent — Startups and entrepreneurship specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import FOUNDER_TOOLS


class FounderAgent(BaseAgent):
    """Startups, entrepreneurship, and developer-to-founder transition.

    Specialises in:
    - Idea validation and founder-market fit analysis
    - MVP scoping based on existing skills
    - Bootstrapping vs. fundraising trade-offs
    - Market opportunity research
    - Developer-to-founder transition planning
    """

    KEYWORDS = frozenset(
        {
            "startup",
            "founder",
            "cofounder",
            "co-founder",
            "launch",
            "product",
            "entrepreneur",
            "mvp",
            "side project",
            "business idea",
            "company",
            "bootstrap",
            "fundraising",
            "revenue",
            "saas",
            "indie",
            "solo",
            "validate",
            "build a product",
            "productize",
        }
    )

    @property
    def name(self) -> str:
        return "founder"

    @property
    def description(self) -> str:
        return "Startups and developer-to-founder strategy"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a startup advisor specialising in developer-founders.\n\n"
            "Focus:\n"
            "- Assess founder-market fit from the user's skills and experience\n"
            "- Scope MVPs the user can build with their existing stack\n"
            "- Research market demand and opportunity size\n"
            "- Compare bootstrapping vs. funding scenarios with real numbers\n"
            "- Plan the developer-to-founder transition step by step\n\n"
            "Always: pull real market and salary data, be realistic about timelines "
            "and effort, reference the user's actual technical stack when suggesting "
            "what to build, prefer sustainable bootstrapping over VC by default."
        )

    @property
    def tools(self) -> list:
        return FOUNDER_TOOLS


__all__ = ["FounderAgent"]
