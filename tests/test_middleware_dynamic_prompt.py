"""Tests for build_dynamic_prompt middleware."""

from typing import Any, cast
from unittest.mock import MagicMock, PropertyMock, patch

from langchain.agents.middleware.types import AgentState, ModelRequest
from langchain_core.messages import HumanMessage, SystemMessage

from fu7ur3pr00f.agents.middleware import _invalidate_prompt_cache, build_dynamic_prompt

pytestmark = __import__("pytest").mark.unit


def _make_state(messages: list[Any]) -> AgentState[Any]:
    """Build a minimal AgentState dict."""
    return cast(AgentState[Any], {"messages": messages})


class TestBuildDynamicPrompt:
    """Tests for build_dynamic_prompt middleware."""

    def setup_method(self):
        _invalidate_prompt_cache()

    def teardown_method(self):
        _invalidate_prompt_cache()

    def _call_middleware(self, mock_profile, mock_stats):
        """Invoke wrap_model_call and capture the system message passed to handler."""
        captured = {}

        def handler(request):
            captured["system_message"] = request.system_message
            return MagicMock()

        request = ModelRequest(
            model=MagicMock(),
            messages=[HumanMessage(content="hello")],
            system_message=SystemMessage(content="original"),
        )

        # Create mock service that returns mock_stats from get_stats()
        mock_service = MagicMock()
        mock_service.get_stats.return_value = mock_stats

        with (
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=mock_profile,
            ),
            patch(
                "fu7ur3pr00f.container.Container.knowledge_service",
                new_callable=PropertyMock,
                return_value=mock_service,
            ),
        ):
            build_dynamic_prompt.wrap_model_call(request, handler)

        return captured["system_message"].content

    def test_with_data_available(self):
        """Dynamic prompt includes knowledge base stats when data exists."""
        profile = MagicMock()
        profile.name = "Juan"
        profile.summary.return_value = "Name: Juan\nRole: Engineer"

        stats = {
            "total_chunks": 350,
            "by_source": {"linkedin": 280, "portfolio": 45, "assessment": 25},
        }

        content = self._call_middleware(profile, stats)
        assert "Name: Juan" in content
        assert "linkedin: 280 chunks" in content
        assert "portfolio: 45 chunks" in content
        assert "assessment: 25 chunks" in content
        assert "do not ask the user" in content.lower()

    def test_with_no_data(self):
        """Dynamic prompt indicate no data when knowledge base is empty."""
        profile = MagicMock()
        profile.name = None
        profile.summary.return_value = "No profile information available."

        stats = {"total_chunks": 0, "by_source": {}}

        content = self._call_middleware(profile, stats)
        # Profile context replaced when summary indicates no data
        assert "No career data indexed" in content
        assert "gather_all_career_data" in content

    def test_partial_sources(self):
        """Only lists sources that have chunks in the data availability section."""
        profile = MagicMock()
        profile.name = "Ana"
        profile.summary.return_value = "Name: Ana"

        stats = {
            "total_chunks": 100,
            "by_source": {"linkedin": 100, "portfolio": 0, "assessment": 0},
        }

        content = self._call_middleware(profile, stats)
        assert "linkedin: 100 chunks" in content
        # Zero-chunk sources should not appear in the data availability section
        assert "portfolio: 0" not in content
        assert "assessment: 0" not in content

    def test_ttl_cache_avoids_repeated_io(self):
        """Second call within TTL reuses cached prompt, no extra I/O."""
        profile = MagicMock()
        profile.name = "Juan"
        profile.summary.return_value = "Name: Juan"
        stats = {"total_chunks": 10, "by_source": {"linkedin": 10}}

        mock_get_stats = MagicMock(return_value=stats)

        def handler(request):
            return MagicMock()

        request = ModelRequest(
            model=MagicMock(),
            messages=[HumanMessage(content="hello")],
            system_message=SystemMessage(content="original"),
        )

        # Create mock service
        mock_service = MagicMock()
        mock_service.get_stats = mock_get_stats

        with (
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=profile,
            ),
            patch(
                "fu7ur3pr00f.container.Container.knowledge_service",
                new_callable=PropertyMock,
                return_value=mock_service,
            ),
        ):
            # First call — should build prompt
            build_dynamic_prompt.wrap_model_call(
                request,
                handler,
            )
            assert mock_get_stats.call_count == 1

            # Second call — should hit cache
            build_dynamic_prompt.wrap_model_call(
                request,
                handler,
            )
            assert mock_get_stats.call_count == 1  # Still 1, cached

    def test_get_stats_called_once_per_invocation(self):
        """get_stats is called exactly once (not twice) per build."""
        profile = MagicMock()
        profile.summary.return_value = "No profile information available."
        stats = {"total_chunks": 0, "by_source": {}}

        mock_get_stats = MagicMock(return_value=stats)
        mock_service = MagicMock()
        mock_service.get_stats = mock_get_stats

        def handler(request):
            return MagicMock()

        request = ModelRequest(
            model=MagicMock(),
            messages=[HumanMessage(content="hello")],
            system_message=SystemMessage(content="original"),
        )

        with (
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=profile,
            ),
            patch(
                "fu7ur3pr00f.container.Container.knowledge_service",
                new_callable=PropertyMock,
                return_value=mock_service,
            ),
        ):
            build_dynamic_prompt.wrap_model_call(
                request,
                handler,
            )
            assert mock_get_stats.call_count == 1
