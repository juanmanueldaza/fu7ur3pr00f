# Tasks: remove-direct-profile-answer

## Phase 1 — Source deletion

**1.1** Delete `_direct_profile_answer` from `conversation_graph.py`
- Remove lines 27–76 (the entire function definition).
- Verify the function is no longer reachable anywhere:
  `grep -r "_direct_profile_answer" src/`

**1.2** Remove the bypass block from `execute_inner_node`
- Delete the `if turn_type == "factual":` guard and all code inside it
  (the `direct_answer` check and early return).
- `execute_inner_node` now starts directly with the `constraints` list
  construction and `orchestrator = get_orchestrator()`.

## Phase 2 — Test cleanup

**2.1** Delete `TestDirectProfileAnswer` from `test_conversation_graph.py`
- Remove the `from fu7ur3pr00f.agents.blackboard.conversation_graph import _direct_profile_answer` import.
- Remove the entire `TestDirectProfileAnswer` class (2 test methods).
- `TestTurnClassifierHeuristics` MUST remain untouched.

**2.2** Add replacement regression test
- In `test_conversation_graph.py` (or a new `test_engine.py`), add a test:
  `test_factual_query_reaches_coach` — mock the executor, assert
  `on_specialist_start` is called with `"coach"` for "who am i?".
  Use `mock_llm` fixture; do not make real LLM calls.

## Phase 3 — Verification

**3.1** Confirm no remaining references
- `grep -r "_direct_profile_answer" .` → zero matches.

**3.2** Run full test suite
- `pytest tests/ -q` — all green.
- `ruff check .` — clean.
- `pyright src/fu7ur3pr00f` — clean.

## Completion Criteria

- [x] `_direct_profile_answer` deleted from source and tests
- [x] Bypass block removed from `execute_inner_node`
- [x] `TestDirectProfileAnswer` deleted
- [x] 1 new regression test added
- [x] `pytest tests/ -q` green
- [x] `ruff check .` clean
- [x] `pyright src/fu7ur3pr00f` clean
