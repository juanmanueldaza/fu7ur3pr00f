```
█████████████████████████████████████████████████████████

  ███████ ██    ██ ▄▄▄█████▓ ██    ██ ██████   ██████
▒██    ▒ ██    ██ ▓  ██▒ ▓▒██    ██▒██    ▒ ▒██    ▒
░ ▓██▄  ██    ██ ▒ ▓██░ ▒░██    ██░ ▓██▄   ░ ▓██▄
  ▒   ██▒██  ██▒ ░ ▓██▓ ░ ▒██   ██░  ▒   ██▒  ▒   ██▒
▒██████▒▒█████▓    ▒██▒ ░ ░ ████▓▒░▒██████▒▒▒██████▒▒
▒ ▒▓▒ ▒ ▒▒▓▒ ▒ ░  ██░   ░ ▒░▒░▒░ ▒ ▒▓▒ ▒ ░▒ ▒▓▒ ▒ ░
░ ░▒  ░ ░░▒  ░ ░  ██░     ░ ▒ ▒░ ░ ░▒  ░ ░░ ░▒  ░ ░
░  ░  ░  ░     ░██░   ░ ░ ░ ▒  ░  ░  ░  ░  ░  ░
      ░  ░       ░        ░ ░        ░         ░

  AI career agent: 41 tools, 12 MCP servers, 5 specialists.

█████████████████████████████████████████████████████████
```
# fu7ur3pr00f

[![PyPI version](https://img.shields.io/pypi/v/fu7ur3pr00f)](https://pypi.org/project/fu7ur3pr00f/)
[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-2.0](https://img.shields.io/badge/license-GPL--2.0-blue.svg)](LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/fu7ur3pr00f?style=flat-square)](https://pypi.org/project/fu7ur3pr00f/)
[![GitHub stars](https://img.shields.io/github/stars/juanmanueldaza/fu7ur3pr00f?style=flat-square)](https://github.com/juanmanueldaza/fu7ur3pr00f)
[![CI](https://github.com/juanmanueldaza/fu7ur3pr00f/actions/workflows/ci.yml/badge.svg)](https://github.com/juanmanueldaza/fu7ur3pr00f/actions/workflows/ci.yml)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat-square)](https://github.com/juanmanueldaza/fu7ur3pr00f/issues)
[![Good First Issues](https://img.shields.io/github/issues/juanmanueldaza/fu7ur3pr00f/good%20first%20issue?style=flat-square&label=good%20first%20issues)](https://github.com/juanmanueldaza/fu7ur3pr00f/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

Invisible infrastructure that harnesses AI agents for career intelligence.

[Concept map](FUTUREPROOF.md) · [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY.md) · [Coexisting with N3RV](docs/COEXISTENCE.md) · [Contributing](CONTRIBUTING.md)

Powered by [opencode](https://opencode.ai). Pattern-aligned with [n3rv](https://github.com/juanmanueldaza/n3rv) — same architecture philosophy, different domain.

## Why fu7ur3pr00f?

Career management is broken. Your professional data is scattered across LinkedIn ZIP exports, PDF assessments, plain-text CVs, and portfolio websites. None of it talks to each other. Job searches are manual and repetitive. CV generation is tedious and rarely ATS-optimized. There's no memory of past decisions or applications.

fu7ur3pr00f fixes this with the same approach n3rv uses for software engineering: **harness engineering** — invisible infrastructure that gives AI agents the tools, data, and context to operate intelligently on your behalf.

It collects your professional data, indexes it into a vector database, and provides AI-powered analysis, CV generation, job search, and career coaching — all through opencode, the open source AI agent runtime.

## Quick Start

```bash
# Clone and install Python deps
git clone https://github.com/juanmanueldaza/fu7ur3pr00f.git
cd fu7ur3pr00f
uv sync

# Open in opencode
opencode
```

In opencode, use slash commands:
- `/gather` — Import LinkedIn, CliftonStrengths, CV, portfolio
- `/analyze` — Skill gap analysis, career alignment, market fit
- `/generate` — ATS-optimized CV (Markdown + PDF)
- `/search` — Search job boards, track applications
- `/profile` — View/edit career identity, goals, preferences

## Architecture

```
opencode CLI
    │
    ▼
.opencode/skills/career-*/SKILL.md     ← AI instructions (Compass, Forge, Observatory)
.opencode/commands/*.md                 ← Slash commands
    │
    ▼
scripts/gather/*.py                     ← Data ingestion (Chronograph, Repository)
scripts/generate/*.py                   ← PDF rendering (Forge)
    │
    ▼
src/fu7ur3pr00f/
  ├── gatherers/    ← LinkedIn, CliftonStrengths, CV, portfolio parsers
  ├── generators/   ← Markdown → PDF (WeasyPrint)
  ├── memory/       ← ChromaDB knowledge + episodic memory (Repository)
  └── utils/        ← Security, data loading
    │
    ▼
ChromaDB (~/.fu7ur3pr00f/)              ← Vector search, semantic recall
```

See [FUTUREPROOF.md](FUTUREPROOF.md) for the full concept map and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the component breakdown.

## Career Commands

| Command | Description |
|---------|-------------|
| `/gather` | Gather career data (LinkedIn, CliftonStrengths, CV, portfolio) |
| `/profile` | View or edit your career profile |
| `/analyze` | Analyze skill gaps, career alignment, market fit |
| `/search` | Search job boards, track applications |
| `/generate` | Generate ATS-optimized CV (Markdown + PDF) |

## Coexisting with N3RV

fu7ur3pr00f and [n3rv](https://github.com/juanmanueldaza/n3rv) coexist cleanly. They share a runtime (opencode) and an architectural philosophy but operate on entirely separate data:

- nerv: `.n3rv/` directory, engineering knowledge, A2A hub for agent task delegation
- fu7ur3pr00f: `~/.fu7ur3pr00f/` directory, career knowledge, no daemons or hub

See [docs/COEXISTENCE.md](docs/COEXISTENCE.md) for the full breakdown.

## Configuration

Create or edit your profile at `~/.fu7ur3pr00f/profile.yaml`:

```yaml
identity:
  name: Your Name
  email: you@example.com
  location: City, Country
  github_username: yourhandle

professional:
  current_role: Senior Engineer
  years_experience: 8

skills:
  technical: [Python, TypeScript, Kubernetes]
  soft: [Leadership, Communication]

career:
  target_roles: [Staff Engineer, Engineering Manager]
  deal_breakers: [no relocation, remote only]

preferences:
  work_style: remote
  salary_expectations: $150K-$200K
```

Run `/profile --edit` in opencode to update interactively.

## Scripts

Standalone Python scripts for data operations:

| Script | Purpose |
|--------|---------|
| `scripts/gather/gather_linkedin.py` | Parse LinkedIn ZIP export |
| `scripts/gather/gather_portfolio.py` | Scrape portfolio website |
| `scripts/gather/gather_assessment.py` | Parse CliftonStrengths PDF |
| `scripts/gather/gather_cv.py` | Parse CV/resume file |
| `scripts/generate/render_cv.py` | Render markdown CV to PDF |

Usage:
```bash
uv run python scripts/gather/gather_linkedin.py ~/Downloads/linkedin_export.zip
uv run python scripts/generate/render_cv.py ~/.fu7ur3pr00f/data/output/cv.md
```

## Tech Stack

Python 3.13 · opencode · ChromaDB · WeasyPrint · MCP · pattern-aligned with n3rv

## Development

```bash
# Install dev tools
uv sync --group dev

# Test
uv run pytest tests/ -q

# Lint
uv run ruff check .
```

## System Dependencies (Optional)

| Feature | Package |
|---------|---------|
| CliftonStrengths PDF parsing | `sudo apt install poppler-utils` |
| CV PDF export | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libcairo2` |

---

Licensed under [GPL-2.0](LICENSE).
