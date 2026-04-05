"""Tests for GitHub tools."""

from unittest.mock import patch

from fu7ur3pr00f.agents.tools.github import (
    _github_http_headers,
    get_github_profile,
    get_github_repo,
    search_github_repos,
)


class TestGithubHttpHeaders:
    """Test _github_http_headers helper."""

    @patch("fu7ur3pr00f.agents.tools.github.settings")
    def test_returns_headers_when_token_configured(self, mock_settings) -> None:
        mock_settings.github_mcp_token_resolved = "ghp-test-token"
        headers, error = _github_http_headers()
        assert error == ""
        assert headers is not None
        assert headers["Authorization"] == "Bearer ghp-test-token"
        assert headers["Accept"] == "application/vnd.github+json"

    @patch("fu7ur3pr00f.agents.tools.github.settings")
    def test_returns_error_when_no_token(self, mock_settings) -> None:
        mock_settings.github_mcp_token_resolved = ""
        headers, error = _github_http_headers()
        assert headers is None
        assert "GitHub token not configured" in error


class TestSearchGithubRepos:
    """Test search_github_repos tool."""

    def test_searches_repos(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value='{"items": [{"name": "repo1"}]}',
        ):
            result = search_github_repos.invoke({"query": "python ml"})

        assert "repo1" in result

    def test_passes_per_page(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value="results",
        ) as mock_github:
            search_github_repos.invoke({"query": "test", "per_page": 25})

        mock_github.assert_called_once_with(
            "search_repositories",
            {"query": "test", "perPage": 25},
        )


class TestGetGithubRepo:
    """Test get_github_repo tool."""

    def test_gets_repo_root(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value='{"name": "test-repo"}',
        ) as mock_github:
            get_github_repo.invoke({"owner": "user", "repo": "test-repo"})

        mock_github.assert_called_once_with(
            "get_file_contents",
            {"owner": "user", "repo": "test-repo"},
        )

    def test_gets_specific_file(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value="# README",
        ) as mock_github:
            get_github_repo.invoke(
                {"owner": "user", "repo": "test-repo", "path": "README.md"}
            )

        mock_github.assert_called_once_with(
            "get_file_contents",
            {"owner": "user", "repo": "test-repo", "path": "README.md"},
        )


class TestGetGithubProfile:
    """Test get_github_profile tool."""

    def test_returns_profile(self) -> None:
        profile_data = '{"login": "johndoe", "name": "John Doe"}'
        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value=profile_data,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.github._save_github_username"
            ) as mock_save:
                result = get_github_profile.invoke({"include_repos": False})

        assert "johndoe" in result
        mock_save.assert_called_once_with("johndoe")

    def test_returns_error_directly(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value="GitHub token not configured",
        ):
            result = get_github_profile.invoke({})

        assert "GitHub token not configured" in result

    def test_fetches_repos_when_requested(self) -> None:
        profile_data = '{"login": "johndoe", "name": "John"}'
        repos_data = '{"items": [{"name": "my-repo"}]}'

        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            side_effect=[profile_data, repos_data],
        ) as mock_github:
            result = get_github_profile.invoke({"include_repos": True})

        assert "my-repo" in result
        assert mock_github.call_count == 2

    def test_skips_repos_when_no_username(self) -> None:
        profile_data = '{"name": "Unknown"}'  # No login field

        with patch(
            "fu7ur3pr00f.agents.tools.github._github",
            return_value=profile_data,
        ) as mock_github:
            get_github_profile.invoke({"include_repos": True})

        # Only profile call, no repos call
        assert mock_github.call_count == 1
