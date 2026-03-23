# Development Guide

## Setup

```bash
git clone https://github.com/juanmanueldaza/fu7ur3pr00f.git
cd fu7ur3pr00f
pip install -e .
pip install pyright pytest ruff
```

## Quality Checks

```bash
# Lint
ruff check .
ruff check . --fix  # Auto-fix

# Type check
pyright src/fu7ur3pr00f

# Test
pytest tests/ -q
pytest tests/ -k test_name  # Specific test
```

## Project Structure

```
src/fu7ur3pr00f/
├── agents/           # Single agent, middleware, orchestrator, tools
├── chat/             # CLI client, HITL loop, Rich UI
├── gatherers/        # LinkedIn, GitHub, GitLab, portfolio, CliftonStrengths
├── generators/       # CV generation (Markdown + PDF)
├── llm/              # Multi-provider fallback routing
├── memory/           # ChromaDB RAG + episodic memory
├── mcp/              # MCP clients (GitHub, Tavily, job boards)
├── prompts/          # System + analysis + CV prompts
├── services/         # Business logic layer
└── utils/            # Security, logging, data loading
```

## Adding a Tool

1. Create tool function in `src/fu7ur3pr00f/agents/tools/<domain>.py`
2. Register in `career_agent.py`
3. Add tests in `tests/agents/tools/`

```python
# Example tool
def analyze_skill_gap(profile: str, target: str) -> str:
    """Analyze skill gaps between profile and target role."""
    ...

# Register in career_agent.py
tools.append(analyze_skill_gap)
```

## Adding a Gatherer

1. Create gatherer in `src/fu7ur3pr00f/gatherers/`
2. Return `Section` NamedTuple
3. Index to ChromaDB
4. Add tests

```python
from collections import namedtuple

Section = namedtuple("Section", ["title", "content", "metadata"])

def gather_linkedin() -> Section:
    """Gather LinkedIn profile data."""
    ...
```

## Testing

### Unit Tests

Use fixtures from `tests/conftest.py`:

```python
def test_gatherer(mock_chromadb, mock_llm):
    ...
```

**Mocking:** Mock external services:

```python
from unittest.mock import patch

@patch("httpx.get")
def test_portfolio_fetch(mock_get):
    mock_get.return_value.status_code = 200
    ...
```

**Running Tests:**

```bash
pytest tests/ -q                    # All tests
pytest tests/ -k "gather"           # By keyword
pytest tests/ --cov=src             # With coverage
```

### Integration Tests

**Fresh Install Connectivity Check:**

Validate a clean pipx install plus MCP/LLM connectivity:

```bash
# From local source
scripts/fresh_install_check.sh --source local --config-from .env

# From PyPI
scripts/fresh_install_check.sh --source pypi --config-from .env
```

This script:
- Creates a temporary HOME directory
- Installs fu7ur3pr00f via pipx
- Tests LLM connectivity
- Tests MCP client connectivity
- Cleans up afterward

**Apt Package Validation (Docker):**

Test .deb package installs/uninstalls cleanly:

```bash
# Build the package first
scripts/build_deb.sh

# Validate in Docker containers
scripts/validate_apt_artifact.sh dist/deb/fu7ur3pr00f_*.deb
```

Tests in:
- `ubuntu:24.04`
- `debian:12`

Verifies: install → version → reinstall → remove → purge → clean

### Vagrant Testing

Use Vagrant for isolated testing of the apt installation path without risking your host OS.

**Requirements:**
- Vagrant
- VirtualBox (or another provider)

**Available Boxes:**

| Box | Description |
|-----|-------------|
| `ubuntu2404` | Ubuntu 24.04 LTS |
| `debian12` | Debian 12 (Bookworm) |

**Running Tests:**

```bash
# Test Ubuntu 24.04
scripts/run_vagrant_apt_smoke.sh ubuntu2404

# Test Debian 12
scripts/run_vagrant_apt_smoke.sh debian12

# Test all boxes
scripts/run_vagrant_apt_smoke.sh all

# Keep VM after test (for debugging)
scripts/run_vagrant_apt_smoke.sh debian12 --keep
```

**What the Script Does:**

1. Boots a disposable VM from `vagrant/Vagrantfile`
2. Adds the public apt repository
3. Runs `install`, `reinstall`, `remove`, and `purge` for `fu7ur3pr00f`
4. Destroys the VM after the run (unless `--keep` is used)

**Manual Vagrant Usage:**

```bash
cd vagrant

# Boot and provision
vagrant up ubuntu2404 --provision
vagrant up debian12 --provision

# Destroy
vagrant destroy -f ubuntu2404 debian12
```

**Development VM:**

For interactive development in a VM:

```bash
scripts/vagrant_dev_setup.sh setup   # Copy data/.env and start VM
scripts/vagrant_dev_setup.sh ssh     # SSH into VM
scripts/vagrant_dev_setup.sh destroy # Clean up
```

See [vagrant/README.md](../vagrant/README.md) for details.

## Debugging

```bash
fu7ur3pr00f --debug  # Verbose logging
```

## Cleaning Up

```bash
# Remove build artifacts
scripts/clean_dev_artifacts.sh
```

See [Scripts Reference](scripts.md) for all available scripts.

## See Also

- [Contributing](../CONTRIBUTING.md)
- [Architecture](architecture.md)
- [QWEN.md](../QWEN.md)
