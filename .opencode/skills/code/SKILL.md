---
name: code
description: "Python language standards: type hints, error handling, logging, and style conventions."
compatibility: opencode
when_to_use: "When writing or reviewing *.py source files."
user-invocable: false
hub-skill-ids: [implementation, review, refactoring]
---

# Skill: Python

## Rules

REJECT if:
- Missing type hints on public functions or methods
- Bare `except:` without a specific exception type
- `print()` used in production code (use `logging` instead)
- Mutable default arguments (e.g., `def f(x=[]):`)

REQUIRE:
- `from __future__ import annotations` in all modules
- Type hints on all public functions and class attributes
- Pydantic v2 for data validation models

PREFER:
- Early returns over deeply nested conditionals
- `pathlib.Path` over `os.path` for filesystem operations
- Dataclasses or Pydantic over raw dicts for structured data