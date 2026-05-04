#!/usr/bin/env python3
"""Gather LinkedIn data from ZIP export."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fu7ur3pr00f.gatherers.linkedin import LinkedInGatherer
from fu7ur3pr00f.memory.knowledge import KnowledgeSource, get_knowledge_store


def main():
    if len(sys.argv) < 2:
        print("Usage: python gather_linkedin.py <path/to/linkedin.zip>")
        sys.exit(1)

    zip_path = Path(sys.argv[1])
    if not zip_path.exists():
        print(f"File not found: {zip_path}")
        sys.exit(1)

    print(f"Gathering LinkedIn data from {zip_path}...")
    gatherer = LinkedInGatherer()
    sections = gatherer.gather(zip_path)
    print(f"Extracted {len(sections)} sections")

    store = get_knowledge_store()
    old_ids = store.get_ids_by_filter({"source": KnowledgeSource.LINKEDIN.value})
    chunk_ids = store.index_sections(source=KnowledgeSource.LINKEDIN, sections=sections)
    if old_ids:
        store.delete_by_ids(old_ids)
    print(f"Indexed {len(chunk_ids)} chunks into knowledge base")
    print("Done.")


if __name__ == "__main__":
    main()
