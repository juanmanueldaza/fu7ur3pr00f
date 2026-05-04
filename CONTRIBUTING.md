# Contributing

## Development Setup

```bash
git clone https://github.com/juanmanueldaza/fu7ur3pr00f.git
cd fu7ur3pr00f
uv sync --group dev
```

Python >= 3.13 required. [uv](https://github.com/astral-sh/uv) for package management.

Optionally install system dependencies for full functionality:

```bash
# CliftonStrengths PDF parsing
sudo apt install poppler-utils

# CV PDF export
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2
```

## Running Tests

```bash
uv run pytest tests/ -q
```

Markers: `unit` (single component, mocked externals), `integration` (multiple components wired), `slow` (benchmarks).

## Linting and Type Checking

```bash
uv run ruff check .
uv run mypy src/     # if mypy is installed
```

## Commit Style

Conventional commits only: `type(scope): description`. See `.opencode/skills/commits/SKILL.md` for the full convention. No AI attribution. No `Co-Authored-By` tags.

## SDD Workflow

For non-trivial changes, use the Spec-Driven Development pipeline:

```
/sdd-new "description of change"
```

This runs the 8-phase pipeline (explore → propose → spec → design → tasks → apply → verify → archive). Each phase produces a memory artifact for traceability.

## Code Philosophy

- **DATA STRUCTURES > CODE**: good programmers worry about data and state; bad programmers worry about code and abstract design patterns
- **AI IS A TOOL**: we direct, AI executes; the human always leads
- **STRICT ADHERENCE**: DRY, KISS, YAGNI, OWASP

See [FUTUREPROOF.md](FUTUREPROOF.md) for the project vision and concept map.
