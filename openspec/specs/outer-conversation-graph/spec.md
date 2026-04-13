# Spec: Outer Conversation Graph

## Requirement: Factual queries follow the coach-only route

The outer graph MUST NOT use a separate direct profile-answer short-circuit for
factual profile questions. Factual routing SHALL continue through the existing
coach-only path.

### Scenario: Direct profile-answer helper is absent

```text
Given  the source tree after archiving the change
When   searching for _direct_profile_answer
Then   no active source file contains that helper
```

### Scenario: Factual query reaches coach through normal execution

```text
Given  a factual query such as "who am i?"
When   the outer graph routes the turn
Then   the coach specialist handles the turn
 And   the normal tool-based execution path remains in use
```

## Requirement: Suggest-next fails soft with empty suggestions

When optional suggestion generation fails inside `suggest_next_node`, the node
MUST return an empty list of suggestions and MUST NOT fabricate heuristic text.

### Scenario: Suggestion LLM failure returns empty suggestions

```text
Given  non-empty findings are available
 And   the suggestion LLM call raises an exception
When   suggest_next_node finishes
Then   the returned suggested_next value is []
 And   the failure is logged
```

### Scenario: Suggestion LLM success still returns parsed suggestions

```text
Given  the suggestion LLM returns bullet-point next steps
When   suggest_next_node finishes successfully
Then   the returned suggested_next value contains the parsed suggestions
 And   no heuristic fallback strings are added
```
