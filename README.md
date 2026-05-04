# fu7ur3pr00f

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL-2.0](https://img.shields.io/badge/license-GPL--2.0-blue.svg)](LICENSE)

Career intelligence opencode workspace — skills, commands, and scripts for gathering professional data, analyzing career trajectories, generating ATS-optimized CVs, and searching job boards.

Powered by [opencode](https://opencode.ai) with [nerv](https://github.com/juanmanueldaza/nerv) for memory and agent orchestration.

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
- `/gather` — Import LinkedIn, GitHub, CliftonStrengths, CV
- `/analyze` — Get skill gap analysis
- `/search` — Search job boards, track applications
- `/generate` — Create ATS-optimized CV (Markdown + PDF)
- `/profile` — View/edit career profile

## Architecture

```
opencode CLI
    │
    ▼
.opencode/skills/career-*/SKILL.md     ← Instructions for AI
.opencode/commands/*.md                 ← User slash commands
    │
    ▼
scripts/gather/*.py                     ← Data gathering entry points
scripts/generate/*.py                   ← PDF rendering
    │
    ▼
src/fu7ur3pr00f/
  ├── gatherers/    ← LinkedIn, GitHub, CliftonStrengths, CV parsers
  ├── generators/   ← Markdown → PDF (WeasyPrint)
  ├── memory/       ← ChromaDB knowledge + episodic memory
  └── utils/        ← Security, data loading
    │
    ▼
ChromaDB (via nerv-memory MCP)
```

## Career Commands

| Command | Description |
|---------|-------------|
| `/gather` | Gather career data (LinkedIn, CliftonStrengths, CV, portfolio) |
| `/profile` | View or edit your career profile |
| `/analyze` | Analyze skill gaps, career alignment, market fit |
| `/search` | Search job boards, track applications |
| `/generate` | Generate ATS-optimized CV (Markdown + PDF) |

## Configuration

Create a profile at `config/profile.yml`:

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
  technical: [Python, TypeScript, Kubernetes, ...]
  soft: [Leadership, Communication, ...]

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

Python 3.13 · opencode · ChromaDB · nerv (memory + hub) · WeasyPrint · MCP

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
