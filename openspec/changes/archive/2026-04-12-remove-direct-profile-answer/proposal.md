# Proposal: remove-direct-profile-answer

## Intent

`conversation_graph.py` contains a 50-line function `_direct_profile_answer`
that intercepts factual queries (e.g. "who am I?", "what's my name?") before
the inner blackboard graph runs. It pattern-matches the query string and
constructs a hardcoded answer from raw profile dict fields.

This is wrong for three reasons:

1. **Hardcoded patterns only.** Handles a fixed list of exact phrases. "tell me
   about myself", "describe my background" → falls through to the inner graph.
   "who am I" → bypasses it. The coverage is arbitrary and invisible to the user.

2. **Inconsistent with architecture.** Every specialist guideline, routing
   prompt, and synthesis prompt is loaded from `prompts/md/` with no hardcoded
   fallbacks. `_direct_profile_answer` is the only place that constructs an
   answer from code instead of letting the LLM + tools do it.

3. **Duplication.** `turn_classifier.py` already has `_FACTUAL_QUERY_PATTERNS`
   that detects the same queries and routes them to coach-only. The coach has
   `get_user_profile` in its toolkit (via `BASE_TOOLKIT`) which returns
   `profile.summary()` — a richer, structured answer than the hardcoded string.

## Scope

### In Scope
- Delete `_direct_profile_answer` from `conversation_graph.py`
- Remove the `if turn_type == "factual": direct_answer = ...` bypass block in
  `execute_inner_node`
- Delete the 2 existing tests in `TestDirectProfileAnswer`
- Add regression tests confirming factual queries are answered by the coach

### Out of Scope
- Changes to `turn_classifier.py` — `_FACTUAL_QUERY_PATTERNS` stays; it
  correctly classifies turn type and enables the coach fast-path routing
- Changes to the coach agent, its tools, or its prompts
- Performance optimisation of factual queries (separate concern)

## Capabilities

| # | Capability | Acceptance Criteria |
|---|------------|---------------------|
| C1 | `_direct_profile_answer` deleted | Function no longer exists in codebase |
| C2 | Factual queries reach the inner graph | "who am i" routes to coach via blackboard |
| C3 | Coach answers profile questions via `get_user_profile` | `get_user_profile` called during factual turn execution |
| C4 | No hardcoded profile string assembly in `execute_inner_node` | The bypass block is removed |

## Rollback Plan

Revert one file (`conversation_graph.py`) and restore the 2 deleted tests.
No data migrations. No schema changes.

## Risks

- **Latency increase** for "who am I"-style queries: now incurs an LLM call +
  tool call. Acceptable — the system requires LLM access to function; there is
  no offline mode.
- **Behaviour change**: the answer will now be richer (LLM-synthesised from
  `profile.summary()`) rather than a fixed template string. This is a
  deliberate improvement, not a regression.
- **Test deletion**: 2 tests in `TestDirectProfileAnswer` are deleted. They
  tested the removed function — not behavioral regressions. Replace with a
  higher-level test confirming the coach is invoked.
