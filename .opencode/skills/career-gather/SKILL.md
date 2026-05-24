---
name: career-gather
description: "Gather professional data: LinkedIn, GitHub, CliftonStrengths, CV/resume, portfolio."
compatibility: opencode
when_to_use: "When the user wants to collect career data from external sources."
model: medium
user-invocable: false
hub-skill-ids:
  - career-intelligence
  - data-gathering
allowed-tools:
  - Bash
  - Read
  - Glob
---

# Skill: Career Gather

Collect professional data and index it into the ChromaDB knowledge base.

## Data Sources

| Source | Script | Input |
|--------|--------|-------|
| LinkedIn | `scripts/gather/gather_linkedin.py` | ZIP export from LinkedIn |
| Portfolio | `scripts/gather/gather_portfolio.py` | Optional URL |
| CliftonStrengths | `scripts/gather/gather_assessment.py` | PDF from Gallup |
| CV/Resume | `scripts/gather/gather_cv.py` | .pdf, .md, or .txt file |

## Workflow

1. Ask the user what data they have available
2. For each source, run the corresponding script via bash:
   ```
   uv run python scripts/gather/gather_<source>.py <path>
   ```
3. Scripts auto-index to ChromaDB via `get_knowledge_store()`
4. Confirm to the user what was gathered and indexed

## Edge Cases

- **No data available yet**: Guide user to export LinkedIn ZIP, find CliftonStrengths PDF, or create a CV markdown file
- **Script fails**: Show the error, suggest checking file format and dependencies (poppler-utils for PDFs)
- **Already indexed**: Scripts replace old data (safe-swap: index new, then delete old)

## Dependencies

- `poppler-utils` for PDF text extraction (`pdftotext`)
- All Python deps in pyproject.toml
