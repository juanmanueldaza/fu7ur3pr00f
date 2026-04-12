# Spec: remove-direct-profile-answer

## Domain: Outer Conversation Graph

### REQ-1 — Deletion

**REQ-1.1** The function `_direct_profile_answer` MUST be removed from
`conversation_graph.py`.

**REQ-1.2** The following block inside `execute_inner_node` MUST be removed:
```python
if turn_type == "factual":
    direct_answer = _direct_profile_answer(query, user_profile)
    if direct_answer:
        blackboard = { ... }
        return {**state, "current_blackboard": blackboard}
```

**REQ-1.3** The `if turn_type == "factual":` guard MAY be removed entirely from
`execute_inner_node`, since the factual routing fast-path (coach-only) is
already applied upstream in `route_turn_node`.

---

### REQ-2 — Factual query routing (unchanged)

**REQ-2.1** `turn_classifier.py` and its `_FACTUAL_QUERY_PATTERNS` MUST NOT
be modified.

**REQ-2.2** Factual queries MUST continue to route to `["coach"]` only via the
existing `route_turn_node` fast-path.

**REQ-2.3** The coach MUST answer profile questions using the `get_user_profile`
tool (already in `BASE_TOOLKIT`).

---

### REQ-3 — Tests

**REQ-3.1** `TestDirectProfileAnswer` class MUST be deleted from
`test_conversation_graph.py`.

**REQ-3.2** A replacement test MUST verify that a factual query causes the
coach's `get_user_profile` tool to be invoked.

---

## Scenarios

### Scenario 1 — _direct_profile_answer no longer exists

```
Given  the codebase after this change
When   searching for _direct_profile_answer
Then   no matches are found in any source file
```

### Scenario 2 — Factual query reaches inner graph

```
Given  a compiled conversation engine
 And   on_specialist_start is wired
When   invoke_turn("who am i?") is called
Then   on_specialist_start is called with "coach"
 And   TurnResult.synthesis.narrative is non-empty
```

### Scenario 3 — Coach uses get_user_profile

```
Given  invoke_turn("who am i?") is called with a mock LLM that calls get_user_profile
When   the turn executes
Then   get_user_profile is invoked exactly once
 And   TurnResult.synthesis.narrative contains profile data
```

### Scenario 4 — Turn classifier unchanged

```
Given  "who am i?" is passed to classify()
When   classify() runs (no LLM, heuristic path)
Then   result is "factual"
 And   TestTurnClassifierHeuristics tests continue to pass
```
