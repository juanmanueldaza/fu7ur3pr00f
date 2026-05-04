---
description: Gather professional data from LinkedIn, GitHub, CliftonStrengths, and CV
agent: build
model: opencode-go/qwen3.5-plus
skill: career-gather
---
Gather professional career data from available sources.

## Workflow

1. Ask what data sources the user has available:
   - LinkedIn ZIP export
   - Portfolio URL
   - CliftonStrengths PDF
   - CV/Resume file (.pdf, .md, .txt)

2. For each source, run the corresponding script:
   ```
   uv run python scripts/gather/gather_linkedin.py <path>
   uv run python scripts/gather/gather_portfolio.py [url]
   uv run python scripts/gather/gather_assessment.py [dir]
   uv run python scripts/gather/gather_cv.py <path>
   ```

3. Confirm indexed results to the user.

4. If no data sources available, guide the user on how to get them:
   - LinkedIn: Settings → Data Privacy → Get a copy of your data
   - CliftonStrengths: Download PDF from Gallup portal
   - CV: Create a markdown file at data/raw/cv.md
