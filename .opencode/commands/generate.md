---
description: Generate ATS-optimized CV in Markdown and PDF
agent: build
model: opencode-go/qwen3.5-plus
skill: career-cv
---
Generate an ATS-optimized CV tailored to a target role. $ARGUMENTS

## Workflow

1. Check knowledge base has data. If not, tell user to run `/gather` first.

2. Load career data and profile:
   ```python
   from fu7ur3pr00f.utils.data_loader import load_career_data_for_cv
   from fu7ur3pr00f.memory.profile import load_profile
   data = load_career_data_for_cv()
   profile = load_profile()
   ```

3. Parse arguments:
   - `--role "Senior ML Engineer"` — target role to tailor for
   - `--language en|es` — output language (default: en)
   - `--format ats|creative` — CV style (default: ats)

4. Generate CV in Markdown using LLM:
   - Professional summary aligned with target role
   - Experience with quantified achievements
   - Skills section with keywords from target role
   - Education, certifications, projects
   - Use standard ATS-friendly section headers

5. Save markdown and render PDF:
   ```python
   from fu7ur3pr00f.generators import save_cv_markdown
   path = save_cv_markdown(cv_content, "cv_ats_en.md")
   ```
   ```
   uv run python scripts/generate/render_cv.py <path>
   ```

6. Report output paths to user.
