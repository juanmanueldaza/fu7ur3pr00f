---
name: career-cv
description: "Generate ATS-optimized CVs in Markdown and PDF format."
compatibility: opencode
when_to_use: "When the user wants to create or update their CV/resume."
model: high
user-invocable: false
hub-skill-ids:
  - career-intelligence
  - generation
allowed-tools:
  - Bash
  - Read
  - Write
---

# Skill: Career CV

Generate tailored CVs using career data from the knowledge base.

## Prerequisites

Career data must be gathered first. Verify:
```python
from fu7ur3pr00f.utils.data_loader import load_career_data_for_cv
data = load_career_data_for_cv()
```

If empty, tell the user to run `/gather` first.

## CV Generation

1. Load career data via `load_career_data_for_cv()`
2. Load profile via `load_profile()`
3. Generate CV content in Markdown using your LLM:
   - Professional summary aligned with target role
   - Experience (from LinkedIn/CV data)
   - Skills (technical + soft)
   - Education & certifications
   - Projects & achievements
4. Save markdown: use `fu7ur3pr00f.generators.save_cv_markdown(content, filename)`
5. Render PDF: `python scripts/generate/render_cv.py path/to/cv.md`

## ATS Optimization Rules

- Use standard section headers (Experience, Education, Skills)
- Include keywords from target job descriptions naturally
- No tables, columns, or images
- Clean, simple formatting
- Quantify achievements with numbers

## Languages

- English: default
- Spanish: `--language es`

## Output

- `~/.fu7ur3pr00f/data/output/cv.md` — markdown source
- `~/.fu7ur3pr00f/data/output/cv.pdf` — ATS-optimized PDF

## Dependencies

- `weasyprint` for PDF rendering
- `libpango`, `libcairo` system libs for PDF
