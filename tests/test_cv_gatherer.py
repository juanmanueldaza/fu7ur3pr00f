"""Tests for CVGatherer — PDF and Markdown CV parsing."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.gatherers.cv import CVGatherer, NoDataError, ServiceError
from fu7ur3pr00f.memory.chunker import Section

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

STRUCTURED_PDF_TEXT = """
EXPERIENCE
Software Engineer at Acme Corp (2020-2023)
Led backend services for the payments platform.
Reduced latency by 40% through cache redesign.

EDUCATION
MSc Computer Science, MIT (2018-2020)
Thesis on distributed consensus algorithms.
GPA 4.0 — Dean's List.
"""

STRUCTURED_MD_TEXT = """
## Experience
Software Engineer at Acme Corp (2020-2023)
Led backend services for the payments platform.

## Education
MSc Computer Science, MIT (2018-2020)
Thesis on distributed consensus algorithms.
"""

UNSTRUCTURED_TEXT = "John Doe, software engineer with 5 years experience in Python and Go."


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
# _extract_text_pdf
# ---------------------------------------------------------------------------


class TestExtractTextPdf:
    def test_success_returns_stdout(self, tmp_path):
        gatherer = CVGatherer()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = STRUCTURED_PDF_TEXT

        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        with (
            patch("shutil.which", return_value="/usr/bin/pdftotext"),
            patch("subprocess.run", return_value=mock_result),
        ):
            text = gatherer._extract_text_pdf(pdf_file)

        assert text == STRUCTURED_PDF_TEXT

    def test_non_zero_returncode_returns_empty(self, tmp_path):
        gatherer = CVGatherer()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "some error"
        mock_result.stdout = ""

        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        with (
            patch("shutil.which", return_value="/usr/bin/pdftotext"),
            patch("subprocess.run", return_value=mock_result),
        ):
            text = gatherer._extract_text_pdf(pdf_file)

        assert text == ""

    def test_pdftotext_missing_raises_service_error(self, tmp_path):
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        gatherer = CVGatherer()
        with patch("shutil.which", return_value=None):
            with pytest.raises(ServiceError, match="pdftotext"):
                gatherer._extract_text_pdf(pdf_file)


# ---------------------------------------------------------------------------
# _extract_text_markdown
# ---------------------------------------------------------------------------


class TestExtractTextMarkdown:
    def test_valid_file_returns_content(self, tmp_path):
        md_file = tmp_path / "cv.md"
        md_file.write_text(STRUCTURED_MD_TEXT, encoding="utf-8")
        gatherer = CVGatherer()
        text = gatherer._extract_text_markdown(md_file)
        assert "Experience" in text
        assert "Education" in text

    def test_empty_file_raises_no_data_error(self, tmp_path):
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("   \n\n  ", encoding="utf-8")
        gatherer = CVGatherer()
        with pytest.raises(NoDataError):
            gatherer._extract_text_markdown(empty_file)


# ---------------------------------------------------------------------------
# _parse_sections_locally
# ---------------------------------------------------------------------------


class TestParseSectionsLocally:
    def test_structured_md_returns_two_sections(self):
        gatherer = CVGatherer()
        sections = gatherer._parse_sections_locally(STRUCTURED_MD_TEXT)
        assert len(sections) >= 2
        names = [s.name for s in sections]
        assert "Experience" in names
        assert "Education" in names

    def test_unstructured_text_returns_empty(self):
        gatherer = CVGatherer()
        sections = gatherer._parse_sections_locally(UNSTRUCTURED_TEXT)
        assert sections == []


# ---------------------------------------------------------------------------
# gather() — happy paths
# ---------------------------------------------------------------------------


class TestGatherHappyPath:
    def test_happy_path_pdf(self, tmp_path):
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        gatherer = CVGatherer()
        with patch.object(gatherer, "_extract_text_pdf", return_value=STRUCTURED_PDF_TEXT):
            sections = gatherer.gather(pdf_file)

        assert isinstance(sections, list)
        assert len(sections) > 0
        assert all(isinstance(s, Section) for s in sections)

    def test_happy_path_markdown(self, tmp_path):
        md_file = tmp_path / "cv.md"
        md_file.write_text(STRUCTURED_MD_TEXT, encoding="utf-8")

        gatherer = CVGatherer()
        sections = gatherer.gather(md_file)

        assert isinstance(sections, list)
        assert len(sections) > 0
        names = [s.name for s in sections]
        assert "Experience" in names
        assert "Education" in names


# ---------------------------------------------------------------------------
# gather() — error paths
# ---------------------------------------------------------------------------


class TestGatherErrors:
    def test_missing_file_raises_file_not_found(self, tmp_path):
        gatherer = CVGatherer()
        with pytest.raises(FileNotFoundError):
            gatherer.gather(tmp_path / "nonexistent.pdf")

    def test_scanned_pdf_raises_no_data_error(self, tmp_path):
        pdf_file = tmp_path / "scanned.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        gatherer = CVGatherer()
        with patch.object(gatherer, "_extract_text_pdf", return_value=""):
            with pytest.raises(NoDataError):
                gatherer.gather(pdf_file)

    def test_pdftotext_not_found_raises_service_error(self, tmp_path):
        pdf_file = tmp_path / "resume.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        gatherer = CVGatherer()
        with patch("shutil.which", return_value=None):
            with pytest.raises(ServiceError, match="pdftotext"):
                gatherer.gather(pdf_file)


# ---------------------------------------------------------------------------
# .txt file support
# ---------------------------------------------------------------------------


class TestTxtFileSupport:
    def test_txt_file_parsed_as_markdown(self, tmp_path):
        txt_file = tmp_path / "resume.txt"
        txt_file.write_text(STRUCTURED_MD_TEXT, encoding="utf-8")

        gatherer = CVGatherer()
        sections = gatherer.gather(txt_file)

        assert len(sections) > 0
        assert all(isinstance(s, Section) for s in sections)

    def test_empty_txt_raises_nodataerror(self, tmp_path):
        txt_file = tmp_path / "empty.txt"
        txt_file.write_text("", encoding="utf-8")

        gatherer = CVGatherer()
        with pytest.raises(NoDataError):
            gatherer.gather(txt_file)

    def test_txt_with_headings_parses_sections(self, tmp_path):
        txt_file = tmp_path / "cv.txt"
        txt_file.write_text(
            """
## Experience
Software Engineer at Acme
Led a team of 5 developers

## Education
BS Computer Science
Graduated with honors
""",
            encoding="utf-8",
        )

        gatherer = CVGatherer()
        sections = gatherer.gather(txt_file)

        assert len(sections) >= 2
        section_names = [s.name.lower() for s in sections]
        assert "experience" in section_names
        assert "education" in section_names


# ---------------------------------------------------------------------------
# gather() — fallback
# ---------------------------------------------------------------------------


class TestGatherFallback:
    def test_unstructured_content_returns_fallback_section(self, tmp_path):
        md_file = tmp_path / "unstructured.md"
        md_file.write_text(UNSTRUCTURED_TEXT, encoding="utf-8")

        gatherer = CVGatherer()
        sections = gatherer.gather(md_file)

        assert len(sections) == 1
        assert sections[0].name == "CV Content"
        assert sections[0].content == UNSTRUCTURED_TEXT


# ---------------------------------------------------------------------------
# Integration smoke test
# ---------------------------------------------------------------------------


class TestCVGathererIntegration:
    def test_gather_returns_sections_with_name_and_content(self, tmp_path):
        md_file = tmp_path / "cv.md"
        md_file.write_text(STRUCTURED_MD_TEXT, encoding="utf-8")

        sections = CVGatherer().gather(md_file)

        assert isinstance(sections, list)
        assert len(sections) > 0
        for s in sections:
            assert isinstance(s, Section)
            assert s.name
            assert s.content
