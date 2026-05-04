"""CV generator — markdown-to-PDF rendering.

LLM content generation is handled by opencode via the career-cv skill.
This module provides the PDF rendering (WeasyPrint) and output management.
"""

import logging
import os
import re
from pathlib import Path

from ..config import settings
from ..utils.security import secure_open, validate_file_size

logger = logging.getLogger(__name__)

_PDF_SUPPORT = False
_WEASY_HTML = None
_WEASY_DEFAULT_URL_FETCHER = None
_markdown = None
_nh3 = None

try:
    import markdown as _md
    import nh3 as _nh3_mod
    from weasyprint import HTML as _WH
    from weasyprint.urls import default_url_fetcher as _WDF

    _markdown = _md
    _nh3 = _nh3_mod
    _WEASY_HTML = _WH
    _WEASY_DEFAULT_URL_FETCHER = _WDF
    _PDF_SUPPORT = True
except ImportError:
    pass

_MAX_MD_SIZE = 1024 * 1024


def _clean_llm_output(text: str) -> str:
    """Strip code fences and trailing disclaimers from LLM output."""
    stripped = text.strip()
    if stripped.startswith("```"):
        if "\n" not in stripped:
            return stripped
        first_newline = stripped.index("\n")
        stripped = stripped[first_newline + 1 :]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3].rstrip()

    stripped = re.sub(r"\n+\*?This CV[^*\n]*\*?\s*$", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\n```\s*$", "", stripped)
    return stripped.rstrip()


def _render_pdf(markdown_path: Path) -> Path:
    """Convert markdown to styled PDF via WeasyPrint."""
    validate_file_size(markdown_path, _MAX_MD_SIZE, "Markdown file")

    if not _PDF_SUPPORT:
        logger.warning("PDF deps not installed — skipping PDF generation")
        return markdown_path

    assert _markdown is not None
    assert _nh3 is not None
    assert _WEASY_HTML is not None
    assert _WEASY_DEFAULT_URL_FETCHER is not None

    wdf = _WEASY_DEFAULT_URL_FETCHER

    md_content = markdown_path.read_text()
    html_content = _markdown.markdown(md_content, extensions=["tables", "fenced_code"])
    html_content = _nh3.clean(
        html_content,
        tags={
            "p",
            "ul",
            "ol",
            "li",
            "strong",
            "em",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "a",
            "br",
            "hr",
            "blockquote",
            "code",
            "pre",
        },
        attributes={"a": {"href"}},
        strip_comments=True,
    )

    styled_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 1.8cm 2.2cm; }}
body {{ font-family: Georgia, serif; font-size: 11pt; line-height: 1.5; color: #2c2416; }}
h1 {{ font-size: 24pt; font-weight: 700; color: #0d1b2a; margin: 0 0 4px 0; }}
h2 {{
    font-family: Arial, sans-serif; font-size: 9.5pt; font-weight: 700;
    color: #0d1b2a; text-transform: uppercase; letter-spacing: 2px;
    border-bottom: 1.5px solid #b8860b; padding-bottom: 3px; margin: 16px 0 8px 0;
}}
h3 {{ font-size: 11.5pt; font-weight: 600; color: #1b263b; margin: 10px 0 1px 0; }}
p {{ margin: 4px 0; }}
ul {{ padding-left: 16px; margin: 4px 0 8px 0; }}
li {{ margin-bottom: 2px; color: #3d3428; font-size: 10pt; }}
a {{ color: #1b4f72; text-decoration: none; }}
</style></head><body>{html_content}</body></html>"""

    def _deny_url_fetcher(url, timeout=10, ssl_context=None):
        if url.startswith("data:"):
            return wdf(url, timeout, ssl_context)
        raise ValueError(f"External resource fetch blocked: {url}")

    pdf_path = markdown_path.with_suffix(".pdf")
    _WEASY_HTML(string=styled_html, url_fetcher=_deny_url_fetcher).write_pdf(pdf_path)
    os.chmod(pdf_path, 0o600)
    return pdf_path


def save_cv_markdown(content: str, filename: str) -> Path:
    """Save markdown CV content to file. Returns path."""
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned = _clean_llm_output(content)
    path = output_dir / filename
    with secure_open(path) as f:
        f.write(cleaned)
    return path


def render_cv_pdf(markdown_path: Path) -> Path:
    """Render a markdown CV file to PDF. Returns PDF path."""
    return _render_pdf(markdown_path)
