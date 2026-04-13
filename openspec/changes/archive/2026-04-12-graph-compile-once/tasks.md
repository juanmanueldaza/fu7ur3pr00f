# Tasks: graph-compile-once

## Phase 1 — Infrastructure (no behavior change)

**1.1** Add `_callbacks` dict to `ConversationEngine.__init__`
- In `engine.py`, add `self._callbacks: dict[str, Any] = {}` before the graph build.
- No other changes in this step — verify tests still pass.

**1.2** Change `build_conversation_graph()` signature
- Replace the 5 individual callback params with `callbacks: dict | None = None`.
- Assign `_cb = callbacks if callbacks is not None else {}` at the top of the function.
- In `execute_inner_node`, replace all 5 direct callback references with
  `_cb.get("on_specialist_start")`, etc.
- The function still gets called with keyword args in `engine.py` — update that
  call to pass `callbacks=self._callbacks`.

**1.3** Compile graph once in `ConversationEngine.__init__`
- Replace `self._build_graph = build_conversation_graph` with:
  ```python
  self._graph = build_conversation_graph(
      checkpointer=self._checkpointer,
      callbacks=self._callbacks,
  )
  ```
- Remove the `self._build_graph` attribute entirely.

## Phase 2 — Per-turn wiring

**2.1** Update `invoke_turn()` to populate the holder
- At the start of `invoke_turn()`, before loading session state, add:
  ```python
  self._callbacks.update({
      "on_specialist_start": on_specialist_start,
      "on_specialist_complete": on_specialist_complete,
      "on_tool_start": on_tool_start,
      "on_tool_result": on_tool_result,
      "confirm_fn": confirm_fn,
  })
  ```
- Remove the `graph = self._build_graph(checkpointer=..., on_specialist_start=..., ...)` call.
- Replace `result_state = graph.invoke(session_state, config)` with
  `result_state = self._graph.invoke(session_state, config)`.

## Phase 3 — Tests

**3.1** Add unit test: graph compiled exactly once
- In `tests/agents/blackboard/test_conversation_graph.py` (or a new
  `test_engine.py`), mock `build_conversation_graph` and assert it is called
  once on engine init and zero times across multiple `invoke_turn()` calls.

**3.2** Add unit test: callbacks change between turns
- Call `invoke_turn()` twice with different `on_specialist_start` spies.
- Assert each spy is called only during its respective turn.
- Use `mock_llm` fixture; patch executor to avoid real LLM calls.

**3.3** Add unit test: None callbacks don't raise
- Call `invoke_turn()` with all callbacks as `None`.
- Assert `TurnResult` is returned without error.

## Phase 4 — Cleanup & docs

**4.1** Add sequential-use docstring to `ConversationEngine`
- Document: "Not safe for concurrent `invoke_turn()` calls on the same instance.
  If concurrent use is needed, use `contextvars.ContextVar` instead of a shared dict."

**4.2** Run full test suite and linter
- `pytest tests/ -q`
- `ruff check .`
- `pyright src/fu7ur3pr00f`

## Completion Criteria

- [x] `build_conversation_graph` called exactly once per engine instance
- [x] All 5 callbacks dispatched correctly per turn
- [x] `reset_conversation_engine()` triggers fresh compile
- [x] 3 new tests passing
- [x] `pytest tests/ -q` green
- [x] `ruff check .` clean
- [x] `pyright src/fu7ur3pr00f` clean
