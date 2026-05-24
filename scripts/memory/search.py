#!/usr/bin/env python3
"""CLI wrapper for semantic search across career knowledge and episodic memories.

Replaces MCP memory tool calls. All output is JSON to stdout. Errors to stderr.

Usage:
    python scripts/memory/search.py --query "Python projects" --limit 5
    python scripts/memory/search.py --query "applied" --memory-type episodic
    python scripts/memory/search.py --query "leadership" --source linkedin --limit 3
    python scripts/memory/search.py --query "skills" --exclude-section "Connections"
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    content: str
    source: str
    section: str
    metadata: dict[str, Any]
    memory_type: str | None = None
    context: str | None = None
    timestamp: str | None = None


def _serialize(result: SearchResult) -> dict[str, Any]:
    d: dict[str, Any] = {
        "content": result.content,
        "source": result.source,
        "section": result.section,
        "metadata": result.metadata,
    }
    if result.memory_type:
        d["memory_type"] = result.memory_type
    if result.context:
        d["context"] = result.context
    if result.timestamp:
        d["timestamp"] = result.timestamp
    return d


def _search_knowledge(args: argparse.Namespace) -> list[dict[str, Any]]:
    from fu7ur3pr00f.memory.knowledge import KnowledgeSource, get_knowledge_store

    store = get_knowledge_store()

    sources: list[KnowledgeSource] | None = None
    if args.source:
        sources = [KnowledgeSource(args.source)]

    results = store.search(
        query=args.query,
        limit=args.limit,
        sources=sources,
        section=args.section or None,
        excluded_sections=frozenset(args.exclude_section) if args.exclude_section else frozenset(),
        excluded_prefixes=tuple(args.exclude_prefix) if args.exclude_prefix else (),
    )

    return [
        _serialize(
            SearchResult(
                content=r["content"],
                source=r.get("source", "unknown"),
                section=r.get("section", ""),
                metadata=r.get("metadata", {}),
            )
        )
        for r in results
    ]


def _search_episodic(args: argparse.Namespace) -> list[dict[str, Any]]:
    from fu7ur3pr00f.memory.episodic import MemoryType, get_episodic_store

    store = get_episodic_store()

    memory_type: MemoryType | None = None
    if args.memory_subtype:
        try:
            memory_type = MemoryType(args.memory_subtype)
        except ValueError:
            print(
                json.dumps({"error": f"Invalid memory_type: {args.memory_subtype}"}),
                file=sys.stderr,
            )
            sys.exit(2)

    results = store.recall(
        query=args.query,
        limit=args.limit,
        memory_type=memory_type,
    )

    return [
        _serialize(
            SearchResult(
                content=m.content,
                source="episodic",
                section=m.memory_type.value,
                metadata=m.metadata,
                memory_type=m.memory_type.value,
                context=m.context,
                timestamp=m.timestamp.isoformat(),
            )
        )
        for m in results
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search career knowledge and episodic memories")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=5, help="Maximum results (default: 5)")
    parser.add_argument(
        "--memory-type",
        default="knowledge",
        choices=["knowledge", "episodic", "both"],
        help="Which ChromaDB collection to search (default: knowledge)",
    )
    parser.add_argument(
        "--memory-subtype",
        default=None,
        choices=["decision", "application"],
        help="Filter episodic results by memory type",
    )
    parser.add_argument(
        "--source",
        default=None,
        choices=["linkedin", "portfolio", "assessment", "cv"],
        help="Filter knowledge results by source",
    )
    parser.add_argument("--section", default=None, help="Filter knowledge results by section name")
    parser.add_argument(
        "--exclude-section",
        nargs="*",
        default=[],
        help="Section names to exclude",
    )
    parser.add_argument(
        "--exclude-prefix",
        nargs="*",
        default=[],
        help="Section name prefixes to exclude",
    )

    args = parser.parse_args()

    try:
        results: list[dict[str, Any]] = []

        if args.memory_type in ("knowledge", "both"):
            results.extend(_search_knowledge(args))

        if args.memory_type in ("episodic", "both"):
            results.extend(_search_episodic(args))

        output = {"results": results, "count": len(results), "query": args.query}
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
