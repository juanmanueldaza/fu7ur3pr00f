"""Analysis tools for the career agent."""

import logging

from langchain_core.tools import tool

from fu7ur3pr00f.agents.tools._analysis_helpers import invoke_with_context
from fu7ur3pr00f.memory.profile import load_profile

logger = logging.getLogger(__name__)


@tool
def analyze_skill_gaps(target_role: str) -> str:
    """Analyze the gap between current skills and a target role's requirements.

    Args:
        target_role: The job role to analyze gaps for
            (e.g., "ML Engineer", "Staff Developer")

    Use this when the user asks about skill gaps, career
    transitions, or what they need to learn.
    """
    try:
        result = invoke_with_context(
            search_query=f"skills experience {target_role}",
            prompt=(
                f"Analyze skill gaps for the target role: {target_role}\n\n"
                "User profile:\n{profile_summary}\n\n"
                "Career context:\n{career_context}\n\n"
                "Provide a concise gap analysis with 3-5 key areas to improve."
            ),
            search_limit=10,
        )
        return f"Skill gap analysis for {target_role!r}:\n\n{result}"

    except Exception as e:
        logger.exception("Skill gap analysis failed for '%s'", target_role)
        profile = load_profile()
        current_skills = profile.technical_skills + profile.soft_skills

        if not current_skills:
            return (
                f"Cannot analyze gaps for {target_role!r} — no skills recorded. "
                "Please tell me about your technical and soft skills first."
            )

        return (
            f"Skill gap analysis for {target_role!r}:\n\n"
            f"Your current skills: {', '.join(current_skills)}\n\n"
            f"Note: Full analysis requires gathered career data. "
            f"Error: {type(e).__name__}. Check logs for details."
        )


@tool
def analyze_career_alignment() -> str:
    """Analyze how well the user's current trajectory aligns with their goals.

    Use this for a comprehensive career analysis including
    goals, skills, and market fit.
    """
    try:
        result = invoke_with_context(
            search_query="career goals trajectory alignment",
            prompt=(
                "Analyze career alignment for this profile:\n"
                "{profile_summary}\n\n"
                "Career context:\n{career_context}\n\n"
                "Assess how well their current trajectory aligns with goals. "
                "Identify strengths and misalignments. Suggest adjustments."
            ),
            search_limit=15,
        )
        return f"Career alignment analysis:\n\n{result}"

    except Exception as e:
        logger.exception("Career alignment analysis failed")
        return (
            "Career alignment analysis encountered an error"
            f" ({type(e).__name__}). Check logs for details."
        )


@tool
def get_career_advice(target: str) -> str:
    """Get strategic career advice for reaching a specific goal or role.

    Args:
        target: The target role, goal, or career question

    Use this when the user asks for advice on career decisions or paths.
    """
    try:
        result = invoke_with_context(
            search_query=target,
            prompt=(
                f"Provide strategic career advice for: {target}\n\n"
                "User profile:\n{profile_summary}\n\n"
                "Relevant context:\n{career_context}\n\n"
                "Give actionable, specific advice with concrete next steps."
            ),
            search_limit=10,
        )
        return f"Career advice for {target!r}:\n\n{result}"

    except Exception as e:
        logger.exception("Career advice failed for '%s'", target)
        return (
            f"Career advice for {target!r} encountered an error"
            f" ({type(e).__name__}). Check logs for details."
        )
