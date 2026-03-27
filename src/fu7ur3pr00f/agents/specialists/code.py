"""Code Agent — GitHub, GitLab, and open source strategy specialist."""

from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import CODE_TOOLS


class CodeAgent(BaseAgent):
    """GitHub, GitLab, and open source portfolio specialist.

    Specialises in:
    - GitHub/GitLab profile and repository analysis
    - Open source contribution strategy
    - Portfolio gap identification
    - Project visibility and developer branding
    - Selecting side projects for career impact
    """

    KEYWORDS = frozenset(
        {
            "github",
            "gitlab",
            "repos",
            "repositories",
            "code",
            "commits",
            "open source",
            "oss",
            "contributions",
            "projects",
            "portfolio",
            "side project",
            "developer brand",
            "visibility",
            "pull request",
            "fork",
            "star",
            "gist",
            "readme",
        }
    )

    @property
    def name(self) -> str:
        return "code"

    @property
    def description(self) -> str:
        return "GitHub, GitLab, and open source strategy"

    @property
    def system_prompt(self) -> str:
        return (
            "You are a developer portfolio and open source strategist.\n\n"
            "Focus:\n"
            "- Analyse the user's GitHub/GitLab repos and activity\n"
            "- Identify portfolio gaps for their target role\n"
            "- Recommend specific projects aligned with market trends\n"
            "- Optimise GitHub profile for recruiter visibility\n"
            "- Suggest open source projects to contribute to\n\n"
            "Always: pull real repo and profile data before advising, "
            "check tech trends to align project suggestions with demand, "
            "prioritise quality over quantity."
        )

    @property
    def tools(self) -> list:
        return CODE_TOOLS


__all__ = ["CodeAgent"]
