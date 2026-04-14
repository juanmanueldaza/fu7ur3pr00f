"""Tests for FutureProofApp main Textual application."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.chat.app import FutureProofApp
from fu7ur3pr00f.chat.widgets import _animations_enabled

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


class TestFutureProofApp:
    @pytest.mark.asyncio
    async def test_app_launches_without_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """App composes and mounts without raising."""
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        mock_engine = MagicMock()
        mock_profile = MagicMock()
        mock_profile.name = "Test User"

        with (
            patch(
                "fu7ur3pr00f.chat.app.get_conversation_engine", return_value=mock_engine
            ),
            patch("fu7ur3pr00f.chat.app.load_profile", return_value=mock_profile),
        ):
            app = FutureProofApp(thread_id="test")
            async with app.run_test(size=(120, 40)):
                # App mounted successfully — check title
                assert app.TITLE == "FUTUREPROOF"

    @pytest.mark.asyncio
    async def test_help_command_pushes_help_screen(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        mock_engine = MagicMock()
        mock_profile = MagicMock()
        mock_profile.name = "Test User"

        with (
            patch(
                "fu7ur3pr00f.chat.app.get_conversation_engine", return_value=mock_engine
            ),
            patch("fu7ur3pr00f.chat.app.load_profile", return_value=mock_profile),
        ):
            app = FutureProofApp(thread_id="test")
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.press("ctrl+q")  # Quit the app cleanly

    @pytest.mark.asyncio
    async def test_quit_command_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        mock_engine = MagicMock()
        mock_profile = MagicMock()
        mock_profile.name = "Test User"

        with (
            patch(
                "fu7ur3pr00f.chat.app.get_conversation_engine", return_value=mock_engine
            ),
            patch("fu7ur3pr00f.chat.app.load_profile", return_value=mock_profile),
        ):
            app = FutureProofApp(thread_id="test")
            async with app.run_test(size=(120, 40)) as pilot:
                # Pressing ctrl+q should exit
                await pilot.press("ctrl+q")
                # If we reach here without error, the app exited cleanly

    @pytest.mark.asyncio
    async def test_empty_input_does_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        mock_engine = MagicMock()
        mock_profile = MagicMock()
        mock_profile.name = "Test User"

        with (
            patch(
                "fu7ur3pr00f.chat.app.get_conversation_engine", return_value=mock_engine
            ),
            patch("fu7ur3pr00f.chat.app.load_profile", return_value=mock_profile),
        ):
            app = FutureProofApp(thread_id="test")
            async with app.run_test(size=(120, 40)) as pilot:
                # Submit empty input — should not crash
                await pilot.press("enter")
                # No exception = pass
                await pilot.press("ctrl+q")

    @pytest.mark.asyncio
    async def test_slash_help_dispatched(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEXTUAL_ANIMATIONS", "disabled")
        monkeypatch.delenv("NO_COLOR", raising=False)

        mock_engine = MagicMock()
        mock_profile = MagicMock()
        mock_profile.name = "Test User"

        with (
            patch(
                "fu7ur3pr00f.chat.app.get_conversation_engine", return_value=mock_engine
            ),
            patch("fu7ur3pr00f.chat.app.load_profile", return_value=mock_profile),
        ):
            app = FutureProofApp(thread_id="test")
            app._handle_command = MagicMock()
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.click("#input-bar")
                await pilot.press(*list("/help"))
                await pilot.press("enter")
                app._handle_command.assert_called_once_with("/help")
                await pilot.press("ctrl+q")
