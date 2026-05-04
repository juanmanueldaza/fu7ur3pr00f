#!/usr/bin/env python3
"""Gather CliftonStrengths assessment data from PDFs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from fu7ur3pr00f.gatherers.cliftonstrengths import CliftonStrengthsGatherer
from fu7ur3pr00f.memory.knowledge import KnowledgeSource, get_knowledge_store


def main():
    input_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    print(f"Gathering assessment data{' from ' + str(input_dir) if input_dir else ''}...")
    gatherer = CliftonStrengthsGatherer()
    sections = gatherer.gather(input_dir)
    print(f"Extracted {len(sections)} sections")

    store = get_knowledge_store()
    old_ids = store.get_ids_by_filter({"source": KnowledgeSource.ASSESSMENT.value})
    chunk_ids = store.index_sections(source=KnowledgeSource.ASSESSMENT, sections=sections)
    if old_ids:
        store.delete_by_ids(old_ids)
    print(f"Indexed {len(chunk_ids)} chunks into knowledge base")
    print("Done.")


if __name__ == "__main__":
    main()
