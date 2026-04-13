# Spec: suggest-next-fail-fast

## Domain: Outer Conversation Graph

### REQ-1 — Failure behaviour

**REQ-1.1** When `suggest_next_node`'s LLM call raises any exception, the node
MUST set `suggestions = []` and MUST NOT construct heuristic strings.

**REQ-1.2** The `except Exception:` block MUST retain the `logger.warning(...,
exc_info=True)` call.

**REQ-1.3** The following lines MUST be removed from the `except` block:
```python
if action_items:
    suggestions.append(f"Start with: {action_items[0]}")
if gaps:
    suggestions.append(f"Address the gap: {gaps[0]}")
if open_questions:
    suggestions.append(f"Explore: {open_questions[0]}")
```

---

### REQ-2 — Happy path unchanged

**REQ-2.1** When the LLM call succeeds, `suggest_next_node` MUST return
`suggestions[:3]` as before.

**REQ-2.2** The early-return paths (`factual` turn type, empty findings) MUST
remain unchanged.

---

### REQ-3 — Tests

**REQ-3.1** A test MUST verify that when the LLM raises an exception inside
`suggest_next_node`, `suggested_next` is `[]` in the returned state.

---

## Scenarios

### Scenario 1 — LLM failure → empty suggestions

```
Given  suggest_next_node is called with non-empty findings
 And   the LLM raises RuntimeError
When   the node returns
Then   state["suggested_next"] == []
 And   a WARNING is logged
```

### Scenario 2 — LLM success → suggestions returned

```
Given  suggest_next_node is called with non-empty findings
 And   the LLM returns "- Learn Docker\n- Update LinkedIn"
When   the node returns
Then   state["suggested_next"] == ["Learn Docker", "Update LinkedIn"]
```

### Scenario 3 — Chat client handles empty suggestions

```
Given  TurnResult.suggested_next == []
When   the chat client renders the response
Then   the "Suggested next steps" section is not displayed
 And   no error is raised
```
