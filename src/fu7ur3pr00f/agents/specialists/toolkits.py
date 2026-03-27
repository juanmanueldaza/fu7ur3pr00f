"""Shared tool groupings for specialist agents.

Single source of truth for base toolkit and per-specialist extensions.
"""

from fu7ur3pr00f.agents.tools.analysis import (
    analyze_career_alignment,
    analyze_skill_gaps,
    get_career_advice,
)
from fu7ur3pr00f.agents.tools.financial import compare_salary_ppp, convert_currency
from fu7ur3pr00f.agents.tools.gathering import (
    gather_all_career_data,
    gather_assessment_data,
    gather_cv_data,
    gather_linkedin_data,
    gather_portfolio_data,
)
from fu7ur3pr00f.agents.tools.generation import generate_cv, generate_cv_draft
from fu7ur3pr00f.agents.tools.github import (
    get_github_profile,
    get_github_repo,
    search_github_repos,
)
from fu7ur3pr00f.agents.tools.gitlab import (
    get_gitlab_file,
    get_gitlab_project,
    search_gitlab_projects,
)
from fu7ur3pr00f.agents.tools.knowledge import (
    clear_career_knowledge,
    get_knowledge_stats,
    index_career_knowledge,
    search_career_knowledge,
)
from fu7ur3pr00f.agents.tools.market import (
    analyze_market_fit,
    analyze_market_skills,
    gather_market_data,
    get_salary_insights,
    get_tech_trends,
    search_jobs,
)
from fu7ur3pr00f.agents.tools.memory import (
    get_memory_stats,
    recall_memories,
    remember_decision,
    remember_job_application,
)
from fu7ur3pr00f.agents.tools.profile import (
    get_user_profile,
    set_target_roles,
    update_current_role,
    update_salary_info,
    update_user_goal,
    update_user_name,
    update_user_skills,
)
from fu7ur3pr00f.agents.tools.settings import get_current_config, update_setting

# Shared across ALL specialists
BASE_TOOLKIT: list = [
    # Profile
    get_user_profile,
    update_user_name,
    update_current_role,
    update_salary_info,
    update_user_skills,
    set_target_roles,
    update_user_goal,
    # Gathering
    gather_portfolio_data,
    gather_linkedin_data,
    gather_assessment_data,
    gather_cv_data,
    gather_all_career_data,
    # Knowledge
    search_career_knowledge,
    get_knowledge_stats,
    index_career_knowledge,
    clear_career_knowledge,
    # Memory
    remember_decision,
    remember_job_application,
    recall_memories,
    get_memory_stats,
    # Settings
    get_current_config,
    update_setting,
]

COACH_TOOLS: list = BASE_TOOLKIT + [
    analyze_skill_gaps,
    analyze_career_alignment,
    get_career_advice,
    generate_cv,
    generate_cv_draft,
]

JOBS_TOOLS: list = BASE_TOOLKIT + [
    analyze_skill_gaps,
    analyze_career_alignment,
    get_career_advice,
    search_jobs,
    get_salary_insights,
    analyze_market_fit,
    analyze_market_skills,
    get_tech_trends,
    gather_market_data,
    convert_currency,
    compare_salary_ppp,
    generate_cv,
    generate_cv_draft,
]

CODE_TOOLS: list = BASE_TOOLKIT + [
    search_github_repos,
    get_github_repo,
    get_github_profile,
    search_gitlab_projects,
    get_gitlab_project,
    get_gitlab_file,
    get_tech_trends,
]

FOUNDER_TOOLS: list = BASE_TOOLKIT + [
    analyze_skill_gaps,
    analyze_career_alignment,
    get_career_advice,
    search_jobs,
    get_salary_insights,
    analyze_market_fit,
    analyze_market_skills,
    get_tech_trends,
    gather_market_data,
    convert_currency,
    compare_salary_ppp,
]

LEARNING_TOOLS: list = BASE_TOOLKIT + [
    analyze_skill_gaps,
    get_tech_trends,
    analyze_market_skills,
    generate_cv,
    generate_cv_draft,
]
