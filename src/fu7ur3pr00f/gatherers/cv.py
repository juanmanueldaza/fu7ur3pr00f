"""CV / resume gatherer.

Parses CV and resume files (PDF or Markdown) into labeled sections
for indexing into the career knowledge base.
"""

import json
import logging
import re
import shutil
import subprocess  # nosec B404 — required for pdftotext CLI
from pathlib import Path

from ..memory.chunker import Section
from ..services.exceptions import NoDataError, ServiceError
from ..utils.security import (
    anonymize_career_data,
    sanitize_for_prompt,
    validate_file_size,
)

logger = logging.getLogger(__name__)

# Security limits
_MAX_CV_SIZE = 10 * 1024 * 1024  # 10MB max CV file size

_pdf_text_cache: dict[tuple[str, float, int], str] = {}
_SECTION_HEADING_RE = re.compile(
    r"^\s{0,3}(?:#{1,6}\s+)?([A-Z][A-Za-z &/+()-]{1,60})\s*$"
)


def _file_cache_key(path: Path) -> tuple[str, float, int]:
    """Generate cache key from file path, mtime, and size.

    Cache is automatically invalidated when file is modified.
    """
    stat = path.stat()
    return (str(path), stat.st_mtime, stat.st_size)


class CVGatherer:
    """Gather and parse a CV or resume file into labeled sections.

    Supports .pdf (via pdftotext) and .md / .txt (stdlib file I/O).
    Uses LLM-based section extraction for all formats.
    """

    def gather(self, file_path: Path | str) -> list[Section]:
        """Parse a CV/resume file into labeled sections.

        Args:
            file_path: Absolute path to a .pdf, .md, or .txt file.

        Returns:
            list[Section] — at least one section is always returned.

        Raises:
            FileNotFoundError: if file_path does not exist or is not a regular file.
            ServiceError: if pdftotext binary is not installed.
            NoDataError: if the file is empty or yields no extractable text.
            ValueError: if the file exceeds maximum size limit.
        """
        path = Path(file_path)

        # Security: Validate file size (also checks existence)
        validate_file_size(path, _MAX_CV_SIZE, "CV file")

        suffix = path.suffix.lower()

        if suffix == ".pdf":
            raw_text = self._extract_text_pdf(path)
        else:
            raw_text = self._extract_text_markdown(path)

        if not raw_text.strip():
            raise NoDataError(
                f"No text could be extracted from {path.name!r}. "
                "Is it a scanned/image PDF or an empty file?"
            )

        sections = self._parse_sections_with_llm(raw_text)
        if not sections:
            sections = self._parse_sections_locally(raw_text)
        if not sections:
            logger.debug(
                "Structured section parsing failed for '%s', using fallback section.",
                path.name,
            )
            return [Section("CV Content", raw_text)]

        return sections

    def _extract_text_pdf_cached(self, cache_key: tuple[str, float, int]) -> str:
        """Cached PDF text extraction.

        Cache is automatically invalidated when file is modified (mtime/size change).
        """
        if cache_key in _pdf_text_cache:
            return _pdf_text_cache[cache_key]
        path = Path(cache_key[0])
        result = self._extract_text_pdf_uncached(path)
        _pdf_text_cache[cache_key] = result
        return result

    def _extract_text_pdf_uncached(self, path: Path) -> str:
        """Run pdftotext -layout and return stdout (uncached)."""
        pdftotext_path = shutil.which("pdftotext")
        if not pdftotext_path:
            raise ServiceError(
                "pdftotext is not installed. "
                "Install it with: apt install poppler-utils  /  brew install poppler"
            )

        try:
            result = subprocess.run(  # nosec B603 — pdftotext resolved via which()
                [pdftotext_path, "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
            logger.warning("pdftotext failed for %s: %s", path, result.stderr)
            return ""
        except subprocess.TimeoutExpired:
            logger.error("Timeout extracting text from %s", path)
            return ""

    def _extract_text_pdf(self, path: Path) -> str:
        """Run pdftotext with caching.

        Raises:
            ServiceError: if pdftotext is not found on PATH.
        """
        cache_key = _file_cache_key(path)
        return self._extract_text_pdf_cached(cache_key)

    def _extract_text_markdown(self, path: Path) -> str:
        """Read a .md or .txt file as UTF-8.

        Raises:
            NoDataError: if the file is empty after stripping whitespace.
        """
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            raise NoDataError(f"File {path.name!r} is empty — no content to import.")
        return content

    def _parse_sections_with_llm(self, text: str) -> list[Section]:
        """Use LLM to extract labeled sections from CV text.

        Sends the raw text to the LLM and asks for a structured JSON list
        of section title + content pairs. Falls back to empty list on failure
        (caller returns a single fallback section).

        Security: Anonymizes PII and sanitizes content before sending to LLM
        to prevent prompt injection attacks.
        """
        from langchain_core.messages import HumanMessage

        from fu7ur3pr00f.llm.fallback import get_model_with_fallback

        # Security: Anonymize PII before sending to external LLM
        anonymized_text = anonymize_career_data(
            text,
            preserve_professional_emails=True,
        )

        # Security: Sanitize to prevent prompt injection
        sanitized_text = sanitize_for_prompt(anonymized_text[:8000])

        prompt = (
            "Extract all sections from this CV/resume text.\n"
            "Return a JSON array where each element has:\n"
            '  "title": the section heading '
            '(e.g. "Experience", "Education", "Skills")\n'
            '  "content": the full text body of that section\n'
            "Only include sections with meaningful content (at least 2 lines).\n\n"
            f"CV text:\n{sanitized_text}\n\n"
            "Respond with valid JSON only — no markdown, no explanation:\n"
            '[{"title": "...", "content": "..."}, ...]'
        )

        try:
            model, _ = get_model_with_fallback(purpose="summary")
            result = model.invoke([HumanMessage(content=prompt)])
            content = result.content.strip()  # type: ignore
            start = content.find("[")
            end = content.rfind("]") + 1
            sections_data = json.loads(content[start:end])
            return [
                Section(s["title"], s["content"])
                for s in sections_data
                if s.get("title") and s.get("content")
            ]
        except Exception:
            logger.warning(
                "LLM section extraction failed, using fallback", exc_info=True
            )
            return []

    def _parse_sections_locally(self, text: str) -> list[Section]:
        """Parse common Markdown/plain-text CV headings without an LLM.

        This fallback keeps the gatherer reliable in offline and CI environments.
        """
        sections: list[Section] = []
        current_title: str | None = None
        current_lines: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            heading = self._normalize_heading(line)
            if heading:
                self._append_section(sections, current_title, current_lines)
                current_title = heading
                current_lines = []
                continue

            if current_title and line:
                current_lines.append(raw_line.rstrip())

        self._append_section(sections, current_title, current_lines)
        return sections

    def _normalize_heading(self, line: str) -> str | None:
        """Return a normalized section title when a line looks like a heading."""
        if not line:
            return None

        match = _SECTION_HEADING_RE.match(line)
        if not match:
            return None

        title = match.group(1).strip("# ").strip()
        normalized = " ".join(word.capitalize() for word in title.split())
        known_headings = {
            "Experience",
            "Education",
            "Skills",
            "Projects",
            "Summary",
            "Profile",
            "Certifications",
            "Languages",
            "Achievements",
        }
        return normalized if normalized in known_headings else None

    def _append_section(
        self,
        sections: list[Section],
        title: str | None,
        lines: list[str],
    ) -> None:
        """Append a structured section if it has enough content."""
        if title and len([line for line in lines if line.strip()]) >= 2:
            sections.append(Section(title, "\n".join(lines).strip()))
