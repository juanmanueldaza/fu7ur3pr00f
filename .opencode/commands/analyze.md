---
description: Analyze skill gaps, career alignment, and market fit
agent: build
model: opencode-go/qwen3.5-plus
skill: career-analyze
---
Analyze the user's career data and provide actionable insights. $ARGUMENTS

## Workflow

1. Check knowledge base has data:
   ```python
   from fu7ur3pr00f.memory.knowledge import get_knowledge_store
   store = get_knowledge_store()
   stats = store.get_stats()
   ```
   If total_chunks is 0, tell user to run `/gather` first.

2. Load career data and profile:
   ```python
   from fu7ur3pr00f.utils.data_loader import load_career_data_for_analysis
   from fu7ur3pr00f.memory.profile import load_profile
   data = load_career_data_for_analysis()
   profile = load_profile()
   ```

3. If a target role was specified, perform skill gap analysis:
   - Current skills vs role requirements
   - Missing certifications
   - Experience level match

4. If no target role, provide general career health check:
   - Skill diversity and modernity
   - Experience narrative coherence
   - Market positioning

5. Present findings as structured analysis with recommendations.
