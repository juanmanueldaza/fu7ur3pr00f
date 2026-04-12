# Tasks: suggest-next-fail-fast

## Phase 1 — Code change (1 file, ~7 lines)

**1.1** Edit `suggest_next_node` except block in `conversation_graph.py`
- Delete the 5 heuristic lines (`if action_items:`, `if gaps:`, `if open_questions:`).
- Update the log message from `"Suggest LLM failed, using heuristics"` to
  `"Suggest LLM failed, returning empty suggestions"`.
- `suggestions = []` is already there — leave it.

## Phase 2 — Tests

**2.1** Add test: LLM failure → `suggested_next == []`
- In `tests/agents/blackboard/test_conversation_graph.py`, add
  `test_suggest_next_returns_empty_on_llm_failure`.
- Patch `get_model` to raise `RuntimeError`.
- Call `suggest_next_node` directly with a state containing non-empty findings.
- Assert `result["suggested_next"] == []`.

**2.2** Add test: LLM success → suggestions returned
- Patch `get_model` to return a mock response with bullet-point text.
- Assert `result["suggested_next"]` is a non-empty list of strings.

## Phase 3 — Verification

**3.1** Run full test suite
- `pytest tests/ -q` — all green.
- `ruff check .` — clean.
- `pyright src/fu7ur3pr00f` — clean.

## Completion Criteria

- [x] Heuristic lines deleted from except block
- [x] Log message updated
- [x] 2 new unit tests passing
- [x] `pytest tests/ -q` green
- [x] `ruff check .` clean
- [x] `pyright src/fu7ur3pr00f` clean
