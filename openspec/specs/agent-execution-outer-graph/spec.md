# Spec: Agent Execution (Outer Graph)

## Requirement: Graph compilation happens once per engine instance

The outer conversation engine MUST compile the LangGraph outer graph exactly
once during `ConversationEngine.__init__` and retain the compiled graph on the
engine instance.

### Scenario: Engine initialization compiles once

```text
Given  a new ConversationEngine instance
When   initialization completes
Then   a compiled outer graph is stored on the engine
 And   build_conversation_graph was called exactly once
```

## Requirement: Per-turn callbacks are resolved at execution time

The engine MUST keep a mutable callback holder that is updated before each turn
and read by the already-compiled graph during execution.

### Scenario: Different turns use different callback callables

```text
Given  a compiled engine
When   invoke_turn is called twice with different callback functions
Then   each turn dispatches only the callbacks provided for that turn
 And   the graph is not recompiled between turns
```

## Requirement: Public engine interface remains stable

`invoke_turn()` SHALL keep the same caller-facing signature and return
`TurnResult`. Existing chat-client callers MUST require no behavioral changes.

### Scenario: Existing caller still works

```text
Given  an existing chat client callsite
When   it invokes the engine after this change
Then   it uses the same invoke_turn interface
 And   receives the same TurnResult shape
```

## Requirement: Sequential-use contract is documented

The engine SHALL document that concurrent `invoke_turn()` calls on the same
instance are not supported.

### Scenario: Thread-safety contract is visible

```text
Given  a developer reading ConversationEngine documentation
When   they review the class contract
Then   they can see that the shared callback holder is for sequential use only
```
