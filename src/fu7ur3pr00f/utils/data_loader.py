"""Unified career data loading utilities.

Database-first: all career data is loaded from ChromaDB knowledge base.
No file I/O — gatherers index content directly to ChromaDB.

Security: Validates input data size and content to prevent processing
malicious or oversized data.
"""

import logging
from collections.abc import Mapping
from typing import Any

from fu7ur3pr00f.utils.services import get_knowledge_service

logger = logging.getLogger(__name__)

# Security limits
_MAX_DATA_SIZE = 5 * 1024 * 1024  # 5MB max combined career data
_MAX_SINGLE_SOURCE = 2 * 1024 * 1024  # 2MB max per source


def load_career_data() -> dict[str, str]:
    """Load all career data from the knowledge base.

    Returns:
        Dictionary with keys like 'linkedin_data', 'portfolio_data', etc.
        Only includes sources that have indexed content.
    """
    service = get_knowledge_service()
    return service.get_all_content()


def load_career_data_for_analysis() -> dict[str, str]:
    """Load career data filtered for analysis (excludes social/network sections).

    Connections, Messages, Posts remain searchable via the agent's
    search_career_knowledge tool but are excluded from analysis prompts.
    """
    service = get_knowledge_service()
    return service.get_filtered_content()


def combine_career_data(
    data: Mapping[str, Any],
    header_prefix: str = "##",
    include_analysis: bool = False,
) -> str:
    """Combine career data dict into formatted string.

    Security: Validates data size and content before processing.

    Args:
        data: Dictionary with career data (linkedin_data, portfolio_data, etc.)
        header_prefix: Markdown header prefix (default "##")
        include_analysis: Whether to include 'analysis' field if present

    Returns:
        Combined markdown string

    Raises:
        ValueError: If data exceeds size limits or contains invalid content
    """
    # Security: Validate total size
    total_size = sum(len(str(v)) for v in data.values() if isinstance(v, str))
    if total_size > _MAX_DATA_SIZE:
        raise ValueError(
            f"Career data too large: {total_size / 1024 / 1024:.1f}MB "
            f"(max {_MAX_DATA_SIZE / 1024 / 1024:.0f}MB)"
        )

    # Security: Validate individual source sizes
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
        if value:
            # Security: Validate value is string
            if not isinstance(value, str):
                logger.warning("Skipping non-string value for %s", key)
                continue
            parts.append(f"{header_prefix} {name}\n{value}")

    return "\n\n".join(parts)


def load_career_data_for_cv() -> str:
    """Load career data formatted for CV generation.

    Uses filtered data — CV doesn't need Connections, Messages, etc.

    Returns:
        Combined markdown string of all career data with section headers
    """
    data = load_career_data_for_analysis()
    if not data:
        return ""
    return combine_career_data(data, header_prefix="###")
