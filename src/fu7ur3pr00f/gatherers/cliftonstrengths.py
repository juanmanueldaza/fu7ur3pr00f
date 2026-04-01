"""CliftonStrengths assessment gatherer.

Extracts and processes Gallup CliftonStrengths assessment data from PDF reports.
Supports multiple report types:
- Top 5 (SF_TOP_5)
- Top 10 (TOP_10)
- All 34 (ALL_34)
- Action Planning (ACTION_PLANNING_TOP_10)
- Leadership Insight (LEADERSHIP_INSIGHT_TOP_10)
- Discovery Development (DISCOVERY_DEVELOPMENT)

Uses strategy pattern for report type parsing (cliftonstrengths_parsers.py).
"""

import logging
import re
import shutil
import subprocess  # nosec B404 — required for pdftotext CLI
from dataclasses import dataclass, field
from pathlib import Path

from fu7ur3pr00f.constants import (
    CLIFTON_ALL_34_MAX_RANK,
    CLIFTON_TOP_5_MAX_RANK,
    CLIFTON_TOP_10_MAX_RANK,
)

from ..config import settings
from ..memory.chunker import Section
from ..utils.security import validate_file_size
from .cliftonstrengths_parsers import (
    ActionPlanningParser,
    DiscoveryDevelopmentParser,
    LeadershipInsightParser,
    SectionExtractor,
)

logger = logging.getLogger(__name__)

# Security limits
_MAX_PDF_SIZE = 50 * 1024 * 1024  # 50MB max PDF size
_PDF_MAGIC = b"%PDF"  # PDF file signature

# Filename indicators for detecting Gallup CliftonStrengths PDFs
GALLUP_PDF_INDICATORS = [
    "top_5",
    "top_10",
    "all_34",
    "action_planning",
    "leadership_insight",
    "discovery_development",
    "sf_top",
    "cliftonstrengths",
    "strengthsfinder",
    "gallup",
]

# CliftonStrengths domains
DOMAINS = {
    "EXECUTING": [
        "Achiever",
        "Arranger",
        "Belief",
        "Consistency",
        "Deliberative",
        "Discipline",
        "Focus",
        "Responsibility",
        "Restorative",
    ],
    "INFLUENCING": [
        "Activator",
        "Command",
        "Communication",
        "Competition",
        "Maximizer",
        "Self-Assurance",
        "Significance",
        "Woo",
    ],
    "RELATIONSHIP BUILDING": [
        "Adaptability",
        "Connectedness",
        "Developer",
        "Empathy",
        "Harmony",
        "Includer",
        "Individualization",
        "Positivity",
        "Relator",
    ],
    "STRATEGIC THINKING": [
        "Analytical",
        "Context",
        "Futuristic",
        "Ideation",
        "Input",
        "Intellection",
        "Learner",
        "Strategic",
    ],
}

# Reverse lookup: strength -> domain
STRENGTH_TO_DOMAIN = {
    strength: domain for domain, strengths in DOMAINS.items() for strength in strengths
}


@dataclass
class StrengthInsight:
    """Parsed insight for a single strength."""

    rank: int
    name: str
    domain: str
    description: str = ""
    unique_insights: list[str] = field(default_factory=list)
    why_succeed: str = ""
    action_items: list[str] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)
    sounds_like_quotes: list[str] = field(default_factory=list)


@dataclass
class CliftonStrengthsData:
    """Parsed CliftonStrengths assessment data."""

    name: str = ""
    date: str = ""
    top_5: list[StrengthInsight] = field(default_factory=list)
    top_10: list[StrengthInsight] = field(default_factory=list)
    all_34: list[str] = field(default_factory=list)
    dominant_domain: str = ""


class CliftonStrengthsGatherer:
    """Gather and process CliftonStrengths assessment data from PDFs.

    Extracts structured data from Gallup CliftonStrengths PDF reports
    and produces labeled sections for career analysis.
    """

    def gather(self, input_dir: Path | None = None) -> list[Section]:
        """Gather CliftonStrengths data from PDF files.

        Args:
            input_dir: Directory containing Gallup PDF files.
                      Defaults to data/raw

        Returns:
            List of Section(name, content) tuples
        """

        input_dir = input_dir or (settings.data_dir / "raw")

        logger.info(f"Gathering CliftonStrengths data from {input_dir}")

        pdf_files = list(input_dir.glob("*.pdf"))
        gallup_pdfs = [p for p in pdf_files if self._is_gallup_pdf(p)]

        if not gallup_pdfs:
            raise FileNotFoundError(
                f"No Gallup CliftonStrengths PDFs found in {input_dir}"
            )

        logger.info(f"Found {len(gallup_pdfs)} Gallup PDF files")

        data = CliftonStrengthsData()

        for pdf_path in gallup_pdfs:
            self._parse_pdf(pdf_path, data)

        # Determine dominant domain from top 5
        if data.top_5:
            domain_counts: dict[str, int] = {}
            for strength in data.top_5:
                domain_counts[strength.domain] = (
                    domain_counts.get(strength.domain, 0) + 1
                )
            data.dominant_domain = max(domain_counts, key=lambda d: domain_counts[d])

        sections = self._build_sections(data)

        logger.info("CliftonStrengths data gathered successfully")
        return sections

    def _is_gallup_pdf(self, path: Path) -> bool:
        """Check if a PDF is a Gallup CliftonStrengths report.

        Security: Validates file size and PDF magic number before processing.
        """

        # Check file size
        try:
            validate_file_size(path, _MAX_PDF_SIZE, "PDF")
        except (FileNotFoundError, ValueError) as e:
            logger.warning("%s", e)
            return False
        except OSError:
            logger.warning("Cannot access PDF file: %s", path)
            return False

        # Check PDF magic number
        try:
            header = path.read_bytes()[:4]
            if header != _PDF_MAGIC:
                logger.warning(
                    "Invalid PDF magic number: %r (expected %r)", header, _PDF_MAGIC
                )
                return False
        except OSError:
            logger.warning("Cannot read PDF file header: %s", path)
            return False

        # Check filename indicators
        name = path.name.lower()
        return any(indicator in name for indicator in GALLUP_PDF_INDICATORS)

    def _extract_ranked_strengths(
        self, text: str, max_rank: int = CLIFTON_ALL_34_MAX_RANK
    ) -> list[StrengthInsight]:
        """Extract ranked strengths from text into StrengthInsight objects.

        Parses "N. StrengthName" patterns, filters valid CliftonStrengths names,
        deduplicates by rank, and returns sorted results.

        Args:
            text: Text containing ranked strength patterns
            max_rank: Maximum rank to include (5 for top_5, 10 for top_10, etc.)

        Returns:
            Sorted list of StrengthInsight objects
        """
        pattern = r"(\d{1,2})\.\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)"
        matches = re.findall(pattern, text)
        seen: set[int] = set()
        results: list[StrengthInsight] = []

        for rank_str, name in matches:
            rank = int(rank_str)
            name = name.strip()
            if name in STRENGTH_TO_DOMAIN and rank not in seen and rank <= max_rank:
                seen.add(rank)
                results.append(
                    StrengthInsight(
                        rank=rank,
                        name=name,
                        domain=STRENGTH_TO_DOMAIN.get(name, "Unknown"),
                    )
                )

        results.sort(key=lambda x: x.rank)
        return results

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using pdftotext."""
        pdftotext_path = shutil.which("pdftotext")
        if not pdftotext_path:
            logger.error("pdftotext not found. Install poppler-utils.")
            return ""
        try:
            result = subprocess.run(  # nosec B603 — pdftotext resolved via which()
                [pdftotext_path, "-layout", str(pdf_path), "-"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout
            else:
                logger.warning(f"pdftotext failed for {pdf_path}: {result.stderr}")
                return ""
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout extracting text from {pdf_path}")
            return ""

    def _parse_pdf(self, pdf_path: Path, data: CliftonStrengthsData) -> None:
        """Parse a single PDF using strategy pattern."""
        filename = pdf_path.name.upper()
        text = self._extract_text(pdf_path)

        if not text:
            logger.warning(f"No text extracted from {pdf_path}")
            return

        # Extract name and date
        name_match = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\|\s*(\d{2}-\d{2}-\d{4})", text
        )
        if name_match and not data.name:
            data.name = name_match.group(1).strip()
            data.date = name_match.group(2).strip()

        # Use strategy pattern for report type parsing
        report_type = self._get_report_type(filename)
        extractor = SectionExtractor(text)

        parsers = {
            "action_planning": ActionPlanningParser(extractor),
            "leadership": LeadershipInsightParser(extractor),
            "discovery": DiscoveryDevelopmentParser(extractor),
        }

        parser = parsers.get(report_type)
        if parser:
            parser.parse(text, data)
        elif report_type == "all_34":
            self._parse_all_34(text, data)
        elif report_type == "top_5":
            self._parse_top_5(text, data)
        elif report_type == "top_10":
            self._parse_top_10(text, data)

    def _get_report_type(self, filename: str) -> str:
        """Determine report type from filename."""
        if "ALL_34" in filename:
            return "all_34"
        elif "SF_TOP_5" in filename or "TOP_5" in filename.replace("TOP_10", ""):
            return "top_5"
        # Specific TOP_10 variants must be checked BEFORE generic TOP_10
        elif "ACTION_PLANNING" in filename:
            return "action_planning"
        elif "LEADERSHIP" in filename:
            return "leadership"
        elif "DISCOVERY" in filename:
            return "discovery"
        elif "TOP_10" in filename:
            return "top_10"
        return "unknown"

    def _parse_all_34(self, text: str, data: CliftonStrengthsData) -> None:
        """Parse the All 34 report for complete strength ranking."""
        all_strengths = self._extract_ranked_strengths(text)
        data.all_34 = [s.name for s in all_strengths]

        # Also populate top_5 and top_10 if not already done
        if not data.top_5 and len(data.all_34) >= CLIFTON_TOP_5_MAX_RANK:
            data.top_5 = list(all_strengths[:CLIFTON_TOP_5_MAX_RANK])

        if not data.top_10 and len(data.all_34) >= CLIFTON_TOP_10_MAX_RANK:
            data.top_10 = list(all_strengths[:CLIFTON_TOP_10_MAX_RANK])

        # Parse detailed insights for each strength
        self._parse_strength_details(text, data)

    def _parse_top_5(self, text: str, data: CliftonStrengthsData) -> None:
        """Parse Top 5 report."""
        if data.top_5:
            return

        data.top_5 = self._extract_ranked_strengths(
            text, max_rank=CLIFTON_TOP_5_MAX_RANK
        )
        self._parse_strength_details(text, data)

    def _parse_top_10(self, text: str, data: CliftonStrengthsData) -> None:
        """Parse Top 10 report."""
        if data.top_10:
            return

        data.top_10 = self._extract_ranked_strengths(
            text, max_rank=CLIFTON_TOP_10_MAX_RANK
        )
        self._parse_strength_details(text, data)

    # -----------------------------------------------------------------
    # Action Planning / Leadership / Discovery parsers
    # -----------------------------------------------------------------

    def _ensure_top_10(self, text: str, data: CliftonStrengthsData) -> None:
        """Populate top_10 from a ranked list in text if not already done."""
        if data.top_10:
            return
        data.top_10 = self._extract_ranked_strengths(
            text, max_rank=CLIFTON_TOP_10_MAX_RANK
        )
        if not data.top_5 and len(data.top_10) >= CLIFTON_TOP_5_MAX_RANK:
            data.top_5 = list(data.top_10[:CLIFTON_TOP_5_MAX_RANK])

    # Note: Helper methods moved to SectionExtractor in cliftonstrengths_parsers.py:
    # - _extract_section_text
    # - _extract_strength_section
    # - _split_personalized_insights

    def _clean_copyright(self, text: str) -> str:
        """Remove copyright lines and page numbers from extracted PDF text."""
        text = re.sub(
            r"\d*\s*\n?\s*StrengthsFinder.*?reserved\.\s*\n?",
            " ",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(r"101360652.*?\n", " ", text)
        text = re.sub(r"®", "", text)
        return text

    # Note: Report type parsing moved to cliftonstrengths_parsers.py (strategy pattern)
    # - ActionPlanningParser
    # - LeadershipInsightParser
    # - DiscoveryDevelopmentParser

    def _parse_strength_details(self, text: str, data: CliftonStrengthsData) -> None:
        """Parse detailed insights for each strength from text."""
        # Split text into sections by strength headers
        # Pattern matches "N. StrengthName" at the start of a strength section
        strength_sections = self._split_into_strength_sections(text)

        # For each strength in top_5, try to find its details
        for insight in data.top_5:
            section_key = f"{insight.rank}. {insight.name}"
            section = strength_sections.get(section_key, "")

            if not section:
                # Try alternate key formats
                for key in strength_sections:
                    if insight.name.lower() in key.lower():
                        section = strength_sections[key]
                        break

            if section:
                self._extract_strength_insight(section, insight)

    def _split_into_strength_sections(self, text: str) -> dict[str, str]:
        """Split text into sections keyed by strength name."""
        sections: dict[str, str] = {}

        # Find all strength section headers (e.g., "1. Learner", "2. Woo")
        # These appear as headers in the Gallup PDFs
        header_pattern = r"(\d+)\.\s+([A-Z][a-z]+(?:-[A-Z][a-z]+)?)\s*®?"

        matches = list(re.finditer(header_pattern, text))

        for i, match in enumerate(matches):
            rank = match.group(1)
            name = match.group(2)
            start = match.end()

            # End is either the next match or end of text
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)

            section_text = text[start:end]
            key = f"{rank}. {name}"

            # Only store if this section has meaningful content
            if (
                "HOW YOU CAN THRIVE" in section_text
                or "WHY YOU SUCCEED" in section_text
            ):
                sections[key] = section_text

        return sections

    def _extract_strength_insight(self, section: str, insight: StrengthInsight) -> None:
        """Extract insight details from a strength section."""
        # Extract description (after "HOW YOU CAN THRIVE")
        desc_match = re.search(
            r"HOW YOU CAN THRIVE\s*(.*?)(?:WHY YOUR|$)",
            section,
            re.DOTALL | re.IGNORECASE,
        )
        if desc_match:
            insight.description = self._clean_text(desc_match.group(1))

        # Extract "WHY YOU SUCCEED" section
        succeed_match = re.search(
            r"WHY YOU SUCCEED.*?\n\s*(.*?)(?:TAKE ACTION|$)",
            section,
            re.DOTALL | re.IGNORECASE,
        )
        if succeed_match:
            insight.why_succeed = self._clean_text(succeed_match.group(1))

        # Extract action items (bullet points after TAKE ACTION)
        action_match = re.search(
            r"TAKE ACTION.*?\n(.*?)(?:WATCH OUT|$)",
            section,
            re.DOTALL | re.IGNORECASE,
        )
        if action_match:
            items = re.findall(
                r"[•●]\s*(.+?)(?=[•●]|$)", action_match.group(1), re.DOTALL
            )
            insight.action_items = [
                self._clean_text(item) for item in items if item.strip()
            ]

        # Extract blind spots
        blind_match = re.search(
            r"WATCH OUT FOR BLIND SPOTS\s*(.*?)(?=\d+\.\s+[A-Z]|StrengthsFinder|$)",
            section,
            re.DOTALL | re.IGNORECASE,
        )
        if blind_match:
            items = re.findall(
                r"[•●]\s*(.+?)(?=[•●]|$)", blind_match.group(1), re.DOTALL
            )
            insight.blind_spots = [
                self._clean_text(item) for item in items if item.strip()
            ]

    def _clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace."""
        text = re.sub(r"\s+", " ", text)
        text = self._clean_copyright(text)
        text = re.sub(r"\d+\s*$", "", text)
        return text.strip()

    def _build_sections(  # noqa: C901
        # Builds 10+ labeled sections from assessment data
        self,
        data: CliftonStrengthsData,
    ) -> list[Section]:
        """Build labeled sections from parsed CliftonStrengths data."""
        sections: list[Section] = []

        # Header info
        header_lines: list[str] = []
        if data.name:
            header_lines.append(f"**Name:** {data.name}")
        if data.date:
            header_lines.append(f"**Assessment Date:** {data.date}")
        if data.dominant_domain:
            header_lines.append(f"**Dominant Domain:** {data.dominant_domain}")
        if header_lines:
            sections.append(
                Section("CliftonStrengths Assessment", "\n".join(header_lines))
            )

        # Top 5 Summary + Domain distribution
        if data.top_5:
            lines = [
                "| Rank | Strength | Domain |",
                "|------|----------|--------|",
            ]
            for insight in data.top_5:
                lines.append(
                    f"| {insight.rank} | **{insight.name}** | {insight.domain} |"
                )
            lines.append("")

            # Domain distribution
            domain_counts: dict[str, list[str]] = {}
            for insight in data.top_5:
                domain_counts.setdefault(insight.domain, []).append(insight.name)
            lines.append("### Domain Distribution (Top 5)")
            for domain, strengths in domain_counts.items():
                lines.append(f"- **{domain}:** {', '.join(strengths)}")

            sections.append(Section("Top 5 Signature Themes", "\n".join(lines)))

        # Detailed insights for top 5
        if data.top_5:
            lines = []
            for insight in data.top_5:
                lines.append(f"### {insight.rank}. {insight.name} ({insight.domain})")
                if insight.description:
                    lines.append(f"**Description:** {insight.description}")
                if insight.why_succeed:
                    lines.append(f"**Why You Succeed:** {insight.why_succeed}")
                if insight.action_items:
                    lines.append("**Action Items:**")
                    for item in insight.action_items[:3]:
                        lines.append(f"- {item}")
                if insight.blind_spots:
                    lines.append("**Blind Spots to Watch:**")
                    for item in insight.blind_spots[:2]:
                        lines.append(f"- {item}")
                lines.append("")
            sections.append(
                Section("Detailed Strength Insights", "\n".join(lines).rstrip())
            )

        # Personalized talent patterns
        all_strengths = data.top_10 if data.top_10 else data.top_5
        has_personalized = any(s.unique_insights for s in all_strengths)
        if has_personalized:
            lines = [
                "Your specific talent manifestations based on your unique"
                " CliftonStrengths combination:",
            ]
            for insight in all_strengths:
                if insight.unique_insights:
                    lines.append(
                        f"### {insight.rank}. {insight.name} "
                        "-- What Makes You Stand Out"
                    )
                    for paragraph in insight.unique_insights:
                        lines.append(paragraph)
            sections.append(Section("Personalized Talent Patterns", "\n\n".join(lines)))

        # Extended Ideas for Action
        has_extended = any(len(s.action_items) > 3 for s in all_strengths)
        if has_extended:
            lines = ["Comprehensive action items for developing each strength:"]
            for insight in all_strengths:
                if len(insight.action_items) > 3:
                    lines.append(f"### {insight.rank}. {insight.name}")
                    for i, item in enumerate(insight.action_items, 1):
                        lines.append(f"{i}. {item}")
                    lines.append("")
            sections.append(
                Section("Extended Ideas for Action", "\n".join(lines).rstrip())
            )

        # Strengths in Practice
        has_quotes = any(s.sounds_like_quotes for s in all_strengths)
        if has_quotes:
            lines = [
                "Real quotes from people who share your top themes,"
                " showing how these strengths manifest:",
            ]
            for insight in all_strengths:
                if insight.sounds_like_quotes:
                    lines.append(f"### {insight.rank}. {insight.name}")
                    for quote in insight.sounds_like_quotes:
                        lines.append(f"> {quote}")
            sections.append(Section("Strengths in Practice", "\n\n".join(lines)))

        # Top 10 (6-10 only)
        if data.top_10 and len(data.top_10) > 5:
            lines = [
                "| Rank | Strength | Domain |",
                "|------|----------|--------|",
            ]
            for insight in data.top_10[5:]:
                lines.append(f"| {insight.rank} | {insight.name} | {insight.domain} |")
            sections.append(Section("Supporting Strengths (6-10)", "\n".join(lines)))

        # Full 34 ranking
        if data.all_34:
            lines = [
                "### Strengthen (1-10)",
                ", ".join(
                    f"**{s}**" if i < 5 else s for i, s in enumerate(data.all_34[:10])
                ),
                "",
                "### Navigate (11-23)",
                ", ".join(data.all_34[10:23]),
                "",
                "### Lesser Themes (24-34)",
                ", ".join(data.all_34[23:]),
            ]
            sections.append(
                Section("Complete Strength Ranking (All 34)", "\n".join(lines))
            )

        return sections
