"""Jobs Agent — Job search and market intelligence specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import JOBS_TOOLS
from fu7ur3pr00f.prompts import load_prompt


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
        return load_prompt("specialist_jobs")

    @property
    def tools(self) -> list:
        return JOBS_TOOLS


__all__ = ["JobsAgent"]
