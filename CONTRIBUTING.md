# Contributing to fu7ur3pr00f

## N3RV (AI Agent Infrastructure)

This project uses [N3RV](https://github.com/juanmanueldaza/n3rv) for agent-native development — Spec-Driven Development (SDD) workflow, A2A agent hub, persistent memory, and OpenCode integration.

```bash
# Install N3RV
git clone https://github.com/juanmanueldaza/n3rv.git ~/n3rv
cd ~/n3rv && uv tool install .

# Initialize in this project
cd /path/to/fu7ur3pr00f
n3rv init
```

See `.opencode/agents/n3rv.md` for available commands, skills, and SDD agents.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.
Please report unacceptable behavior according to the instructions in the Code of Conduct.

## Dev Setup

See `AGENTS.md` for coding standards, rules, and the skill index.

## Running Tests

```bash
pytest
```

## Code Style

All rules are enforced via `AGENTS.md` (loaded automatically by opencode agent).
See the **Skill Index** and **Universal Rules** sections.

## Adding Skills

See `AGENTS.md` → **Skill Index** for the full list. To add a new skill:
1. Create `.opencode/skills/<name>/SKILL.md` with required frontmatter
2. Add it to `AGENTS.md` skills table