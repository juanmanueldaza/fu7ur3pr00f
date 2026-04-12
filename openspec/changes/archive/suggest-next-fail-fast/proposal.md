# Proposal: suggest-next-fail-fast

## Intent

`suggest_next_node` in `conversation_graph.py` has a heuristic fallback when
the LLM call fails. Instead of returning `[]`, it constructs strings like
`"Start with: {action_items[0]}"` and `"Address the gap: {gaps[0]}"` from raw
specialist output.

This is wrong for two reasons:

1. **Inconsistent with the no-hardcoded-fallbacks policy.** CLAUDE.md states
   that all guidance lives in `prompts/md/` and the system errors on missing
   prompts. `suggest_next_node` is the only graph node that silently substitutes
   hardcoded template strings when the LLM fails.

2. **Misleading output.** The heuristic strings look like real LLM-synthesised
   suggestions but are raw data concatenations. The user cannot tell the
   difference, and may act on low-quality "suggestions" that were never
   actually reasoned about.

Suggestions (`suggested_next`) are non-critical: the main synthesis is already
delivered before this node runs. The chat client already handles `[]` gracefully
(renders nothing). Returning `[]` on failure is the correct behaviour.

## Scope

### In Scope
- Replace the heuristic fallback in the `except Exception:` block with
  `suggestions = []`
- Remove the 5 lines that build heuristic strings from `action_items`, `gaps`,
  `open_questions`
- Keep the `except` clause (log the warning, set `suggestions = []`)

### Out of Scope
- Changes to the `suggest_next.md` prompt
- Changes to how suggestions are displayed in `chat/client.py`
- Removing the `suggest_next_node` entirely

## Capabilities

| # | Capability | Acceptance Criteria |
|---|------------|---------------------|
| C1 | LLM failure returns `[]` not heuristic strings | `except` block sets `suggestions = []` |
| C2 | Warning still logged on failure | `logger.warning(...)` retained |
| C3 | Happy path unchanged | When LLM succeeds, suggestions returned normally |
| C4 | Chat client unaffected | `if result.suggested_next:` guard already handles `[]` |

## Rollback Plan

Revert 5 lines in `conversation_graph.py`. Trivial.

## Risks

None. Suggestions are optional. Chat client already handles `[]`.
