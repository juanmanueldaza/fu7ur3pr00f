"""Tests for Textual chat UI widgets."""

from unittest.mock import MagicMock

import pytest

from fu7ur3pr00f.chat.widgets import (
    ResponseBubble,
    SpecialistStatus,
    SplashBanner,
    ToolLogPanel,
    _animations_enabled,
)

pytestmark = pytest.mark.unit


class TestAnimationsEnabled:
    def test_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("TEXTUAL_ANIMATIONS", raising=False)
        assert _animations_enabled() is True

    def test_disabled_by_no_color(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        assert _animations_enabled() is False

    def test_disabled_by_textual_animations_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        assert _animations_enabled() is False

    def test_case_insensitive_disabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "DISABLED")
        assert _animations_enabled() is False

    def test_other_value_keeps_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "enabled")
        assert _animations_enabled() is True


class TestResponseBubble:
    def test_append_token_accumulates(self) -> None:
        bubble = ResponseBubble()
        bubble._accumulated = ""
        # Mock the Markdown widget query
        mock_md = MagicMock()
        bubble.query_one = MagicMock(return_value=mock_md)

        bubble.append_token("Hello")
        bubble.append_token(" world")

        assert bubble._accumulated == "Hello world"

    def test_finalize_with_accumulated_uses_it(self) -> None:
        bubble = ResponseBubble()
        bubble._accumulated = "Accumulated response"
        mock_md = MagicMock()
        mock_loader = MagicMock()

        def query_side(selector: object) -> MagicMock:
            from textual.widgets import LoadingIndicator

            if selector is LoadingIndicator:
                return mock_loader
            return mock_md

        bubble.query_one = MagicMock(side_effect=query_side)
        bubble.finalize()

        mock_md.update.assert_called_with("Accumulated response")

    def test_finalize_with_result_uses_narrative(self) -> None:
        bubble = ResponseBubble()
        bubble._accumulated = ""
        mock_md = MagicMock()
        mock_loader = MagicMock()

        def query_side(selector: object) -> MagicMock:
            from textual.widgets import LoadingIndicator

            if selector is LoadingIndicator:
                return mock_loader
            return mock_md

        bubble.query_one = MagicMock(side_effect=query_side)
        bubble.finalize({"synthesis": {"narrative": "The narrative"}})

        mock_md.update.assert_called_with("The narrative")

    def test_finalize_fallback_when_no_data(self) -> None:
        bubble = ResponseBubble()
        bubble._accumulated = ""
        mock_md = MagicMock()
        mock_loader = MagicMock()

        def query_side(selector: object) -> MagicMock:
            from textual.widgets import LoadingIndicator

            if selector is LoadingIndicator:
                return mock_loader
            return mock_md

        bubble.query_one = MagicMock(side_effect=query_side)
        bubble.finalize(None)

        mock_md.update.assert_called_with("Analysis complete.")


class TestSpecialistStatus:
    def test_start_specialist_adds_working_class(self) -> None:
        status = SpecialistStatus()
        # Mock the badge row
        mock_row = MagicMock()
        status.query_one = MagicMock(return_value=mock_row)
        status.display = False

        status.start_specialist("coach")

        assert "coach" in status._badges
        badge = status._badges["coach"]
        assert "--working" in badge._classes

    def test_complete_specialist_swaps_to_done(self) -> None:
        status = SpecialistStatus()
        mock_row = MagicMock()
        status.query_one = MagicMock(return_value=mock_row)
        status.display = False

        status.start_specialist("jobs")
        status.complete_specialist("jobs")

        badge = status._badges["jobs"]
        assert "--done" in badge._classes
        assert "--working" not in badge._classes

    def test_complete_nonexistent_specialist_is_safe(self) -> None:
        status = SpecialistStatus()
        # Should not raise
        status.complete_specialist("nonexistent")

    def test_reset_clears_badges(self) -> None:
        status = SpecialistStatus()
        mock_row = MagicMock()
        status.query_one = MagicMock(return_value=mock_row)
        status.display = False

        status.start_specialist("coach")
        status.reset()

        assert status._badges == {}

    def test_start_same_specialist_twice_updates_class(self) -> None:
        status = SpecialistStatus()
        mock_row = MagicMock()
        status.query_one = MagicMock(return_value=mock_row)
        status.display = False

        status.start_specialist("coach")
        badge = status._badges["coach"]
        badge.remove_class = MagicMock()
        badge.add_class = MagicMock()
        badge._classes = {"--done"}

        status.start_specialist("coach")

        badge.remove_class.assert_called_with("--done")
        badge.add_class.assert_called_with("--working")


class TestSplashBanner:
    def test_splash_no_animation_shows_text(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When animations disabled, SplashBanner.on_mount() calls self.update()."""
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        banner = SplashBanner()
        banner.update = MagicMock()

        banner.on_mount()

        banner.update.assert_called_once_with("FUTUREPROOF")

    def test_splash_with_animation_calls_run_tte(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        monkeypatch.delenv("TEXTUAL_ANIMATIONS", raising=False)

        banner = SplashBanner()
        banner._run_tte = MagicMock()
        banner.update = MagicMock()

        banner.on_mount()

        banner._run_tte.assert_called_once()


class TestToolLogPanel:
    def test_write_tool_start(self) -> None:
        panel = ToolLogPanel()
        mock_log = MagicMock()
        panel.query_one = MagicMock(return_value=mock_log)

        panel.write_tool_start("coach", "search_jobs", {"query": "python"})

        mock_log.write.assert_called_once()
        call_arg = mock_log.write.call_args[0][0]
        assert "coach" in call_arg
        assert "search_jobs" in call_arg

    def test_write_tool_result_truncates_long_result(self) -> None:
        panel = ToolLogPanel()
        mock_log = MagicMock()
        panel.query_one = MagicMock(return_value=mock_log)

        long_result = "x" * 300
        panel.write_tool_result("jobs", "search_jobs", long_result)

        call_arg = mock_log.write.call_args[0][0]
        assert "…" in call_arg

    def test_toggle_panel_flips_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """toggle_panel flips is_visible_panel; watcher is suppressed via env."""
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        panel = ToolLogPanel()
        panel.add_class = MagicMock()
        panel.remove_class = MagicMock()
        # Prevent watcher from calling animate (no active app in unit test)
        panel.watch_is_visible_panel = MagicMock()

        panel.toggle_panel()

        assert panel.is_visible_panel is True
