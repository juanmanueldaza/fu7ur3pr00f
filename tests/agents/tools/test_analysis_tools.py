"""Tests for analysis tools."""

from unittest.mock import MagicMock, patch

from fu7ur3pr00f.agents.tools.analysis import (
    analyze_career_alignment,
    analyze_skill_gaps,
    get_career_advice,
)
from fu7ur3pr00f.container import container


class TestAnalyzeSkillGaps:
    """Test analyze_skill_gaps tool."""

    def test_returns_analysis_on_success(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            return_value="You need to learn Kubernetes and Docker.",
        ):
            result = analyze_skill_gaps.invoke({"target_role": "DevOps Engineer"})

        assert "DevOps Engineer" in result
        assert "Kubernetes" in result

    def test_returns_fallback_when_no_skills(self) -> None:
        mock_profile = MagicMock()
        mock_profile.technical_skills = []
        mock_profile.soft_skills = []

        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            side_effect=RuntimeError("KB unavailable"),
        ):
            with patch.object(
                container,
                "_profile",
                mock_profile,
            ):
                result = analyze_skill_gaps.invoke({"target_role": "ML Engineer"})

        assert "no skills recorded" in result

    def test_returns_partial_analysis_when_kb_unavailable(self) -> None:
        mock_profile = MagicMock()
        mock_profile.technical_skills = ["Python", "Go"]
        mock_profile.soft_skills = ["Communication"]

        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            side_effect=RuntimeError("KB unavailable"),
        ):
            with patch.object(
                container,
                "_profile",
                mock_profile,
            ):
                result = analyze_skill_gaps.invoke({"target_role": "ML Engineer"})

        assert "Python" in result
        assert "Full analysis requires" in result


class TestAnalyzeCareerAlignment:
    """Test analyze_career_alignment tool."""

    def test_returns_analysis_on_success(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            return_value="Your goals align well with market demands.",
        ):
            result = analyze_career_alignment.invoke({})

        assert "Career alignment analysis" in result
        assert "align well" in result

    def test_returns_error_message_on_failure(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            side_effect=RuntimeError("Service unavailable"),
        ):
            result = analyze_career_alignment.invoke({})

        assert "encountered an error" in result


class TestGetCareerAdvice:
    """Test get_career_advice tool."""

    def test_returns_advice_on_success(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            return_value="Focus on building a strong portfolio.",
        ):
            result = get_career_advice.invoke({"target": "transition to AI"})

        assert "transition to AI" in result
        assert "portfolio" in result

    def test_returns_error_message_on_failure(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.analysis.invoke_with_context",
            side_effect=ValueError("Invalid prompt"),
        ):
            result = get_career_advice.invoke({"target": "become CTO"})

        assert "encountered an error" in result
