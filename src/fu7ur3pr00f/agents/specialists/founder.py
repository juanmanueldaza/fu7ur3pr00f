"""Founder Agent — Startups and entrepreneurship specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import FOUNDER_TOOLS
from fu7ur3pr00f.prompts import load_prompt


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
        return load_prompt("specialist_founder")

    @property
    def tools(self) -> list:
        return FOUNDER_TOOLS


__all__ = ["FounderAgent"]
