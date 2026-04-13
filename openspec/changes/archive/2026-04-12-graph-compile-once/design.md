# Design: graph-compile-once

## Architecture Decision

### ADR-1: _CallbackHolder (mutable dict) over recompile

**Decision**: Close over a mutable `self._callbacks` dict in node functions at
compile time. Update the dict contents per turn before `graph.invoke()`.

**Rationale**:
- The outer graph nodes cannot receive per-call data through LangGraph state
  (callables are not JSON-serializable and cannot live in the checkpointer).
- `get_stream_writer()` / `stream_mode="custom"` is already used by the INNER
  graph (`graph.py` + `executor.py`) — that layer is correct and untouched.
- `contextvars.ContextVar` would also work but adds complexity for a codebase
  that is synchronous and single-threaded per engine instance.
- A mutable dict closed over at `__init__` time is the minimal, safe solution
  for a sequential caller.

**Rejected**: Full `get_stream_writer()` migration at the outer graph level —
the inner graph already handles this correctly. Migrating the outer graph too
would duplicate the dispatch logic for no benefit.

**Rejected**: `contextvars.ContextVar` — correct but over-engineered for
current sequential use. Leave as a documented migration path if concurrency is
ever needed.

---

### ADR-2: keep graph.invoke() at outer level

**Decision**: The outer graph continues using `self._graph.invoke()`. No
migration to `graph.stream()` at this layer.

**Rationale**: The outer graph synthesizes a final response and returns full
state — `invoke()` is the right API for this. The inner graph streams for
real-time events (already done). Mixing streaming at the outer level would
require unwinding the `accumulate → synthesize → suggest_next` pipeline and
parsing final state from chunks — complexity with no gain.

---

## Code Changes

### `agents/blackboard/engine.py`

```python
class ConversationEngine:
    def __init__(self) -> None:
        from fu7ur3pr00f.agents.blackboard.conversation_graph import (
            build_conversation_graph,
        )
        checkpointer = get_checkpointer()
        self._checkpointer = checkpointer
        # Mutable holder — updated per turn, read by nodes at execution time
        self._callbacks: dict[str, Any] = {}
        # Compile once — nodes close over self._callbacks
        self._graph = build_conversation_graph(
            checkpointer=checkpointer,
            callbacks=self._callbacks,
        )

    def invoke_turn(self, query, thread_id="main", user_profile=None,
                    on_specialist_start=None, on_specialist_complete=None,
                    on_tool_start=None, on_tool_result=None,
                    confirm_fn=None) -> TurnResult:
        # Update holder before invoking — nodes read this at execution time
        self._callbacks.update({
            "on_specialist_start": on_specialist_start,
            "on_specialist_complete": on_specialist_complete,
            "on_tool_start": on_tool_start,
            "on_tool_result": on_tool_result,
            "confirm_fn": confirm_fn,
        })
        ...
        result_state = self._graph.invoke(session_state, config)
        ...
```

### `agents/blackboard/conversation_graph.py`

```python
def build_conversation_graph(
    checkpointer: Any = None,
    callbacks: dict | None = None,   # replaces 5 individual params
) -> ...:
    _cb = callbacks if callbacks is not None else {}

    def execute_inner_node(state):
        ...
        blackboard = dict(
            executor.execute(
                query=query,
                user_profile=user_profile,
                constraints=constraints,
                on_specialist_start=_cb.get("on_specialist_start"),
                on_specialist_complete=_cb.get("on_specialist_complete"),
                on_tool_start=_cb.get("on_tool_start"),
                on_tool_result=_cb.get("on_tool_result"),
                confirm_fn=_cb.get("confirm_fn"),
            )
        )
        ...
```

The `_cb` dict is the same object as `self._callbacks` on the engine — mutating
it in `invoke_turn()` is immediately visible to nodes at execution time.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Concurrent invoke_turn calls overwrite shared _callbacks | Low | Medium | Document sequential contract; if concurrent use needed, use threading.local |
| Tests that mock build_conversation_graph break | Low | Low | Tests mock at the module level; signature change from 5 params → 1 dict param needs updating |
| Existing callers of build_conversation_graph outside engine.py | Very Low | Medium | Grep for callers before removing old params |
