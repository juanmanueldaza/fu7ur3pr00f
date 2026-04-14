"""Tests for profile management tools."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.tools.profile import (
    get_user_profile,
    set_target_roles,
    update_current_role,
    update_salary_info,
    update_user_goal,
    update_user_name,
    update_user_skills,
)

pytestmark = pytest.mark.unit


class TestGetUserProfile:
    """Test get_user_profile tool."""

    def test_returns_summary_when_profile_has_name(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = "John Doe"
        mock_profile.summary.return_value = "John Doe - Software Engineer"

        with patch(
            "fu7ur3pr00f.agents.tools.profile.get_profile",
            return_value=mock_profile,
        ):
            result = get_user_profile.invoke({})

        assert "John Doe" in result
        mock_profile.summary.assert_called_once()

    def test_returns_setup_message_when_profile_empty(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = ""

        with patch(
            "fu7ur3pr00f.agents.tools.profile.get_profile",
            return_value=mock_profile,
        ):
            result = get_user_profile.invoke({})

        assert "No profile configured" in result
        mock_profile.summary.assert_not_called()

    def test_returns_setup_message_when_name_is_none(self) -> None:
        mock_profile = MagicMock()
        mock_profile.name = None

        with patch(
            "fu7ur3pr00f.agents.tools.profile.get_profile",
            return_value=mock_profile,
        ):
            result = get_user_profile.invoke({})

        assert "No profile configured" in result


class TestUpdateUserGoal:
    """Test update_user_goal tool."""

    def test_adds_goal_with_default_priority(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = update_user_goal.invoke({"goal_description": "Become a tech lead"})

        assert "Become a tech lead" in result
        assert "medium" in result
        mock_edit.assert_called_once()

    def test_adds_goal_with_custom_priority(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = update_user_goal.invoke(
                {"goal_description": "Learn Rust", "priority": "high"}
            )

        assert "Learn Rust" in result
        assert "high" in result
        mock_edit.assert_called_once()


class TestUpdateUserSkills:
    """Test update_user_skills tool."""

    def test_adds_technical_skills(self) -> None:
        def mock_edit(fn):
            profile = MagicMock()
            profile.technical_skills = ["Go", "Python", "Rust", "TypeScript"]
            profile.soft_skills = []
            fn(profile)
            return profile

        with patch(
            "fu7ur3pr00f.agents.tools.profile.edit_profile",
            side_effect=mock_edit,
        ):
            result = update_user_skills.invoke(
                {"skills": ["Rust", "TypeScript"], "skill_type": "technical"}
            )

        assert "Rust" in result
        assert "TypeScript" in result
        assert "technical" in result

    def test_adds_soft_skills(self) -> None:
        def mock_edit(fn):
            profile = MagicMock()
            profile.technical_skills = []
            profile.soft_skills = ["Communication", "Leadership"]
            fn(profile)
            return profile

        with patch(
            "fu7ur3pr00f.agents.tools.profile.edit_profile",
            side_effect=mock_edit,
        ):
            result = update_user_skills.invoke(
                {"skills": ["Leadership"], "skill_type": "soft"}
            )

        assert "Leadership" in result
        assert "soft" in result

    def test_merges_with_existing_skills(self) -> None:
        mock_profile = MagicMock()
        mock_profile.technical_skills = ["Python", "Rust", "TypeScript"]
        mock_profile.soft_skills = []

        with patch(
            "fu7ur3pr00f.agents.tools.profile.edit_profile",
            return_value=mock_profile,
        ):
            result = update_user_skills.invoke(
                {"skills": ["Rust"], "skill_type": "technical"}
            )

        assert "Python" in result
        assert "Rust" in result


class TestSetTargetRoles:
    """Test set_target_roles tool."""

    def test_sets_roles(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = set_target_roles.invoke(
                {"roles": ["Senior Engineer", "Staff Engineer"]}
            )

        assert "Senior Engineer" in result
        assert "Staff Engineer" in result
        mock_edit.assert_called_once()


class TestUpdateUserName:
    """Test update_user_name tool."""

    def test_updates_name(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = update_user_name.invoke({"name": "Jane Smith"})

        assert "Jane Smith" in result
        mock_edit.assert_called_once()


class TestUpdateCurrentRole:
    """Test update_current_role tool."""

    def test_updates_role_without_experience(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = update_current_role.invoke({"role": "Senior Developer"})

        assert "Senior Developer" in result
        assert "years" not in result
        mock_edit.assert_called_once()

    def test_updates_role_with_experience(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = update_current_role.invoke(
                {"role": "Staff Engineer", "years_experience": 8}
            )

        assert "Staff Engineer" in result
        assert "8 years" in result
        mock_edit.assert_called_once()


class TestUpdateSalaryInfo:
    """Test update_salary_info tool."""

    def test_updates_salary_basic(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile") as mock_edit:
            result = update_salary_info.invoke({"current_salary": "95000"})

        assert "Saved current compensation" in result
        assert "95000" in result
        assert "USD" in result
        mock_edit.assert_called_once()

    def test_updates_salary_with_currency(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile"):
            result = update_salary_info.invoke(
                {"current_salary": "80000", "currency": "EUR"}
            )

        assert "EUR" in result
        assert "80000" in result

    def test_updates_salary_with_bonus(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.profile.edit_profile"):
            result = update_salary_info.invoke(
                {
                    "current_salary": "120000",
                    "includes_bonus": True,
                    "notes": "plus 10% annual bonus",
                }
            )

        assert "includes bonus/equity" in result
        assert "plus 10% annual bonus" in result
