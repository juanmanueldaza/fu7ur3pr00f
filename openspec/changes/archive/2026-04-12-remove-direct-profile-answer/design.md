# Design: remove-direct-profile-answer

## Architecture Decision

### ADR-1: Full deletion, no replacement

**Decision**: Delete `_direct_profile_answer` and the bypass block entirely.
No replacement function, no alternative short-circuit.

**Rationale**: The coach already handles profile questions correctly via
`get_user_profile` → `profile.summary()`. The factual fast-path (coach-only
routing) is preserved in `route_turn_node`. Adding a replacement mechanism
would be premature — if latency becomes a problem for factual queries, address
it as a dedicated performance change (e.g. response caching, not query pattern
matching).

**Rejected**: Replacing with a data-driven lookup (e.g. if all fields present,
return profile.summary() directly) — that's a performance optimization, not
a correctness fix. Out of scope here.

---

### ADR-2: Remove entire factual guard from execute_inner_node

**Decision**: The `if turn_type == "factual":` block in `execute_inner_node` is
removed entirely (not just the `_direct_profile_answer` call inside it).

**Rationale**: The only purpose of the guard is the short-circuit. Without the
short-circuit, the guard is dead code — the inner graph handles factual queries
the same way as any other query. The `factual` → `coach` fast-path is enforced
upstream in `route_turn_node`; no need to duplicate the check.

---

## Code Changes

### `agents/blackboard/conversation_graph.py`

**Remove** (lines 27–76): the entire `_direct_profile_answer` function.

**Remove** (inside `execute_inner_node`): the factual guard block:
```python
# DELETE THIS ENTIRE BLOCK:
if turn_type == "factual":
    direct_answer = _direct_profile_answer(query, user_profile)
    if direct_answer:
        blackboard = {
            "query": query,
            "findings": {
                "coach": {
                    "reasoning": direct_answer,
                    "confidence": 1.0,
                }
            },
            "synthesis": {"narrative": direct_answer},
            "errors": [],
        }
        return {**state, "current_blackboard": blackboard}
```

The `execute_inner_node` function then proceeds directly to fetching the
orchestrator and running `executor.execute()`.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Coach LLM fails to call get_user_profile for "who am i" | Low | Medium | Covered by specialist_guidance.md prompt; coach always calls get_user_profile first |
| Latency regression on factual queries | Medium | Low | Acceptable tradeoff; document in change notes |
| Test_conversation_graph imports _direct_profile_answer and fails | Certain | Low | Delete TestDirectProfileAnswer class and the import in the same commit |
