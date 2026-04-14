"""Tests for knowledge service and knowledge store."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.memory.chunker import Section
from fu7ur3pr00f.memory.knowledge import KnowledgeSource
from fu7ur3pr00f.services.knowledge_service import KnowledgeService

pytestmark = pytest.mark.unit


class TestKnowledgeService:
    def test_import(self):
        assert KnowledgeService is not None

    def test_instantiation(self):
        service = KnowledgeService()
        assert service is not None

    def test_get_stats_returns_dict(self):
        service = KnowledgeService()
        with patch.object(service, "_store", create=True) as mock_store:
            mock_store.get_stats.return_value = {
                "total_chunks": 0,
                "by_source": {},
            }
            stats = service.get_stats()
        assert isinstance(stats, dict)
        assert "total_chunks" in stats

    def test_index_sections_excludes_sensitive_prefixes_before_indexing(self):
        store = MagicMock()
        store.get_ids_by_filter.return_value = []
        store.index_sections.return_value = ["chunk-1"]
        service = KnowledgeService(store=store)

        sections = [
            Section(name="Experience", content="Built systems"),
            Section(name="Conversation: Alice", content="Private DM"),
            Section(name="Sponsored Conversation", content="Sponsored InMail"),
        ]

        count = service.index_sections(KnowledgeSource.LINKEDIN, sections)

        assert count == 1
        store.index_sections.assert_called_once()
        indexed_sections = store.index_sections.call_args.kwargs["sections"]
        assert [section.name for section in indexed_sections] == ["Experience"]


class TestCareerKnowledgeStore:
    def test_import(self):
        from fu7ur3pr00f.memory.knowledge import CareerKnowledgeStore

        assert CareerKnowledgeStore is not None

    def test_instantiation_with_temp_dir(self):
        from fu7ur3pr00f.memory.knowledge import CareerKnowledgeStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = CareerKnowledgeStore(persist_dir=Path(tmpdir))
            assert store is not None


class TestChunker:
    def test_import(self):
        from fu7ur3pr00f.memory.chunker import MarkdownChunker

        assert MarkdownChunker is not None

    def test_chunk_section(self):
        from fu7ur3pr00f.memory.chunker import MarkdownChunker, Section

        chunker = MarkdownChunker(max_tokens=500, min_tokens=10)
        section = Section(name="Experience", content="Built APIs and microservices.")
        chunks = chunker.chunk_section(section)
        assert len(chunks) >= 1
        assert any("APIs" in c.content for c in chunks)

    def test_chunk_long_section_splits(self):
        from fu7ur3pr00f.memory.chunker import MarkdownChunker, Section

        chunker = MarkdownChunker(max_tokens=50, min_tokens=10)
        long_content = "\n\n".join([f"Paragraph {i}. " * 20 for i in range(10)])
        section = Section(name="Experience", content=long_content)
        chunks = chunker.chunk_section(section)
        assert len(chunks) > 1

    def test_chunk_preserves_section_path(self):
        from fu7ur3pr00f.memory.chunker import MarkdownChunker, Section

        chunker = MarkdownChunker(max_tokens=500, min_tokens=10)
        section = Section(name="Skills", content="Python, JavaScript, Go")
        chunks = chunker.chunk_section(section)
        assert len(chunks) >= 1
        assert "Skills" in chunks[0].section_path


class TestEmbeddings:
    def test_import(self):
        from fu7ur3pr00f.memory.embeddings import get_embedding_function

        assert get_embedding_function is not None
