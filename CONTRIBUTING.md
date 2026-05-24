# Contributing to fu7ur3pr00f

## NERV (AI Agent Infrastructure)

This project uses [NERV](https://github.com/juanmanueldaza/nerv) for agent-native development — Spec-Driven Development (SDD) workflow, A2A agent hub, persistent memory, and OpenCode integration.

```bash
# Install NERV
git clone https://github.com/juanmanueldaza/nerv.git ~/nerv
cd ~/nerv && uv tool install .

# Initialize in this project
cd /path/to/fu7ur3pr00f
nerv init
```

See `.opencode/agents/nerv.md` for available commands, skills, and SDD agents.

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