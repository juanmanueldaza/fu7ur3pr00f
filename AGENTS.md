# Repository Guidelines — fu7ur3pr00f

## Project Structure & Module Organization
This repository uses a `src/` layout. Core code lives in `src/fu7ur3pr00f/`:

| Directory | Purpose |
|-----------|---------|
| `agents/` | Multi-agent orchestration, blackboard, specialist agents |
| `agents/specialists/` | Agent implementations (coach, code, jobs, learning, founder) |
| `agents/tools/` | 41 LangChain StructuredTools (profile, market, financial, etc.) |
| `agents/blackboard/` | Shared state (CareerBlackboard TypedDict) |
| `chat/` | Terminal UI (prompt-toolkit based) |
| `gatherers/` | External data collection (LinkedIn, portfolio, job market) |
| `generators/` | CV/document generation |
| `llm/` | LLM provider abstractions, model selection |
| `mcp/` | Model Context Protocol service clients |
| `memory/` | Persistence and retrieval (ChromaDB, SQLite) |
| `prompts/` | Markdown prompt assets |
| `services/` | Business logic services |
| `utils/` | Shared utilities (security, helpers) |

Tests live under `tests/` mirroring the source layout. Utility scripts in `scripts/`.

## Build, Test, and Development Commands

### Setup
```bash
pip install -e .
pip install -r requirements-dev.txt
```

### Running Tests
```bash
pytest tests/ -q                          # full suite (quiet)
pytest tests/ -v                          # full suite (verbose)
pytest tests/test_config.py -v            # single test file
pytest tests/test_config.py::TestSettings::test_default_values -v  # single test
pytest tests/agents/tools/ -v             # all tool tests
pytest tests/ -m unit -v                  # unit tests only
pytest tests/ -m integration -v           # integration tests only
pytest tests/ -x --tb=short               # stop on first failure
```

### Linting & Type Checking
```bash
ruff check .                              # lint (E, F, I, UP rules)
ruff check . --fix                        # auto-fix safe issues
pyright src/fu7ur3pr00f                   # static type check (pyright)
mypy src tests                            # static type check (mypy)
```

### Pre-commit Validation
```bash
python scripts/run_tests.py               # run type check + lint + tests
scripts/setup_precommit.sh                # install git hooks
```

## Code Style & Conventions

### Imports
- Standard library → third-party → local (`fu7ur3pr00f.*`)
- Use absolute imports from `fu7ur3pr00f`, never relative imports across packages
- Group imports with blank lines between groups; isort profile `black`
- **Lazy imports**: Inside functions to break circular deps (see Architecture Notes)

### Formatting
- **Black** for code formatting (line length 88)
- **Ruff** for linting (line length 100, rules: E, F, I, UP)
- 4-space indentation, no tabs
- Trailing commas on multiline collections

### Naming Conventions
- `snake_case` for modules, functions, variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Test files: `test_*.py`, classes: `Test*`, functions: `test_*`

### Types
- Target Python 3.13; use modern type hints (`dict[str, str]` not `Dict[str, str]`)
- Prefer explicit return types on public functions
- Use `None` return annotation for void functions

### Error Handling
- Raise specific exceptions (ValueError, RuntimeError) with descriptive messages
- Use pydantic validation for config/data models
- Mock LLMs and HTTP clients in tests — never make real API calls
- Sanitize user input in `utils/security.py` (SSRF, PII protections)

## Testing Guidelines
- Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Use shared fixtures from `tests/conftest.py` (`tmp_project`, `mock_llm`, `sample_career_data`)
- Mock external services (LLMs, HTTP clients, MCP servers) — patch at source module
- Keep tests focused; one assertion concept per test
- **Key mock patterns**: Lazy imports must be patched at source module, not at call site

## Extending the Agent System

### Adding a New Specialist
1. Create `src/fu7ur3pr00f/agents/specialists/my_specialist.py`
2. Subclass `BaseAgent`, implement `name`, `description`, `system_prompt`, `tools`
3. Add a prompt file `src/fu7ur3pr00f/prompts/md/specialist_my_specialist.md`
4. Register in `src/fu7ur3pr00f/agents/specialists/orchestrator.py`
5. Add tests in `tests/agents/specialists/test_my_specialist.py`

Example specialist:
```python
from fu7ur3pr00f.agents.specialists.base import BaseAgent
from fu7ur3pr00f.agents.specialists.toolkits import MY_TOOLS
from fu7ur3pr00f.prompts import load_prompt

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my_agent"

    @property
    def description(self) -> str:
        return "My specialist description"

    @property
    def system_prompt(self) -> str:
        return load_prompt("specialist_my_agent")

    @property
    def tools(self) -> list:
        return MY_TOOLS
```

### Adding a New Tool
1. Create or add to `src/fu7ur3pr00f/agents/tools/my_tools.py`
2. Use `@tool` decorator from `langchain_core.tools`
3. Return strings (not dicts) — the LLM reads string outputs
4. Add to a toolkit in `agents/specialists/toolkits.py`
5. Add tests in `tests/agents/tools/test_my_tools.py`

Example tool:
```python
from langchain_core.tools import tool

@tool
def my_tool(arg1: str, arg2: int = 5) -> str:
    """Short docstring for the LLM. Args are parsed for tool schema."""
    result = do_something(arg1, arg2)
    return f"Result: {result}"
```

## Architecture Notes

### Blackboard Pattern
Specialists collaborate via `CareerBlackboard` (TypedDict). Each specialist:
1. Reads `query`, `user_profile`, and previous `findings` from the blackboard
2. Runs its multi-turn tool-calling loop
3. Returns a `SpecialistFinding` with `reasoning`, `confidence`, and domain-specific keys
4. Findings from all specialists are merged for final synthesis

### Circular Import Mitigation
Modules use lazy imports inside functions to break circular dependency chains:
- `base.py` imports `get_model` inside methods (not at module level)
- `tools/` modules import services inside functions
- `config.py` uses mixins (`LLMProviderMixin`, `IntegrationMixin`, `KnowledgeMixin`, `PathManager`)
- Constants are split into sub-modules under `constants/` with a re-export facade

A full architectural refactor to eliminate lazy imports would require:
- Dependency injection container for singletons
- Proper layer separation (config → services → agents → tools)
- This is planned for a future release when the architecture stabilizes

## Commit & Pull Request Guidelines
- Conventional Commit prefixes: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Subject lines: short, imperative (`fix: handle empty profile import`)
- PRs should explain the behavioral change, list validation performed, link relevant issues

## Configuration & Security Tips
- Copy values from `.env.example`; never commit `.env` or secrets
- Do not commit generated user data under `data/`
- File-based gatherers accept paths under home directory, repo workspace, or `/tmp`
- Keep SSRF and PII protections in `utils/security.py` intact
- Click<8.3 constraint documented in pyproject.toml — workaround for Typer 0.24 compatibility
