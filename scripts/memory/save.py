#!/usr/bin/env python3
"""CLI wrapper for storing episodic memories (decisions and job applications).

Replaces MCP memory_save tool calls. All output is JSON to stdout. Errors to stderr.

Usage:
    python scripts/memory/save.py --action decision \
        --context "Chose remote over hybrid" --decision "Remote-first preference"
    python scripts/memory/save.py --action application \
        --context "Interview stage" --company "Acme" --role "Staff Engineer" --status "interviewing"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _save_decision(args: argparse.Namespace) -> dict[str, Any]:
    from fu7ur3pr00f.memory.episodic import get_episodic_store, remember_decision

    if not args.context:
        print(json.dumps({"error": "--context is required for decisions"}), file=sys.stderr)
        sys.exit(2)

    if not args.decision:
        print(json.dumps({"error": "--decision is required for decisions"}), file=sys.stderr)
        sys.exit(2)

    memory = remember_decision(
        decision=args.decision,
        context=args.context,
        outcome=args.outcome or None,
    )

    store = get_episodic_store()
    store.remember(memory)

    return {"id": memory.id, "memory_type": "decision", "status": "stored"}


def _save_application(args: argparse.Namespace) -> dict[str, Any]:
    from fu7ur3pr00f.memory.episodic import get_episodic_store, remember_application

    if not args.company:
        print(json.dumps({"error": "--company is required for applications"}), file=sys.stderr)
        sys.exit(2)

    if not args.role:
        print(json.dumps({"error": "--role is required for applications"}), file=sys.stderr)
        sys.exit(2)

    if not args.status:
        print(json.dumps({"error": "--status is required for applications"}), file=sys.stderr)
        sys.exit(2)

    memory = remember_application(
        company=args.company,
        role=args.role,
        status=args.status,
        notes=args.notes or "",
    )

    store = get_episodic_store()
    store.remember(memory)

    return {"id": memory.id, "memory_type": "application", "status": "stored"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Store episodic memories (decisions and applications)"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["decision", "application"],
        help="Type of memory to store",
    )
    parser.add_argument("--context", default=None, help="Context for decision or application")
    parser.add_argument(
        "--decision",
        default=None,
        help="The decision that was made (required for --action decision)",
    )
    parser.add_argument("--outcome", default=None, help="Optional outcome of the decision")
    parser.add_argument(
        "--company", default=None, help="Company name (required for --action application)"
    )
    parser.add_argument(
        "--role", default=None, help="Role applied for (required for --action application)"
    )
    parser.add_argument(
        "--status", default=None, help="Application status (applied, interviewing, rejected, offer)"
    )
    parser.add_argument("--notes", default=None, help="Additional notes about the application")

    args = parser.parse_args()

    try:
        if args.action == "decision":
            result = _save_decision(args)
        else:
            result = _save_application(args)

        print(json.dumps(result, indent=2))
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
