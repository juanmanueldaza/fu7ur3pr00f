# GEMINI.md

fu7ur3pr00f is an opencode-native workspace for career intelligence. It provides skills, commands, and Python scripts for gathering professional data, analyzing career trajectories, generating ATS-optimized CVs, and searching job boards.

## Architecture

opencode is the agent runtime. Skills (`.opencode/skills/career-*/SKILL.md`) define HOW to perform operations. Python scripts (`scripts/`) handle heavy lifting (data gathering, PDF rendering). ChromaDB via nerv-memory stores career knowledge and episodic memories.

## Running

```bash
uv sync
opencode  # opens the workspace
```

In opencode: `/gather`, `/analyze`, `/generate`, `/search`, `/profile`

## Testing

```bash
uv run pytest tests/ -q
uv run ruff check .
```

## Conventions

- Python 3.13, type hints with `collections.abc`
- Lines < 100 chars
- Conventional commits, no AI attribution
