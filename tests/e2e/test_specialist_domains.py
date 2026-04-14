"""E2E tests for each specialist domain.

Verify that each specialist can:
1. Be instantiated
2. Receive a blackboard query
3. Call contribute() (with mocked LLM)
4. Return a valid SpecialistFinding
"""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.blackboard.blackboard import make_initial_blackboard
from fu7ur3pr00f.agents.specialists.coach import CoachAgent
from fu7ur3pr00f.agents.specialists.code import CodeAgent
from fu7ur3pr00f.agents.specialists.founder import FounderAgent
from fu7ur3pr00f.agents.specialists.jobs import JobsAgent
from fu7ur3pr00f.agents.specialists.learning import LearningAgent

pytestmark = pytest.mark.integration


class TestCoachSpecialistE2E:
    """End-to-end tests for Coach specialist."""

    def test_contribute_with_mocked_llm(self):
        """Coach contribute() should return a valid finding."""
        agent = CoachAgent()
        blackboard = make_initial_blackboard(
            query="How do I get promoted to Staff Engineer?",
            user_profile={
                "name": "Test User",
                "current_role": "Senior Engineer",
                "years_experience": 5,
                "technical_skills": ["Python", "Go"],
            },
        )

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Focus on leadership and ML skills."
        mock_model.bind_tools.return_value = mock_model
        mock_model.invoke.return_value = mock_response

        mock_extractor = MagicMock()
        mock_finding = MagicMock()
        mock_finding.model_dump.return_value = {
            "reasoning": "Focus on leadership and ML skills.",
            "confidence": 0.8,
        }
        mock_extractor.invoke.return_value = mock_finding

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            mock_model.with_structured_output.return_value = mock_extractor
            finding = agent.contribute(blackboard)

        assert isinstance(finding, dict)
        assert "reasoning" in finding
        assert "confidence" in finding

    def test_has_required_tools(self):
        """Coach has analysis and gathering tools."""
        agent = CoachAgent()
        tool_names = {t.name for t in agent.tools}
        assert "get_career_advice" in tool_names
        assert "analyze_skill_gaps" in tool_names


class TestJobsSpecialistE2E:
    """End-to-end tests for Jobs specialist."""

    def test_contribute_with_mocked_llm(self):
        """Jobs contribute() should return a valid finding."""
        agent = JobsAgent()
        blackboard = make_initial_blackboard(
            query="Find remote Python developer jobs",
            user_profile={
                "name": "Test User",
                "current_role": "Python Developer",
                "technical_skills": ["Python", "Django"],
            },
        )

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Strong market for Python developers."
        mock_model.bind_tools.return_value = mock_model
        mock_model.invoke.return_value = mock_response

        mock_extractor = MagicMock()
        mock_finding = MagicMock()
        mock_finding.model_dump.return_value = {
            "reasoning": "Strong market for Python developers.",
            "confidence": 0.75,
        }
        mock_extractor.invoke.return_value = mock_finding

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            mock_model.with_structured_output.return_value = mock_extractor
            finding = agent.contribute(blackboard)

        assert isinstance(finding, dict)
        assert "reasoning" in finding

    def test_has_job_search_tools(self):
        """Jobs has search_jobs and salary tools."""
        agent = JobsAgent()
        tool_names = {t.name for t in agent.tools}
        assert "search_jobs" in tool_names
        assert "compare_salary_ppp" in tool_names


class TestLearningSpecialistE2E:
    """End-to-end tests for Learning specialist."""

    def test_contribute_with_mocked_llm(self):
        """Learning contribute() should return a valid finding."""
        agent = LearningAgent()
        blackboard = make_initial_blackboard(
            query="I want to learn machine learning",
            user_profile={
                "name": "Test User",
                "technical_skills": ["Python"],
            },
        )

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Start with Python ML fundamentals."
        mock_model.bind_tools.return_value = mock_model
        mock_model.invoke.return_value = mock_response

        mock_extractor = MagicMock()
        mock_finding = MagicMock()
        mock_finding.model_dump.return_value = {
            "reasoning": "Start with Python ML fundamentals.",
            "confidence": 0.85,
        }
        mock_extractor.invoke.return_value = mock_finding

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            mock_model.with_structured_output.return_value = mock_extractor
            finding = agent.contribute(blackboard)

        assert isinstance(finding, dict)
        assert "reasoning" in finding

    def test_has_learning_tools(self):
        """Learning has tech trends and learning tools."""
        agent = LearningAgent()
        tool_names = {t.name for t in agent.tools}
        assert "get_tech_trends" in tool_names


class TestCodeSpecialistE2E:
    """End-to-end tests for Code specialist."""

    def test_contribute_with_mocked_llm(self):
        """Code contribute() should return a valid finding."""
        agent = CodeAgent()
        blackboard = make_initial_blackboard(
            query="Review my GitHub repos",
            user_profile={
                "name": "Test User",
                "github_username": "testuser",
                "technical_skills": ["Python", "JavaScript"],
            },
        )

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Strong portfolio with clean repos."
        mock_model.bind_tools.return_value = mock_model
        mock_model.invoke.return_value = mock_response

        mock_extractor = MagicMock()
        mock_finding = MagicMock()
        mock_finding.model_dump.return_value = {
            "reasoning": "Strong portfolio with clean repos.",
            "confidence": 0.8,
        }
        mock_extractor.invoke.return_value = mock_finding

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            mock_model.with_structured_output.return_value = mock_extractor
            finding = agent.contribute(blackboard)

        assert isinstance(finding, dict)
        assert "reasoning" in finding

    def test_has_code_tools(self):
        """Code has GitHub and GitLab tools."""
        agent = CodeAgent()
        tool_names = {t.name for t in agent.tools}
        assert "get_github_profile" in tool_names
        assert "search_gitlab_projects" in tool_names


class TestFounderSpecialistE2E:
    """End-to-end tests for Founder specialist."""

    def test_contribute_with_mocked_llm(self):
        """Founder contribute() should return a valid finding."""
        agent = FounderAgent()
        blackboard = make_initial_blackboard(
            query="How do I launch my SaaS startup?",
            user_profile={
                "name": "Test User",
                "current_role": "Senior Engineer",
                "technical_skills": ["Python", "React"],
            },
        )

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = "Validate your idea with an MVP first."
        mock_model.bind_tools.return_value = mock_model
        mock_model.invoke.return_value = mock_response

        mock_extractor = MagicMock()
        mock_finding = MagicMock()
        mock_finding.model_dump.return_value = {
            "reasoning": "Validate your idea with an MVP first.",
            "confidence": 0.78,
        }
        mock_extractor.invoke.return_value = mock_finding

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            mock_model.with_structured_output.return_value = mock_extractor
            finding = agent.contribute(blackboard)

        assert isinstance(finding, dict)
        assert "reasoning" in finding

    def test_has_founder_tools(self):
        """Founder has market analysis and financial tools."""
        agent = FounderAgent()
        tool_names = {t.name for t in agent.tools}
        assert "analyze_market_fit" in tool_names
        assert "convert_currency" in tool_names
