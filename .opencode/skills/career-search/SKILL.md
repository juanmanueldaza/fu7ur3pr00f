---
name: career-search
description: "Search job boards, scan company portals, and track applications."
compatibility: opencode
when_to_use: "When the user wants to search for jobs or track applications."
model: medium
user-invocable: false
hub-skill-ids:
  - career-intelligence
  - search
allowed-tools:
  - Bash
  - WebFetch
  - mcp__nerv-memory__memory_search
  - mcp__nerv-memory__memory_save
---

# Skill: Career Search

Search job boards and track applications using the ChromaDB episodic memory.

## Job Search

1. Use web search (`tavily` MCP if configured) or direct HTTP to search job boards
2. Parse results and present to user with:
   - Company, role, location, salary (if available)
   - Link to apply
   - Quick match assessment

## Job Boards

- RemoteOK, WeWorkRemotely, Himalayas, Remotive, Jobicy (via `python-jobspy` package)
- Hacker News "Who is hiring" threads
- Company career pages (manual)

## Application Tracking

Use episodic memory to track applications:
```python
from fu7ur3pr00f.memory.episodic import remember_application, get_episodic_store
```

### Remember an application:
```python
remember_application(company="Acme Corp", role="Senior Engineer", status="applied", notes="...")
```

### Search past applications:
```python
store = get_episodic_store()
results = store.recall("machine learning engineer")
```

## Pipeline Viewing

Use ChromaDB to query by status:
```python
store = get_episodic_store()
results = store.recall("", memory_type=MemoryType.APPLICATION, limit=50)
```
