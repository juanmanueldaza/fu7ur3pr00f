---
description: Search job boards and track applications
agent: build
model: opencode-go/qwen3.5-plus
skill: career-search
---
Search for jobs matching the user's profile and track applications. $ARGUMENTS

## Workflow

1. Parse arguments:
   - `--query "senior backend engineer"` — search query
   - `--source remoteok|weworkremotely|himalayas|...` — specific board
   - `--track` — view application tracker

2. If tracking, load episodic memory:
   ```python
   from fu7ur3pr00f.memory.episodic import get_episodic_store, MemoryType
   store = get_episodic_store()
   results = store.recall("", memory_type=MemoryType.APPLICATION, limit=50)
   ```

3. If searching, use web search or job board APIs. Present results with:
   - Company, role, location, salary
   - Quick match score against user profile
   - Link to apply

4. Offer to save interesting jobs to tracker:
   ```python
   from fu7ur3pr00f.memory.episodic import remember_application
   remember_application(company="...", role="...", status="saved", notes="...")
   ```
