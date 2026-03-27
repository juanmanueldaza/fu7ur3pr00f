"""Jobs Agent — Job search and market intelligence specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import JOBS_TOOLS


class JobsAgent(BaseAgent):
    """Job search, market intelligence, and compensation specialist.

    Specialises in:
    - Job board search across 7 boards + Hacker News
    - Salary benchmarking with PPP-adjusted comparisons
    - Market fit analysis for target roles
    - CV optimisation for specific job openings
    - Offer evaluation and negotiation strategy
    """

    KEYWORDS = frozenset(
        {
            "jobs",
            "job",
            "hiring",
            "interview",
            "salary",
            "compensation",
            "benefits",
            "remote",
            "work from home",
            "job search",
            "apply",
            "resume",
            "cv",
            "negotiate",
            "offer",
            "market",
            "opportunity",
            "recruiter",
            "application",
            "cover letter",
            "market fit",
            "search",
            "find",
            "looking for work",
        }
    )

    @property
    def name(self) -> str:
        return "jobs"

    @property
    def description(self) -> str:
        return "Job search and market intelligence"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a job search strategist for software developers.\n\n"
            "Focus:\n"
            "- Search job boards and Hacker News for live opportunities\n"
            "- Benchmark salary with PPP adjustments for any location\n"
            "- Analyse market fit and identify the user's strongest selling points\n"
            "- Help generate targeted CVs for specific roles\n"
            "- Advise on offer evaluation and negotiation\n\n"
            "Always: search jobs and get salary data before giving advice, "
            "be specific about salary ranges (use the financial tools), "
            "warn about common pitfalls (lowball offers, red-flag job descriptions)."
        )

    @property
    def tools(self) -> list:
        return JOBS_TOOLS


__all__ = ["JobsAgent"]
