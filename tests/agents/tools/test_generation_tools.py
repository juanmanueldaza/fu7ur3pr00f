"""Tests for CV generation tools."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.tools.generation import generate_cv, generate_cv_draft

pytestmark = pytest.mark.unit


class TestGenerateCv:
    """Test generate_cv tool."""

    def test_generates_cv_when_approved(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.generation.interrupt",
            return_value=True,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.generation.create_cv",
                return_value="/path/to/cv.pdf",
            ):
                result = generate_cv.invoke(
                    {
                        "target_role": "Senior Developer",
                        "language": "en",
                        "format": "ats",
                    }
                )

        assert "CV generated successfully" in result
        assert "Senior Developer" in result
        assert "/path/to/cv.pdf" in result
        assert "ATS" in result
        assert "English" in result

    def test_generates_spanish_cv(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.generation.interrupt",
            return_value=True,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.generation.create_cv",
                return_value="/path/to/cv.pdf",
            ):
                result = generate_cv.invoke(
                    {"target_role": None, "language": "es", "format": "creative"}
                )

        assert "Spanish" in result
        assert "CREATIVE" in result

    def test_returns_cancelled_when_not_approved(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.generation.interrupt",
            return_value=False,
        ):
            result = generate_cv.invoke({})

        assert "cancelled" in result.lower()


class TestGenerateCvDraft:
    """Test generate_cv_draft tool."""

    def test_returns_draft_with_profile_data(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = "John Doe"
        mock_profile.current_role = "Software Engineer"
        mock_profile.technical_skills = ["Python", "Go", "Rust"]
        mock_profile.soft_skills = ["Leadership", "Communication"]
        mock_profile.target_roles = ["Staff Engineer"]
        mock_profile.goals = [
            MagicMock(description="Learn AI", priority="high"),
            MagicMock(description="Get promoted", priority="medium"),
        ]

        with patch(
            "fu7ur3pr00f.agents.tools.generation.get_profile",
            return_value=mock_profile,
        ):
            result = generate_cv_draft.invoke({"target_role": "Staff Engineer"})

        assert "CV Draft for Staff Engineer" in result
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python" in result
        assert "Leadership" in result
        assert "Staff Engineer" in result
        assert "Learn AI" in result
        assert "draft preview" in result.lower()

    def test_truncates_skills_to_12(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = "John"
        mock_profile.current_role = None
        mock_profile.technical_skills = [f"Skill{i}" for i in range(20)]
        mock_profile.soft_skills = []
        mock_profile.target_roles = []
        mock_profile.goals = []

        with patch(
            "fu7ur3pr00f.agents.tools.generation.get_profile",
            return_value=mock_profile,
        ):
            result = generate_cv_draft.invoke({"target_role": "Dev"})

        assert "Skill0" in result
        assert "Skill11" in result
        assert "Skill12" not in result

    def test_truncates_goals_to_3(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = "John"
        mock_profile.current_role = None
        mock_profile.technical_skills = []
        mock_profile.soft_skills = []
        mock_profile.target_roles = []
        mock_profile.goals = [
            MagicMock(description=f"Goal {i}", priority="high") for i in range(5)
        ]

        with patch(
            "fu7ur3pr00f.agents.tools.generation.get_profile",
            return_value=mock_profile,
        ):
            result = generate_cv_draft.invoke({"target_role": "Dev"})

        assert "Goal 0" in result
        assert "Goal 2" in result
        assert "Goal 3" not in result

    def test_returns_error_when_no_profile(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = ""

        with patch(
            "fu7ur3pr00f.agents.tools.generation.get_profile",
            return_value=mock_profile,
        ):
            result = generate_cv_draft.invoke({"target_role": "Dev"})

        assert "Cannot generate a CV without profile" in result

    def test_handles_missing_optional_fields(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = "John"
        mock_profile.current_role = None
        mock_profile.technical_skills = []
        mock_profile.soft_skills = []
        mock_profile.target_roles = []
        mock_profile.goals = []

        with patch(
            "fu7ur3pr00f.agents.tools.generation.get_profile",
            return_value=mock_profile,
        ):
            result = generate_cv_draft.invoke({"target_role": "Dev"})

        assert "John" in result
        assert "Technical Skills" not in result
        assert "Soft Skills" not in result
