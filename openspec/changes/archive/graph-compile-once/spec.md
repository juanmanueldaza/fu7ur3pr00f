# Spec: graph-compile-once

## Domain: Agent Execution (Outer Graph)

### REQ-1 — Graph compilation

**REQ-1.1** `ConversationEngine` MUST compile the outer LangGraph `StateGraph`
exactly once, during `__init__`, and store it as `self._graph`.

**REQ-1.2** `invoke_turn()` MUST NOT call `build_conversation_graph()`.

**REQ-1.3** After `reset_conversation_engine()` is called, the next call to
`get_conversation_engine()` MUST create a new `ConversationEngine` instance,
triggering a fresh compile.

---

### REQ-2 — Per-turn callback wiring

**REQ-2.1** `ConversationEngine.__init__` MUST initialise a `_callbacks` dict
(the holder) and close over it in the graph nodes.

**REQ-2.2** `invoke_turn()` MUST update `self._callbacks` with the current
turn's callables before invoking the graph.

**REQ-2.3** Node functions inside `build_conversation_graph()` MUST read
callbacks from the holder at execution time, not from closure-captured
variables set at compile time.

**REQ-2.4** `build_conversation_graph()` MUST NOT accept individual callback
parameters (`on_specialist_start`, `on_specialist_complete`, `on_tool_start`,
`on_tool_result`, `confirm_fn`). It SHALL accept a single `callbacks: dict`
parameter instead.

---

### REQ-3 — Unchanged interfaces

**REQ-3.1** `invoke_turn()` signature MUST remain identical: same parameter
names, same types, same `TurnResult` return type.

**REQ-3.2** `chat/client.py` MUST require zero changes.

**REQ-3.3** The inner graph, executor, and specialist nodes MUST NOT be
modified.

---

### REQ-4 — Thread safety contract

**REQ-4.1** The `ConversationEngine` SHALL document that `invoke_turn()` is not
safe for concurrent calls on the same instance (sequential use only, matching
current chat client behavior).

---

## Scenarios

### Scenario 1 — Graph compiled once

```
Given  a new ConversationEngine is instantiated
When   __init__ completes
Then   self._graph is a compiled LangGraph Pregel instance
 And   build_conversation_graph has been called exactly once
 And   invoke_turn has not been called
```

### Scenario 2 — Callbacks dispatched correctly

```
Given  a compiled engine
 And   invoke_turn is called with on_specialist_start=<spy_fn>
When   a specialist executes inside the inner graph
Then   the outer node reads on_specialist_start from self._callbacks
 And   passes it to executor.execute()
 And   spy_fn is called at least once
```

### Scenario 3 — Callbacks change between turns

```
Given  a compiled engine
When   invoke_turn is called with on_specialist_start=fn_A
 And   invoke_turn is called again with on_specialist_start=fn_B
Then   the first turn dispatches fn_A
 And   the second turn dispatches fn_B
 And   build_conversation_graph is called exactly once total
```

### Scenario 4 — Engine reset

```
Given  an existing engine singleton
When   reset_conversation_engine() is called
 And   get_conversation_engine() is called
Then   a new ConversationEngine is created
 And   build_conversation_graph is called once more
```

### Scenario 5 — None callbacks

```
Given  invoke_turn is called with all callback params as None
When   the graph executes
Then   execution completes without error
 And   TurnResult is returned with correct synthesis and specialists
```
