"""Analysis tools for the career agent."""

import logging

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from fu7ur3pr00f.llm.fallback import get_model_with_fallback
from fu7ur3pr00f.memory.profile import load_profile
from fu7ur3pr00f.services.knowledge_service import KnowledgeService

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
        profile = load_profile()
        service = KnowledgeService()

        career_data = service.search(f"skills experience {target_role}", limit=10)
        career_context = (
            "\n".join(f"- {r.content}" for r in career_data)
            if career_data
            else "No career data available."
        )

        prompt = (
            f"Analyze skill gaps for the target role: {target_role}\n\n"
            f"User profile:\n{profile.summary()}\n\n"
            f"Career context:\n{career_context}\n\n"
            f"Provide a concise gap analysis with 3-5 key areas to improve."
        )

        model, _ = get_model_with_fallback(purpose="analysis")
        result = model.invoke([HumanMessage(content=prompt)])

        return f"Skill gap analysis for {target_role!r}:\n\n{result.content}"

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
        profile = load_profile()
        service = KnowledgeService()

        career_data = service.search("career goals trajectory alignment", limit=15)
        career_context = (
            "\n".join(f"- {r.content}" for r in career_data)
            if career_data
            else "No career data available."
        )

        prompt = (
            f"Analyze career alignment for this profile:\n"
            f"{profile.summary()}\n\n"
            f"Career context:\n{career_context}\n\n"
            f"Assess how well their current trajectory aligns with goals. "
            f"Identify strengths and misalignments. Suggest adjustments."
        )

        model, _ = get_model_with_fallback(purpose="analysis")
        result = model.invoke([HumanMessage(content=prompt)])

        return f"Career alignment analysis:\n\n{result.content}"

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
        profile = load_profile()
        service = KnowledgeService()

        career_data = service.search(target, limit=10)
        career_context = (
            "\n".join(f"- {r.content}" for r in career_data)
            if career_data
            else "No career data available."
        )

        prompt = (
            f"Provide strategic career advice for: {target}\n\n"
            f"User profile:\n{profile.summary()}\n\n"
            f"Relevant context:\n{career_context}\n\n"
            f"Give actionable, specific advice with concrete next steps."
        )

        model, _ = get_model_with_fallback(purpose="analysis")
        result = model.invoke([HumanMessage(content=prompt)])

        return f"Career advice for {target!r}:\n\n{result.content}"

    except Exception as e:
        logger.exception("Career advice failed for '%s'", target)
        return (
            f"Career advice for {target!r} encountered an error"
            f" ({type(e).__name__}). Check logs for details."
        )
