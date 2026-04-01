"""Tests for GitLab tools."""

from unittest.mock import MagicMock, patch

from fu7ur3pr00f.agents.tools.gitlab import (
    _RE_PROJECT_PATH,
    _glab,
    _validate_gitlab_input,
    get_gitlab_file,
    get_gitlab_project,
    search_gitlab_projects,
)


class TestValidateGitlabInput:
    """Test _validate_gitlab_input helper."""

    def test_valid_input(self) -> None:
        result = _validate_gitlab_input("my-project", "name", _RE_PROJECT_PATH, 256)
        assert result is None

    def test_empty_input(self) -> None:
        result = _validate_gitlab_input("", "name", _RE_PROJECT_PATH, 256)
        assert result is not None
        assert "must be 1-256 characters" in result

    def test_too_long(self) -> None:
        result = _validate_gitlab_input("x" * 300, "name", _RE_PROJECT_PATH, 256)
        assert result is not None
        assert "must be 1-256 characters" in result

    def test_starts_with_dash(self) -> None:
        result = _validate_gitlab_input("-malicious", "name", _RE_PROJECT_PATH, 256)
        assert result is not None
        assert "must not start with '-'" in result

    def test_disallowed_characters(self) -> None:
        result = _validate_gitlab_input("my project!@#", "name", _RE_PROJECT_PATH, 256)
        assert result is not None
        assert "contains disallowed characters" in result


class TestGlab:
    """Test _glab helper."""

    def test_returns_error_when_glab_not_installed(self) -> None:
        with patch("shutil.which", return_value=None):
            result = _glab(["repo", "list"])

        assert "GitLab CLI (glab) is not installed" in result

    def test_returns_output_on_success(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "project1\nproject2"

        with patch("shutil.which", return_value="/usr/bin/glab"):
            with patch("subprocess.run", return_value=mock_result):
                result = _glab(["repo", "list"])

        assert "project1" in result
        assert "project2" in result

    def test_returns_error_on_failure(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "authentication required"

        with patch("shutil.which", return_value="/usr/bin/glab"):
            with patch("subprocess.run", return_value=mock_result):
                result = _glab(["repo", "list"])

        assert "GitLab CLI error" in result
        assert "authentication required" in result

    def test_returns_timeout_on_expire(self) -> None:
        import subprocess

        with patch("shutil.which", return_value="/usr/bin/glab"):
            with patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(["glab"], 30),
            ):
                result = _glab(["repo", "list"], timeout=30)

        assert "timed out" in result


class TestSearchGitlabProjects:
    """Test search_gitlab_projects tool."""

    def test_searches_projects(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.gitlab._glab",
            return_value="project1\nproject2",
        ) as mock_glab:
            result = search_gitlab_projects.invoke({"query": "colmena"})

        assert "project1" in result
        mock_glab.assert_called_once_with(["repo", "search", "--search", "colmena"])

    def test_rejects_empty_query(self) -> None:
        result = search_gitlab_projects.invoke({"query": ""})
        assert "Invalid query" in result

    def test_rejects_long_query(self) -> None:
        result = search_gitlab_projects.invoke({"query": "x" * 300})
        assert "Invalid query" in result

    def test_rejects_dash_prefix(self) -> None:
        result = search_gitlab_projects.invoke({"query": "-flag"})
        assert "must not start with '-'" in result


class TestGetGitlabProject:
    """Test get_gitlab_project tool."""

    def test_gets_project(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.gitlab._glab",
            return_value='{"name": "my-project"}',
        ) as mock_glab:
            result = get_gitlab_project.invoke({"project_path": "user/my-project"})

        assert "my-project" in result
        mock_glab.assert_called_once_with(
            ["repo", "view", "user/my-project", "--output", "json"]
        )

    def test_rejects_invalid_path(self) -> None:
        result = get_gitlab_project.invoke({"project_path": "-invalid"})
        assert "must not start with '-'" in result


class TestGetGitlabFile:
    """Test get_gitlab_file tool."""

    def test_gets_file(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.gitlab._glab",
            return_value="# README content",
        ) as mock_glab:
            result = get_gitlab_file.invoke(
                {
                    "project_path": "user/my-project",
                    "file_path": "README.md",
                    "ref": "main",
                }
            )

        assert "README content" in result
        mock_glab.assert_called_once_with(
            [
                "api",
                "projects/user%2Fmy-project/repository/files/README.md/raw",
                "--method",
                "GET",
                "-f",
                "ref=main",
            ]
        )

    def test_rejects_invalid_project_path(self) -> None:
        result = get_gitlab_file.invoke({"project_path": "", "file_path": "README.md"})
        assert "Invalid" in result

    def test_rejects_invalid_file_path(self) -> None:
        result = get_gitlab_file.invoke(
            {"project_path": "user/proj", "file_path": "!!!invalid"}
        )
        assert "Invalid file path" in result

    def test_rejects_invalid_ref(self) -> None:
        result = get_gitlab_file.invoke(
            {"project_path": "user/proj", "file_path": "README.md", "ref": "bad ref!"}
        )
        assert "Invalid ref" in result
