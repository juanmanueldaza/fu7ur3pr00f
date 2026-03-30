"""Tests for interactive chat command handlers."""

from unittest.mock import MagicMock, patch

from fu7ur3pr00f.chat.client import _cmd_gather


class TestGatherCommand:
    def test_gather_auto_populates_profile_and_invalidates_prompt_cache(self):
        mock_service = MagicMock()
        mock_service.gather_all.return_value = {
            "portfolio": True,
            "linkedin": True,
            "assessment": True,
        }

        with (
            patch("fu7ur3pr00f.chat.client.console.print"),
            patch(
                "fu7ur3pr00f.services.gatherer_service.GathererService",
                return_value=mock_service,
            ),
            patch(
                "fu7ur3pr00f.agents.tools.gathering._auto_populate_profile",
                return_value="Auto-populated profile: name=Juan",
            ) as auto_populate,
            patch("fu7ur3pr00f.utils.services.reload_profile") as reload_profile,
            patch(
                "fu7ur3pr00f.agents.middleware.invalidate_prompt_cache"
            ) as invalidate_prompt_cache,
        ):
            result = _cmd_gather({}, "")

        assert result is False
        mock_service.gather_all.assert_called_once_with(verbose=True)
        auto_populate.assert_called_once_with()
        reload_profile.assert_called_once_with()
        invalidate_prompt_cache.assert_called_once_with()
