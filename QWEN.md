# QWEN.md — Project Context

**Project**: fu7ur3pr00f — Career intelligence opencode workspace
**Stack**: Python 3.13, opencode, ChromaDB (nerv-memory), WeasyPrint

## Architecture

```
opencode CLI → .opencode/skills/career-*/SKILL.md → scripts/*.py → ChromaDB
```

## Key Files

| File | Purpose |
|------|---------|
| `.opencode/skills/career-*/SKILL.md` | Career operation instructions |
| `.opencode/commands/*.md` | Slash command definitions |
| `scripts/gather/*.py` | Data gathering entry points |
| `scripts/generate/render_cv.py` | CV PDF rendering |
| `src/fu7ur3pr00f/gatherers/` | LinkedIn, CV, portfolio parsers |
| `src/fu7ur3pr00f/generators/` | WeasyPrint PDF generation |
| `src/fu7ur3pr00f/memory/` | ChromaDB stores, chunker, profile |
| `src/fu7ur3pr00f/utils/security.py` | PII anonymization, secure file I/O |

## Coding Standards

- Imports: `collections.abc` types, not `typing`
- Type hints: Required. Python 3.13 syntax.
- Line length: 100 (ruff enforces)
- Error handling: Raise exceptions, never return error dicts

## Testing

```bash
uv run pytest tests/ -q
uv run ruff check .
```

Mock external services (LLMs, HTTP, ChromaDB) — no real API calls.
