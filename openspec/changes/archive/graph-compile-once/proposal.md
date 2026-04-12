# Proposal: graph-compile-once

## Intent

`ConversationEngine.invoke_turn()` calls `build_conversation_graph()` on every
user message, compiling a full LangGraph `StateGraph` each time. The rebuild is
forced because the current design closes over per-turn callbacks (5 Python
callables) inside node functions at compile time. Since callbacks can vary per
call, a new graph is compiled each turn.

This is the only problem. The rest of the stack is already correct:
- The inner blackboard graph (`graph.py`) already uses `get_stream_writer()` for
  real-time events.
- The executor (`executor.py`) already streams via
  `graph.stream(stream_mode=["updates", "custom"])` with interrupt handling.

The fix is minimal: compile the outer graph once in `__init__` and pass
per-turn callbacks through a mutable `_CallbackHolder` dict that node functions
read from at execution time (not at compile time).

## Scope

### In Scope
- Compile the outer `StateGraph` once in `ConversationEngine.__init__`
- Replace callback closure capture with a `_CallbackHolder` dict closed over
  in `__init__` and updated per turn in `invoke_turn()`
- Ensure `reset_conversation_engine()` still triggers a fresh compile on the
  next `get_conversation_engine()` call

### Out of Scope
- Any changes to the inner graph (`graph.py`), executor (`executor.py`), or
  specialist nodes — they are already correct
- Migrating from `graph.invoke()` to `graph.stream()` at the outer level
- LangGraph interrupt / `Command` changes
- The `StateGraph(dict)` typing issue (separate tech debt)

## Capabilities

| # | Capability | Acceptance Criteria |
|---|------------|---------------------|
| C1 | Graph compiled exactly once per engine instance | `build_conversation_graph` called in `__init__`, zero times in `invoke_turn` |
| C2 | Per-turn callbacks correctly wired | Each `invoke_turn()` call dispatches the callbacks passed to that call |
| C3 | `reset_conversation_engine()` triggers fresh compile | After reset, next `get_conversation_engine()` call compiles a new graph |
| C4 | All existing tests pass unchanged | No test modifications required |

## Approach

1. Add `_CallbackHolder` (plain `dict`) as an instance attribute on
   `ConversationEngine`, initialized in `__init__`.
2. Change `build_conversation_graph()` to accept a `callbacks: dict` parameter
   instead of the 5 individual callable parameters.
3. Nodes that previously closed over individual callbacks now read from the
   holder dict at execution time.
4. In `invoke_turn()`, populate `self._callbacks` with the current turn's
   callables before calling `self._graph.invoke()`.

## Rollback Plan

Two files: `engine.py` and `conversation_graph.py`. No data migrations, no
schema changes, no behavioral changes. Revert the commit.

## Risks

- Low effort. Topology, executor, inner graph, and chat client are untouched.
- Thread-safety note: the chat client is sequential (one turn at a time per
  engine). Document this contract. If concurrent turns are ever needed, replace
  the shared holder with a `threading.local()` or `contextvars.ContextVar`.
