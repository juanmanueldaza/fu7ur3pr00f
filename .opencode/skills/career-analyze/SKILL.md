---
name: career-analyze
description: "Analyze skill gaps, career alignment, and market fit using ChromaDB knowledge."
compatibility: opencode
when_to_use: "When the user wants career analysis, skill gap assessment, or market positioning."
model: high
user-invocable: false
---

# Skill: Career Analyze

Analyze career data from the knowledge base against target roles and market data.

## Prerequisites

Career data must be gathered first. Check knowledge base:
```python
from fu7ur3pr00f.memory.knowledge import get_knowledge_store
store = get_knowledge_store()
stats = store.get_stats()
```

If `stats["total_chunks"] == 0`, tell the user to run `/gather` first.

## Analysis Types

1. **Skill Gap Analysis**: Compare current skills against target role requirements
2. **Career Alignment**: How well current trajectory aligns with goals
3. **Market Fit**: Salary expectations vs market data, location analysis
4. **Strength Leverage**: How to apply CliftonStrengths to target roles

## Workflow

1. Load career data: `from fu7ur3pr00f.utils.data_loader import load_career_data_for_analysis`
2. Load profile: `from fu7ur3pr00f.memory.profile import load_profile`
3. Search for market data or use web search for salary/trend info
4. Use your LLM reasoning to produce structured analysis
5. Present findings to user with actionable recommendations

## Output Format

```
## Skill Gap Analysis: [Target Role]

### Current Skills
[from profile + knowledge base]

### Required Skills
[from market research]

### Gaps
- Missing: [list]
- Emerging: [list]

### Recommendations
1. [actionable step]
2. [actionable step]
```
