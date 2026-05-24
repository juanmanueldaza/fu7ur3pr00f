#!/usr/bin/env python3
"""CLI wrapper for aggregate memory statistics.

Replaces MCP memory_stats tool calls. All output is JSON to stdout. Errors to stderr.

Usage:
    python scripts/memory/stats.py
"""

from __future__ import annotations

import json
import sys
from typing import Any


def main() -> None:
    try:
        from fu7ur3pr00f.memory.knowledge import get_knowledge_store
        from fu7ur3pr00f.memory.episodic import get_episodic_store

        knowledge_store = get_knowledge_store()
        episodic_store = get_episodic_store()

        knowledge_stats = knowledge_store.get_stats()
        episodic_stats = episodic_store.stats()

        output: dict[str, Any] = {
            "knowledge": knowledge_stats,
            "episodic": episodic_stats,
        }
        print(json.dumps(output, indent=2))
    except ImportError:
        print(
            json.dumps({"error": "Run: uv sync (chromadb not found)"}),
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
