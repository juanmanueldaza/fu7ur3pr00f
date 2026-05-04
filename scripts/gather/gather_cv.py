#!/usr/bin/env python3
"""Gather CV/resume data from a file."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fu7ur3pr00f.gatherers.cv import CVGatherer
from fu7ur3pr00f.memory.knowledge import KnowledgeSource, get_knowledge_store


def main():
    if len(sys.argv) < 2:
        print("Usage: python gather_cv.py <path/to/cv.pdf|md|txt>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    print(f"Parsing CV from {file_path}...")
    gatherer = CVGatherer()
    sections = gatherer.gather(file_path)
    print(f"Extracted {len(sections)} sections")

    store = get_knowledge_store()
    old_ids = store.get_ids_by_filter({"source": KnowledgeSource.CV.value})
    chunk_ids = store.index_sections(source=KnowledgeSource.CV, sections=sections)
    if old_ids:
        store.delete_by_ids(old_ids)
    print(f"Indexed {len(chunk_ids)} chunks into knowledge base")
    print("Done.")


if __name__ == "__main__":
    main()
