---
name: testing
description: "pytest testing standards: naming, fixtures, isolation, and parametrize patterns."
compatibility: opencode
when_to_use: "When writing or reviewing test files in tests/ or matching *test*.py."
user-invocable: false
hub-skill-ids: [review]
---

# Skill: Testing

## Framework

pytest — `uv run pytest -q`

## Rules

REQUIRE:
- Tests for all public functions and behavior changes
- Descriptive test names: `test_<subject>_<condition>_<expected_outcome>`
- Use `tmp_path` fixture for filesystem-touching tests
- Isolated tests: no shared mutable state between tests

REJECT if:
- Tests call external services without mocking
- Empty test body
- Tests depend on execution order

PREFER:
- `pytest.mark.parametrize` over repeated similar test functions
- Factory fixtures over inline setup in each test
- `conftest.py` for shared fixtures within a package