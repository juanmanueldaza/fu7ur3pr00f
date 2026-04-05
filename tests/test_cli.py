"""CLI smoke tests for FutureProof."""

import re

from typer.testing import CliRunner

from fu7ur3pr00f.cli import app

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestCLIBasics:
    """Test basic CLI functionality."""

    def test_app_shows_help(self) -> None:
        """Test app shows help with --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Career Intelligence System" in _strip_ansi(result.output)

    def test_version_flag(self) -> None:
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "FutureProof" in _strip_ansi(result.output)

    def test_thread_option_in_help(self) -> None:
        """Test --thread option appears in help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--thread" in _strip_ansi(result.output)

    def test_debug_option_in_help(self) -> None:
        """Test --debug option appears in help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--debug" in _strip_ansi(result.output)
