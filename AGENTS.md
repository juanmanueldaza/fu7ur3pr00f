# Repository Guidelines

## Project Structure & Module Organization
This repository uses a `src/` layout. Core code lives in `src/fu7ur3pr00f/`: `agents/` for orchestration and tools, `gatherers/` for external data collection, `mcp/` for service clients, `memory/` for persistence and retrieval, `prompts/` for Markdown prompt assets, and `chat/` for the terminal UI. Tests live under `tests/`, with focused suites such as `tests/agents/`, `tests/gatherers/`, and `tests/benchmarks/`. Utility scripts are in `scripts/`; Vagrant-based packaging checks live in `vagrant/`.

## Build, Test, and Development Commands
Set up locally with `pip install -e .` and `pip install -r requirements-dev.txt`.

- `pytest tests/ -q`: run the main test suite.
- `pytest tests/benchmarks/ -v`: run benchmark-oriented tests separately.
- `pyright src/fu7ur3pr00f`: run static type checks.
- `ruff check .`: run linting and import-order checks.
- `ruff check . --fix`: apply safe Ruff fixes.
- `python scripts/run_tests.py`: run the pre-commit validation bundle.
- `scripts/setup_precommit.sh`: install and verify Git hooks.

## Coding Style & Naming Conventions
Target Python 3.13 and keep code compatible with the `src/fu7ur3pr00f` package layout. Use 4-space indentation, `snake_case` for modules/functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Ruff is the primary linter with a 100-character line limit; `setup.cfg` retains Flake8/isort settings for compatibility, so avoid import churn and keep public APIs explicit.

## Testing Guidelines
Pytest is configured with strict markers and strict config. Name tests `test_*.py`, classes `Test*`, and functions `test_*`. Keep new tests near the behavior they cover, for example `tests/gatherers/test_html_extractor.py`. Prefer focused unit tests first; add benchmark or integration coverage only when behavior crosses modules or external clients. Mock LLMs and HTTP clients so offline behavior such as keyword routing and local CV parsing stays covered.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit prefixes such as `feat:`, `fix:`, and `docs:`. Keep subject lines short and imperative, for example `fix: handle empty profile import`. Pull requests should explain the behavioral change, list validation performed, and link the relevant issue if one exists. Include terminal output or screenshots when changing chat UX, CLI flows, or generated document output.

## Configuration & Security Tips
Copy values from `.env.example` instead of inventing new keys. Do not commit secrets, local `.env` files, or generated user data under `data/`. File-based gatherers accept paths under the home directory, repo workspace, or `/tmp`; keep SSRF and PII protections in `utils/security.py` intact. When changing external clients or gatherers, note rate limits, offline behavior, and required system packages in `README.md`.
