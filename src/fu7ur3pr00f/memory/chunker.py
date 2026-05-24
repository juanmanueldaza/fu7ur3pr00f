"""Markdown chunking for career documents.

Chunks content by size while preserving section metadata.
Section labels are passed in directly — no header regex parsing.
"""

from dataclasses import dataclass, field
from typing import NamedTuple

from fu7ur3pr00f.constants import CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS


class Section(NamedTuple):
    """A named section of content (e.g., name="Experience", content="...")."""

    name: str
    content: str


@dataclass
class MarkdownChunk:
    """A chunk of content with section context."""

    content: str
    section_path: list[str] = field(default_factory=list)


class MarkdownChunker:
    """Split markdown content into size-bounded chunks.

    Strategy:
    1. Accept pre-labeled sections (Section NamedTuples)
    2. Split sections that exceed max_tokens or max_chars by paragraphs
    3. If paragraphs still too large, split by sentences
    4. Final fallback: hard truncate at max_chars
    """

    # Hard char limit to prevent Ollama API errors (model context limits)
    MAX_CHARS = 4000

    def __init__(self, max_tokens: int = CHUNK_MAX_TOKENS, min_tokens: int = CHUNK_MIN_TOKENS):
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens

    def chunk_section(self, section: Section) -> list[MarkdownChunk]:
        """Split a single section into size-bounded chunks.

        Section name flows directly into chunk metadata — no header parsing.

        Args:
            section: Named section with content

        Returns:
            List of MarkdownChunk objects with section_path=[section.name]
        """
        content = section.content.strip()
        if not content:
            return []

        chunk = MarkdownChunk(
            content=content,
            section_path=[section.name],
        )

        return self._split_large_chunks([chunk])

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (~1.3 tokens per word for English text)."""
        return int(len(text.split()) * 1.3)

    def _split_large_chunks(self, chunks: list[MarkdownChunk]) -> list[MarkdownChunk]:
        """Split chunks that exceed max_tokens or MAX_CHARS."""
        result: list[MarkdownChunk] = []

        for chunk in chunks:
            # Check both token and char limits
            if (
                self._estimate_tokens(chunk.content) <= self.max_tokens
                and len(chunk.content) <= self.MAX_CHARS
            ):
                result.append(chunk)
            else:
                # Split by paragraphs first
                paragraphs = chunk.content.split("\n\n")
                if len(paragraphs) <= 1:
                    # No paragraphs, split by sentences
                    paragraphs = self._split_by_sentences(chunk.content)

                current_content: list[str] = []
                current_tokens = 0
                current_chars = 0

                for para in paragraphs:
                    para_tokens = self._estimate_tokens(para)
                    para_chars = len(para)

                    # If single paragraph exceeds limits, force split
                    if para_tokens > self.max_tokens or para_chars > self.MAX_CHARS:
                        # Flush current content first
                        if current_content:
                            result.append(
                                MarkdownChunk(
                                    content="\n\n".join(current_content),
                                    section_path=chunk.section_path,
                                )
                            )
                            current_content = []
                            current_tokens = 0
                            current_chars = 0

                        # Split this large paragraph
                        sub_chunks = self._split_oversized_paragraph(para)
                        result.extend(sub_chunks)
                        continue

                    # Check if adding this paragraph exceeds limits
                    if (
                        current_tokens + para_tokens > self.max_tokens
                        or current_chars + para_chars > self.MAX_CHARS
                    ) and current_content:
                        result.append(
                            MarkdownChunk(
                                content="\n\n".join(current_content),
                                section_path=chunk.section_path,
                            )
                        )
                        current_content = [para]
                        current_tokens = para_tokens
                        current_chars = para_chars
                    else:
                        current_content.append(para)
                        current_tokens += para_tokens
                        current_chars += para_chars

                if current_content:
                    result.append(
                        MarkdownChunk(
                            content="\n\n".join(current_content),
                            section_path=chunk.section_path,
                        )
                    )

        return result

    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text by sentence boundaries."""
        import re

        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_oversized_paragraph(self, text: str) -> list[MarkdownChunk]:
        """Split a paragraph that exceeds limits by sentences or hard truncation."""
        result: list[MarkdownChunk] = []

        # Try splitting by sentences
        sentences = self._split_by_sentences(text)
        if len(sentences) > 1:
            current_content: list[str] = []
            current_chars = 0

            for sent in sentences:
                sent_chars = len(sent)
                if current_chars + sent_chars > self.MAX_CHARS and current_content:
                    result.append(
                        MarkdownChunk(
                            content=" ".join(current_content),
                            section_path=[],
                        )
                    )
                    current_content = [sent]
                    current_chars = sent_chars
                else:
                    current_content.append(sent)
                    current_chars += sent_chars

            if current_content:
                result.append(
                    MarkdownChunk(
                        content=" ".join(current_content),
                        section_path=[],
                    )
                )
            return result

        # Hard truncate as last resort
        while len(text) > self.MAX_CHARS:
            # Find last space before limit
            split_point = text.rfind(" ", 0, self.MAX_CHARS)
            if split_point == -1:
                split_point = self.MAX_CHARS

            result.append(
                MarkdownChunk(
                    content=text[:split_point].strip(),
                    section_path=[],
                )
            )
            text = text[split_point:].strip()

        if text:
            result.append(
                MarkdownChunk(
                    content=text,
                    section_path=[],
                )
            )

        return result
