"""Strategy-based parsers for CliftonStrengths report types.

Extracts duplicated parsing logic from cliftonstrengths.py into
reusable strategy classes.
"""

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cliftonstrengths import CliftonStrengthsData, StrengthInsight


class ReportTypeParser(ABC):
    """Abstract base for report type parsers."""

    @abstractmethod
    def parse(self, text: str, data: "CliftonStrengthsData") -> None:
        """Parse text and populate data object."""
        pass


class SectionExtractor:
    """Helper for extracting sections from PDF text."""

    def __init__(self, text: str):
        self.text = text

    def extract_section(self, start_pattern: str, end_pattern: str) -> str:
        """Extract text between two patterns."""
        start_match = re.search(start_pattern, self.text)
        if not start_match:
            return ""

        start = start_match.end()
        end_match = re.search(end_pattern, self.text[start:])
        end = start + (end_match.start() if end_match else len(self.text) - start)

        return self.text[start:end]

    def extract_strength_block(
        self,
        section_text: str,
        insight: "StrengthInsight",
        header_pattern: str,
        end_marker: str = "QUESTIONS",
    ) -> str:
        """Extract a strength's section from formatted text."""
        pattern = re.compile(header_pattern, re.IGNORECASE)
        match = pattern.search(section_text)
        if not match:
            return ""

        remaining = section_text[match.end() :]
        end_pos = remaining.find(end_marker)
        return remaining[:end_pos] if end_pos != -1 else remaining

    @staticmethod
    def split_by_openers(text: str, openers: list[str]) -> list[str]:
        """Split text by opener patterns."""
        pattern = r"(?=" + "||".join(openers) + r")"
        parts = re.split(pattern, text)
        return [p.strip() for p in parts if p.strip() and len(p.strip()) > 30]


class ActionPlanningParser(ReportTypeParser):
    """Parser for Action Planning Top 10 reports."""

    PERSONAL_OPENERS = [
        r"Chances are good that",
        r"Driven by your talents",
        r"Because of your strengths",
        r"It's very likely that",
        r"Instinctively",
        r"By nature",
    ]

    def __init__(self, extractor: SectionExtractor):
        self.extractor = extractor

    def parse(self, text: str, data: "CliftonStrengthsData") -> None:
        """Parse Action Planning report."""
        self._parse_personalized_insights(text, data)
        self._parse_action_ideas(text, data)
        self._parse_sounds_like(text, data)

    def _parse_personalized_insights(
        self, text: str, data: "CliftonStrengthsData"
    ) -> None:
        """Parse Section I — personalized insights."""
        section_text = self.extractor.extract_section(
            r"Section I:\s*Awareness", r"Section II:\s*Application"
        )
        if not section_text:
            return

        for insight in data.top_10:
            raw = self.extractor.extract_strength_block(
                section_text,
                insight,
                rf"{re.escape(insight.name)}\s*\n.*?YOUR PERSONALIZED STRENGTHS INSIGHTS",
            )
            if not raw:
                continue

            # Skip header if present
            standout = re.search(r"What makes you stand out\?", raw)
            if standout and standout.start() < 50:
                raw = raw[standout.end() :]

            paragraphs = SectionExtractor.split_by_openers(raw, self.PERSONAL_OPENERS)
            if paragraphs:
                insight.unique_insights = [self._clean_text(p) for p in paragraphs]

    def _parse_action_ideas(self, text: str, data: "CliftonStrengthsData") -> None:
        """Parse Section II — Ideas for Action."""
        section_text = self.extractor.extract_section(
            r"Section II:\s*Application", r"Section III:\s*Achievement"
        )
        if not section_text:
            return

        for insight in data.top_10:
            raw = self.extractor.extract_strength_block(
                section_text,
                insight,
                rf"(?:^|\n)\s*{re.escape(insight.name)}\s*\n\s*IDEAS FOR ACTION",
            )
            if not raw:
                continue

            items = [
                self._clean_text(item)
                for item in re.split(r"\n\s*\n", raw)
                if item.strip() and len(item.strip()) > 30
            ]
            if items:
                insight.action_items = items

    def _parse_sounds_like(self, text: str, data: "CliftonStrengthsData") -> None:
        """Parse Section III — 'Sounds Like This' quotes."""
        section_text = self.extractor.extract_section(
            r"Section III:\s*Achievement", r"QUESTIONS"
        )
        if not section_text:
            return

        for insight in data.top_10:
            raw = self.extractor.extract_strength_block(
                section_text,
                insight,
                rf"{re.escape(insight.name.upper())}\s+SOUNDS LIKE THIS:",
                end_marker="SOUNDS LIKE THIS:",
            )
            if not raw:
                continue

            quote_splits = re.split(r"(?=\n[A-Z][a-z]+\s+[A-Z]\.?,\s+)", raw)
            quotes = [
                self._clean_text(part)
                for part in quote_splits
                if self._clean_text(part) and len(self._clean_text(part)) > 40
            ]
            if quotes:
                insight.sounds_like_quotes = quotes

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"®", "", text)
        return text


class LeadershipInsightParser(ReportTypeParser):
    """Parser for Leadership Insight reports."""

    def __init__(self, extractor: SectionExtractor):
        self.extractor = extractor

    def parse(self, text: str, data: "CliftonStrengthsData") -> None:
        """Parse Leadership Insight report."""
        # Skip if insights already populated
        if any(s.unique_insights for s in data.top_10):
            return

        section_text = self.extractor.extract_section(
            r"Your Personalized Strengths Insights", r"COPYRIGHT STANDARDS"
        )
        if not section_text:
            return

        for i, insight in enumerate(data.top_10):
            next_name = (
                data.top_10[i + 1].name.upper()
                if i + 1 < len(data.top_10)
                else "COPYRIGHT"
            )
            raw = self.extractor.extract_strength_block(
                section_text,
                insight,
                rf"{re.escape(insight.name.upper())}\s+",
                end_marker=next_name,
            )
            if not raw:
                continue

            paragraphs = SectionExtractor.split_by_openers(
                raw, ActionPlanningParser.PERSONAL_OPENERS
            )
            if paragraphs:
                insight.unique_insights = [self._clean_text(p) for p in paragraphs]

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"®", "", text)
        return text


class DiscoveryDevelopmentParser(ReportTypeParser):
    """Parser for Discovery Development reports."""

    def __init__(self, extractor: SectionExtractor):
        self.extractor = extractor

    def parse(self, text: str, data: "CliftonStrengthsData") -> None:
        """Parse Discovery Development report."""
        # Skip if action items already rich
        if any(len(s.action_items) > 5 for s in data.top_5):
            return

        section_text = self._clean_copyright(text)

        for insight in data.top_5:
            pattern = re.compile(
                rf"{re.escape(insight.name)}\s+.*?ACTION ITEMS\s*\n",
                re.DOTALL | re.IGNORECASE,
            )
            match = pattern.search(section_text)
            if not match:
                continue

            remaining = section_text[match.end() :]
            next_strength = re.search(r"\n\s*\w+(?:-\w+)?\s+®", remaining)
            raw = remaining[: next_strength.start()] if next_strength else remaining

            items = [
                self._clean_text(item)
                for item in re.split(r"\n\s*\n", raw)
                if item.strip() and len(item.strip()) > 30
            ]
            if items:
                insight.action_items = items

    def _clean_copyright(self, text: str) -> str:
        """Remove copyright lines."""
        text = re.sub(
            r"\d*\s*\n?\s*StrengthsFinder.*?reserved\.\s*\n?",
            " ",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        text = re.sub(r"101360652.*?\n", " ", text)
        text = re.sub(r"®", "", text)
        return text

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r"\s+", " ", text).strip()
        return text
