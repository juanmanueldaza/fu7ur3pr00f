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

_PATCH_TARGET = "fu7ur3pr00f.utils.data_loader.get_knowledge_service"


class TestLoadCareerData:
    """Test load_career_data function (queries ChromaDB via KnowledgeService)."""

    def test_returns_empty_dict_when_no_data(self) -> None:
        """Test returns empty dict when knowledge base is empty."""
        mock_service = MagicMock()
        mock_service.get_all_content.return_value = {}
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data()
            assert result == {}

    def test_returns_data_from_knowledge_base(self) -> None:
        """Test returns data from knowledge base."""
        expected = {
            "linkedin_data": "# LinkedIn\nSoftware Engineer",
            "portfolio_data": "# Portfolio\nDeveloper",
        }
        mock_service = MagicMock()
        mock_service.get_all_content.return_value = expected
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data()
            assert result == expected

    def test_only_includes_sources_with_content(self) -> None:
        """Test only includes sources that have indexed content."""
        mock_service = MagicMock()
        mock_service.get_all_content.return_value = {
            "portfolio_data": "# Portfolio\nContent"
        }
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data()
            assert "portfolio_data" in result
            assert "linkedin_data" not in result


class TestLoadCareerDataForAnalysis:
    """Test load_career_data_for_analysis function (filtered loading)."""

    def test_returns_empty_dict_when_no_data(self) -> None:
        """Test returns empty dict when knowledge base is empty."""
        mock_service = MagicMock()
        mock_service.get_filtered_content.return_value = {}
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data_for_analysis()
            assert result == {}

    def test_returns_filtered_data(self) -> None:
        """Test returns filtered data from knowledge base."""
        expected = {
            "linkedin_data": "Experience content only",
            "portfolio_data": "Portfolio content",
        }
        mock_service = MagicMock()
        mock_service.get_filtered_content.return_value = expected
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data_for_analysis()
            assert result == expected


class TestLoadCareerDataForCV:
    """Test load_career_data_for_cv function (uses filtered data)."""

    def test_returns_empty_string_when_no_data(self) -> None:
        """Test returns empty string when no data exists."""
        mock_service = MagicMock()
        mock_service.get_filtered_content.return_value = {}
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data_for_cv()
            assert result == ""

    def test_includes_section_headers(self) -> None:
        """Test includes section headers for each source."""
        mock_service = MagicMock()
        mock_service.get_filtered_content.return_value = {
            "linkedin_data": "LinkedIn content",
            "portfolio_data": "Portfolio content",
        }
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data_for_cv()
            assert "### LinkedIn" in result
            assert "### Portfolio" in result

    def test_returns_string_not_dict(self) -> None:
        """Test returns combined string, not dict."""
        mock_service = MagicMock()
        mock_service.get_filtered_content.return_value = {
            "portfolio_data": "Portfolio content",
        }
        with patch(_PATCH_TARGET, return_value=mock_service):
            result = load_career_data_for_cv()
            assert isinstance(result, str)


class TestCombineCareerData:
    """Test combine_career_data function."""

    def test_combines_all_data_sources(
        self, sample_career_data: dict[str, str]
    ) -> None:
        """Test combines all provided data sources."""
        result = combine_career_data(sample_career_data)

        assert "LinkedIn" in result
        assert "Portfolio" in result

    def test_uses_custom_header_prefix(
        self, sample_career_data: dict[str, str]
    ) -> None:
        """Test uses custom header prefix."""
        result = combine_career_data(sample_career_data, header_prefix="###")

        assert "### LinkedIn" in result
        assert "### Portfolio" in result

    def test_excludes_analysis_by_default(self) -> None:
        """Test excludes analysis field by default."""
        data = {
            "linkedin_data": "LinkedIn content",
            "analysis": "Previous analysis content",
        }
        result = combine_career_data(data)

        assert "LinkedIn" in result
        assert "Previous Analysis" not in result

    def test_includes_analysis_when_requested(self) -> None:
        """Test includes analysis when include_analysis=True."""
        data = {
            "linkedin_data": "LinkedIn content",
            "analysis": "Previous analysis content",
        }
        result = combine_career_data(data, include_analysis=True)

        assert "LinkedIn" in result
        assert "Previous Analysis" in result

    def test_handles_empty_data(self) -> None:
        """Test handles empty data dict."""
        result = combine_career_data({})
        assert result == ""

    def test_handles_partial_data(self) -> None:
        """Test handles partial data (some sources missing)."""
        data = {"portfolio_data": "Only portfolio data"}
        result = combine_career_data(data)

        assert "Portfolio" in result
        assert "LinkedIn" not in result

    def test_handles_none_values(self) -> None:
        """Test handles None values in data."""
        data = {
            "linkedin_data": "Has content",
            "portfolio_data": None,
        }
        result = combine_career_data(data)

        assert "LinkedIn" in result
        assert "Portfolio" not in result

    def test_preserves_content(self, sample_career_data: dict[str, str]) -> None:
        """Test preserves actual content from sources."""
        result = combine_career_data(sample_career_data)

        assert "Software Engineer with 5 years" in result
        assert "passionate about AI" in result
