"""Career intelligence tools for the ReAct agent.

Tools are organized by domain:
- profile: get/update user profile and goals
- gathering: collect data from portfolio, LinkedIn, assessments
- analysis: skill gaps, career alignment, advice
- market: job search, tech trends, salary insights, market fit/skills analysis
- financial: real-time currency conversion, purchasing power parity comparison
- generation: CV drafts and documents
- knowledge: RAG search and indexing over career data
- memory: episodic memory (decisions, applications)
"""

from .analysis import analyze_career_alignment, analyze_skill_gaps, get_career_advice
from .financial import compare_salary_ppp, convert_currency
from .gathering import (
    gather_all_career_data,
    gather_assessment_data,
    gather_cv_data,
    gather_linkedin_data,
    gather_portfolio_data,
)
from .generation import generate_cv, generate_cv_draft
from .github import get_github_profile, get_github_repo, search_github_repos
from .gitlab import get_gitlab_file, get_gitlab_project, search_gitlab_projects
from .knowledge import (
    clear_career_knowledge,
    get_knowledge_stats,
    index_career_knowledge,
    search_career_knowledge,
)
from .market import (
    analyze_market_fit,
    analyze_market_skills,
    gather_market_data,
    get_salary_insights,
    get_tech_trends,
    search_jobs,
)
from .memory import (
    get_memory_stats,
    recall_memories,
    remember_decision,
    remember_job_application,
)
from .profile import (
    get_user_profile,
    set_target_roles,
    update_current_role,
    update_salary_info,
    update_user_goal,
    update_user_name,
    update_user_skills,
)
from .settings import get_current_config, update_setting

# Single source of truth for all agent tools, organized by category.
# This structure drives tool registration, help display, and UI styling.
_TOOLS_BY_CATEGORY = {
    "profile": [
        get_user_profile,
        update_user_name,
        update_current_role,
        update_salary_info,
        update_user_skills,
        set_target_roles,
        update_user_goal,
    ],
    "gathering": [
        gather_portfolio_data,
        gather_linkedin_data,
        gather_assessment_data,
        gather_cv_data,
        gather_all_career_data,
    ],
    "github": [
        search_github_repos,
        get_github_repo,
        get_github_profile,
    ],
    "gitlab": [
        search_gitlab_projects,
        get_gitlab_project,
        get_gitlab_file,
    ],
    "knowledge": [
        search_career_knowledge,
        get_knowledge_stats,
        index_career_knowledge,
        clear_career_knowledge,
    ],
    "analysis": [
        analyze_skill_gaps,
        analyze_career_alignment,
        get_career_advice,
    ],
    "market": [
        search_jobs,
        get_tech_trends,
        get_salary_insights,
        analyze_market_fit,
        analyze_market_skills,
        gather_market_data,
    ],
    "financial": [
        convert_currency,
        compare_salary_ppp,
    ],
    "generation": [
        generate_cv,
        generate_cv_draft,
    ],
    "memory": [
        remember_decision,
        remember_job_application,
        recall_memories,
        get_memory_stats,
    ],
    "settings": [
        get_current_config,
        update_setting,
    ],
}

_ALL_TOOLS = [t for tools in _TOOLS_BY_CATEGORY.values() for t in tools]
_tool_names = [t.name for t in _ALL_TOOLS]
__all__ = [*_tool_names, "get_all_tools", "get_tool_categories"]  # pyright: ignore


def get_all_tools() -> list:
    """Get all career intelligence tools for the agent.

    Returns all 41 tools: profile, gathering, github, gitlab, analysis,
    market, financial, generation, knowledge, memory, and settings.
    """
    return list(_ALL_TOOLS)


def get_tool_categories() -> dict[str, str]:
    """Get a mapping of tool names to their categories.

    Returns:
        Mapping of tool_name -> category_name
    """
    mapping = {}
    for cat, tools in _TOOLS_BY_CATEGORY.items():
        for t in tools:
            mapping[t.name] = cat
    return mapping
