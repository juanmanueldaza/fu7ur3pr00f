"""Tests for data gathering tools."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.tools.gathering import (
    _resolve_home_path,
    gather_all_career_data,
    gather_assessment_data,
    gather_cv_data,
    gather_linkedin_data,
    gather_portfolio_data,
)

pytestmark = pytest.mark.unit


class TestResolveHomePath:
    """Test _resolve_home_path helper."""

    def test_rejects_path_outside_allowed_roots(self) -> None:
        _, err = _resolve_home_path("/etc/passwd")
        assert err is not None
        assert "Access denied" in err

    def test_accepts_path_in_tmp(self) -> None:
        resolved, err = _resolve_home_path("/tmp/test.txt")
        assert err is None
        assert resolved.name == "test.txt"

    def test_expands_and_resolves_relative(self) -> None:
        # Use /tmp which is always in allowed roots
        resolved, err = _resolve_home_path("/tmp/../tmp/test.txt")
        assert err is None
        assert "test.txt" in str(resolved)


class TestGatherPortfolioData:
    """Test gather_portfolio_data tool."""

    def test_gathers_portfolio(self) -> None:
        mock_service = MagicMock()
        with patch(
            "fu7ur3pr00f.agents.tools.gathering.GathererService",
            return_value=mock_service,
        ):
            result = gather_portfolio_data.invoke({})

        assert "Portfolio data gathered" in result
        mock_service.gather_portfolio.assert_called_once_with(None)

    def test_gathers_with_custom_url(self) -> None:
        mock_service = MagicMock()
        with patch(
            "fu7ur3pr00f.agents.tools.gathering.GathererService",
            return_value=mock_service,
        ):
            result = gather_portfolio_data.invoke({"url": "https://example.com"})

        assert "Portfolio data gathered" in result
        mock_service.gather_portfolio.assert_called_once_with("https://example.com")


class TestGatherAllCareerData:
    """Test gather_all_career_data tool."""

    def test_returns_cancelled_when_not_approved(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.gathering.interrupt",
            return_value=False,
        ):
            result = gather_all_career_data.invoke({})

        assert "cancelled" in result.lower()

    def test_gathers_when_approved(self) -> None:
        mock_service = MagicMock()
        mock_service.gather_all.return_value = {
            "portfolio": True,
            "linkedin": False,
            "assessment": True,
        }

        with patch(
            "fu7ur3pr00f.agents.tools.gathering.interrupt",
            return_value=True,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.gathering.GathererService",
                return_value=mock_service,
            ):
                result = gather_all_career_data.invoke({})

        assert "Career data gathering complete" in result
        assert "+ portfolio" in result
        assert "- linkedin" in result
        assert "+ assessment" in result

    def test_skips_auto_populate_when_no_success(self) -> None:
        mock_service = MagicMock()
        mock_service.gather_all.return_value = {"portfolio": False}

        with patch(
            "fu7ur3pr00f.agents.tools.gathering.interrupt",
            return_value=True,
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.gathering.GathererService",
                return_value=mock_service,
            ):
                result = gather_all_career_data.invoke({})

        assert "0/1 sources" in result


class TestGatherLinkedInData:
    """Test gather_linkedin_data tool."""

    def test_processes_valid_zip(self, tmp_path) -> None:
        zip_file = tmp_path / "LinkedIn.zip"
        zip_file.write_text("fake zip content")

        mock_service = MagicMock()
        with patch(
            "fu7ur3pr00f.agents.tools.gathering.GathererService",
            return_value=mock_service,
        ):
            with patch("pathlib.Path.home", return_value=tmp_path):
                result = gather_linkedin_data.invoke({"zip_path": str(zip_file)})

        assert "LinkedIn data processed" in result

    def test_returns_error_for_missing_file(self) -> None:
        result = gather_linkedin_data.invoke(
            {"zip_path": "/tmp/nonexistent/LinkedIn.zip"}
        )
        assert "not found" in result.lower()

    def test_returns_error_for_outside_allowed_path(self) -> None:
        result = gather_linkedin_data.invoke({"zip_path": "/etc/data.zip"})
        assert "Access denied" in result


class TestGatherCvData:
    """Test gather_cv_data tool."""

    def test_rejects_unsupported_format(self, tmp_path) -> None:
        cv_file = tmp_path / "resume.docx"
        cv_file.write_text("fake content")

        result = gather_cv_data.invoke({"file_path": str(cv_file)})
        assert "Unsupported format" in result

    def test_rejects_missing_file(self) -> None:
        result = gather_cv_data.invoke({"file_path": "/tmp/nonexistent/resume.pdf"})
        assert "not found" in result.lower()

    def test_rejects_outside_path(self) -> None:
        result = gather_cv_data.invoke({"file_path": "/etc/passwd"})
        assert "Access denied" in result

    def test_imports_md_file(self, tmp_path) -> None:
        cv_file = tmp_path / "resume.md"
        cv_file.write_text("# John Doe\n\nSoftware Engineer")

        mock_service = MagicMock()
        mock_service.gather_cv.return_value = [{"title": "Summary"}]

        with patch(
            "fu7ur3pr00f.agents.tools.gathering.interrupt",
            return_value="import",
        ):
            with patch(
                "fu7ur3pr00f.agents.tools.gathering.GathererService",
                return_value=mock_service,
            ):
                with patch(
                    "fu7ur3pr00f.agents.tools.gathering.get_knowledge_store",
                    return_value=None,
                ):
                    result = gather_cv_data.invoke({"file_path": str(cv_file)})

        assert "imported" in result
        assert "1 sections" in result


class TestGatherAssessmentData:
    """Test gather_assessment_data tool."""

    def test_processes_pdfs_from_default_dir(self) -> None:
        mock_service = MagicMock()
        with patch(
            "fu7ur3pr00f.agents.tools.gathering.GathererService",
            return_value=mock_service,
        ):
            result = gather_assessment_data.invoke({})

        assert "CliftonStrengths" in result
        mock_service.gather_assessment.assert_called_once_with(None)

    def test_returns_error_for_empty_dir(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.gathering.GathererService",
        ) as mock_cls:
            mock_cls.return_value.gather_assessment.side_effect = FileNotFoundError
            result = gather_assessment_data.invoke({"input_dir": "/tmp/empty"})

        assert "No Gallup PDF files found" in result

    def test_rejects_outside_path(self) -> None:
        result = gather_assessment_data.invoke({"input_dir": "/etc"})
        assert "Access denied" in result
