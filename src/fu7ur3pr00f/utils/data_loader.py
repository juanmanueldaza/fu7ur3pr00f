"""Unified career data loading utilities.

Database-first: all career data is loaded from ChromaDB knowledge base.
No file I/O — gatherers index content directly to ChromaDB.
"""

import logging
from collections.abc import Mapping
from typing import Any

from fu7ur3pr00f.memory.knowledge import (
    KnowledgeSource,
    get_knowledge_store,
)

logger = logging.getLogger(__name__)

_MAX_DATA_SIZE = 5 * 1024 * 1024
_MAX_SINGLE_SOURCE = 2 * 1024 * 1024


def load_career_data() -> dict[str, str]:
    """Load all career data from the knowledge base."""
    store = get_knowledge_store()
    data: dict[str, str] = {}
    source_keys = {
        KnowledgeSource.LINKEDIN: "linkedin_data",
        KnowledgeSource.PORTFOLIO: "portfolio_data",
        KnowledgeSource.ASSESSMENT: "assessment_data",
    }
    for source, key in source_keys.items():
        content = store.get_all_content(source)
        if content:
            data[key] = content
    return data


def load_career_data_for_analysis() -> dict[str, str]:
    """Load filtered career data (excludes social/network sections)."""
    store = get_knowledge_store()
    data: dict[str, str] = {}

    # LinkedIn — filtered
    linkedin = store.get_filtered_content(
        KnowledgeSource.LINKEDIN,
        frozenset({"Connections", "Messages", "Network", "Job Applications", "Posts"}),
        ("Conversation:", "Conversation ", "Sponsored"),
    )
    if linkedin:
        data["linkedin_data"] = linkedin

    # Portfolio & Assessment — full
    for source, key in [
        (KnowledgeSource.PORTFOLIO, "portfolio_data"),
        (KnowledgeSource.ASSESSMENT, "assessment_data"),
    ]:
        content = store.get_all_content(source)
        if content:
            data[key] = content

    return data


def combine_career_data(
    data: Mapping[str, Any],
    header_prefix: str = "##",
    include_analysis: bool = False,
) -> str:
    """Combine career data dict into formatted markdown string."""
    total_size = sum(len(str(v)) for v in data.values() if isinstance(v, str))
    if total_size > _MAX_DATA_SIZE:
        raise ValueError(
            f"Career data too large: {total_size / 1024 / 1024:.1f}MB "
            f"(max {_MAX_DATA_SIZE / 1024 / 1024:.0f}MB)"
        )

    for key, value in data.items():
        if isinstance(value, str) and len(value) > _MAX_SINGLE_SOURCE:
            raise ValueError(
                f"Source {key!r} too large: {len(value) / 1024 / 1024:.1f}MB "
                f"(max {_MAX_SINGLE_SOURCE / 1024 / 1024:.0f}MB)"
            )

    parts = []
    source_names = {
        "linkedin_data": "LinkedIn",
        "portfolio_data": "Portfolio",
        "assessment_data": "CliftonStrengths Assessment",
    }
    if include_analysis:
        source_names["analysis"] = "Previous Analysis"

    for key, name in source_names.items():
        value = data.get(key)
        if value and isinstance(value, str):
            parts.append(f"{header_prefix} {name}\n{value}")

    return "\n\n".join(parts)


def load_career_data_for_cv() -> str:
    """Load career data formatted for CV generation."""
    data = load_career_data_for_analysis()
    if not data:
        return ""
    return combine_career_data(data, header_prefix="###")
