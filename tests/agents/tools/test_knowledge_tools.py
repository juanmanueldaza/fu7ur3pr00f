"""Tests for knowledge base (RAG) tools."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.tools.knowledge import (
    clear_career_knowledge,
    get_knowledge_stats,
    index_career_knowledge,
    search_career_knowledge,
)

pytestmark = pytest.mark.unit


class TestSearchCareerKnowledge:
    """Test search_career_knowledge tool."""

    def test_returns_results_when_found(self) -> None:
        mock_service = MagicMock()
        mock_service.search.return_value = [
            {
                "source": "linkedin",
                "section": "Experience",
                "content": "Software Engineer at TechCorp",
            }
        ]

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = search_career_knowledge.invoke({"query": "experience"})

        assert "Found 1 relevant results" in result
        assert "Software Engineer" in result
        mock_service.search.assert_called_once_with(
            "experience",
            limit=5,
            sources=None,
            section=None,
            include_social=False,
        )

    def test_returns_no_results_message_when_empty(self) -> None:
        mock_service = MagicMock()
        mock_service.search.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = search_career_knowledge.invoke({"query": "nonexistent"})

        assert "No results found" in result

    def test_respects_limit_parameter(self) -> None:
        mock_service = MagicMock()
        mock_service.search.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            search_career_knowledge.invoke({"query": "test", "limit": 20})

        mock_service.search.assert_called_once_with(
            "test",
            limit=20,
            sources=None,
            section=None,
            include_social=False,
        )

    def test_filters_by_source(self) -> None:
        mock_service = MagicMock()
        mock_service.search.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            search_career_knowledge.invoke({"query": "test", "sources": ["linkedin"]})

        mock_service.search.assert_called_once_with(
            "test",
            limit=5,
            sources=["linkedin"],
            section=None,
            include_social=False,
        )

    def test_filters_by_section(self) -> None:
        mock_service = MagicMock()
        mock_service.search.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            search_career_knowledge.invoke({"query": "test", "section": "Experience"})

        mock_service.search.assert_called_once_with(
            "test",
            limit=5,
            sources=None,
            section="Experience",
            include_social=False,
        )

    def test_includes_social_when_requested(self) -> None:
        mock_service = MagicMock()
        mock_service.search.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            search_career_knowledge.invoke(
                {"query": "connections", "include_social": True}
            )

        mock_service.search.assert_called_once_with(
            "connections",
            limit=5,
            sources=None,
            section=None,
            include_social=True,
        )


class TestGetKnowledgeStats:
    """Test get_knowledge_stats tool."""

    def test_returns_empty_message_when_no_chunks(self) -> None:
        mock_service = MagicMock()
        mock_service.get_stats.return_value = {"total_chunks": 0}

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = get_knowledge_stats.invoke({})

        assert "empty" in result.lower()

    def test_returns_stats_when_populated(self) -> None:
        mock_service = MagicMock()
        mock_service.get_stats.return_value = {
            "total_chunks": 150,
            "by_source": {
                "linkedin": 100,
                "portfolio": 50,
            },
        }

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = get_knowledge_stats.invoke({})

        assert "150" in result
        assert "linkedin" in result
        assert "portfolio" in result


class TestIndexCareerKnowledge:
    """Test index_career_knowledge tool."""

    def test_returns_all_sources_summary(self) -> None:
        mock_service = MagicMock()
        mock_service.index_all.return_value = {
            "linkedin": 100,
            "portfolio": 50,
        }

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = index_career_knowledge.invoke({})

        assert "150 chunks" in result
        assert "2 sources" in result

    def test_returns_specific_source_count(self) -> None:
        mock_service = MagicMock()
        mock_service.index_all.return_value = {
            "linkedin": 100,
            "portfolio": 50,
        }

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = index_career_knowledge.invoke({"source": "linkedin"})

        assert "100 chunks" in result
        assert "linkedin" in result

    def test_returns_no_data_message_for_unindexed_source(self) -> None:
        mock_service = MagicMock()
        mock_service.index_all.return_value = {
            "linkedin": 100,
            "portfolio": 0,
        }

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = index_career_knowledge.invoke({"source": "assessment"})

        assert "No data indexed" in result

    def test_returns_error_for_invalid_source(self) -> None:
        mock_service = MagicMock()
        mock_service.index_all.return_value = {}

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            result = index_career_knowledge.invoke({"source": "invalid_source"})

        assert "Invalid source" in result


class TestClearCareerKnowledge:
    """Test clear_career_knowledge tool."""

    def test_clears_all_with_approval(self) -> None:
        mock_service = MagicMock()
        mock_service.clear_all.return_value = 150

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.knowledge.interrupt",
                return_value=True,
            ):
                result = clear_career_knowledge.invoke({})

        assert "Cleared 150 chunks" in result
        mock_service.clear_all.assert_called_once()

    def test_clears_specific_source_with_approval(self) -> None:
        mock_service = MagicMock()
        mock_service.clear_source.return_value = 100

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.knowledge.interrupt",
                return_value=True,
            ):
                result = clear_career_knowledge.invoke({"source": "linkedin"})

        assert "Cleared 100 chunks" in result
        mock_service.clear_source.assert_called_once()

    def test_returns_cancel_message_without_approval(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.knowledge.interrupt",
            return_value=False,
        ):
            result = clear_career_knowledge.invoke({})

        assert "cancelled" in result.lower()

    def test_returns_error_for_invalid_source(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.knowledge.interrupt",
            return_value=True,
        ):
            result = clear_career_knowledge.invoke({"source": "invalid"})

        assert "Invalid source" in result

    def test_clear_portfolio_source(self) -> None:
        mock_service = MagicMock()
        mock_service.clear_source.return_value = 50

        with patch(
            "fu7ur3pr00f.agents.tools.knowledge._get_knowledge_service",
            return_value=mock_service,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.knowledge.interrupt",
                return_value=True,
            ):
                result = clear_career_knowledge.invoke({"source": "portfolio"})

        assert "Cleared 50 chunks" in result
        assert "portfolio" in result
