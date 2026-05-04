"""Tests for data loading utilities."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.utils.data_loader import (
    combine_career_data,
    load_career_data,
    load_career_data_for_analysis,
    load_career_data_for_cv,
)

pytestmark = pytest.mark.unit

_PATCH_TARGET = "fu7ur3pr00f.utils.data_loader.get_knowledge_store"


@pytest.fixture
def sample_career_data() -> dict[str, str]:
    return {
        "linkedin_data": ("# LinkedIn Profile\n\nSoftware Engineer with 5 years experience."),
        "portfolio_data": ("# Portfolio\n\n## About\nFull-stack developer passionate about AI."),
    }


class TestLoadCareerData:
    def test_returns_empty_dict_when_no_data(self) -> None:
        mock_store = MagicMock()
        mock_store.get_all_content.return_value = ""
        with patch(_PATCH_TARGET, return_value=mock_store):
            result = load_career_data()
            assert result == {}

    def test_returns_data_from_knowledge_base(self) -> None:
        mock_store = MagicMock()
        mock_store.get_all_content.side_effect = lambda source: {
            "linkedin": "# LinkedIn\nSoftware Engineer",
            "portfolio": "# Portfolio\nDeveloper",
            "assessment": "",
        }.get(
            {"linkedin": "linkedin", "portfolio": "portfolio", "assessment": "assessment"}.get(
                getattr(source, "value", ""), ""
            ),
            "",
        )

        with patch(_PATCH_TARGET, return_value=mock_store):
            result = load_career_data()
            assert "linkedin_data" in result or "portfolio_data" in result


class TestLoadCareerDataForAnalysis:
    def test_returns_empty_dict_when_no_data(self) -> None:
        mock_store = MagicMock()
        mock_store.get_filtered_content.return_value = ""
        mock_store.get_all_content.return_value = ""
        with patch(_PATCH_TARGET, return_value=mock_store):
            result = load_career_data_for_analysis()
            assert result == {}


class TestLoadCareerDataForCV:
    def test_returns_empty_string_when_no_data(self) -> None:
        mock_store = MagicMock()
        mock_store.get_filtered_content.return_value = ""
        mock_store.get_all_content.return_value = ""
        with patch(_PATCH_TARGET, return_value=mock_store):
            result = load_career_data_for_cv()
            assert result == ""

    def test_returns_string_not_dict(self) -> None:
        mock_store = MagicMock()
        mock_store.get_filtered_content.return_value = "## LinkedIn\n\nPortfolio content"
        mock_store.get_all_content.return_value = "## Assessment\n\nStrengths"
        with patch(_PATCH_TARGET, return_value=mock_store):
            result = load_career_data_for_cv()
            assert isinstance(result, str)


class TestCombineCareerData:
    def test_combines_all_data_sources(self, sample_career_data: dict[str, str]) -> None:
        result = combine_career_data(sample_career_data)
        assert "LinkedIn" in result
        assert "Portfolio" in result

    def test_uses_custom_header_prefix(self, sample_career_data: dict[str, str]) -> None:
        result = combine_career_data(sample_career_data, header_prefix="###")
        assert "### LinkedIn" in result
        assert "### Portfolio" in result

    def test_excludes_analysis_by_default(self) -> None:
        data = {
            "linkedin_data": "LinkedIn content",
            "analysis": "Previous analysis content",
        }
        result = combine_career_data(data)
        assert "LinkedIn" in result
        assert "Previous Analysis" not in result

    def test_includes_analysis_when_requested(self) -> None:
        data = {
            "linkedin_data": "LinkedIn content",
            "analysis": "Previous analysis content",
        }
        result = combine_career_data(data, include_analysis=True)
        assert "LinkedIn" in result
        assert "Previous Analysis" in result

    def test_handles_empty_data(self) -> None:
        result = combine_career_data({})
        assert result == ""

    def test_handles_none_values(self) -> None:
        data = {
            "linkedin_data": "Has content",
            "portfolio_data": None,
        }
        result = combine_career_data(data)
        assert "LinkedIn" in result
        assert "Portfolio" not in result

    def test_preserves_content(self, sample_career_data: dict[str, str]) -> None:
        result = combine_career_data(sample_career_data)
        assert "Software Engineer with 5 years" in result
        assert "passionate about AI" in result
