# Design: suggest-next-fail-fast

## Architecture Decision

### ADR-1: Return [] on failure, not raise

**Decision**: Catch the exception, log a warning, return `[]`. Do not re-raise.

**Rationale**: `suggest_next_node` is the last node before `END`. The main
synthesis and specialist findings are already in state. Suggestions are a
convenience feature — propagating an exception here would abort the entire
turn delivery for a non-critical enhancement. `[]` is the semantically correct
"no suggestions available" value and is already what the node returns for
factual queries and empty findings.

**Rejected**: Re-raising the exception (fail-fast at the turn level) — too
disruptive for an optional enhancement. The fail-fast policy in CLAUDE.md
applies to missing prompts (which crash on load), not to LLM call failures
inside optional enhancement nodes.

---

## Code Change

### `agents/blackboard/conversation_graph.py` — `suggest_next_node`

**Before** (except block, lines 326–338):
```python
except Exception:
    logger.warning(
        "Suggest LLM failed, using heuristics",
        exc_info=True,
    )
    suggestions = []
    if action_items:
        suggestions.append(f"Start with: {action_items[0]}")
    if gaps:
        suggestions.append(f"Address the gap: {gaps[0]}")
    if open_questions:
        suggestions.append(f"Explore: {open_questions[0]}")
```

**After**:
```python
except Exception:
    logger.warning(
        "Suggest LLM failed, returning empty suggestions",
        exc_info=True,
    )
    suggestions = []
```

Total diff: delete 6 lines, update 1 log message.

---

## Risk Register

None. The change is contained to one except block. Chat client already handles
`[]` via the `if result.suggested_next:` guard.
