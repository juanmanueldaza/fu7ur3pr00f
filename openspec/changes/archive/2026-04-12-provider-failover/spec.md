# Spec: provider-failover

## Domain: LLM Model Selection

### REQ-1 — Provider availability check

**REQ-1.1** A module-level function `_is_configured(config: ModelConfig) -> bool`
MUST be added to `llm/model_selection.py`.

**REQ-1.2** `_is_configured` MUST return `True` only if the provider's required
credentials are set in `settings`, using the existing detection properties:

| Provider | Condition |
|----------|-----------|
| `fu7ur3pr00f` | `settings.has_proxy` |
| `openai` | `settings.has_openai` |
| `anthropic` | `settings.has_anthropic` |
| `google` | `settings.has_google` |
| `azure` | `settings.has_azure` |
| `ollama` | `settings.has_ollama` |
| unknown | `False` |

---

### REQ-2 — Chain walk in get_model

**REQ-2.1** `ModelSelectionManager.get_model()` MUST iterate over
`effective_chain` in order.

**REQ-2.2** For each `ModelConfig` in the chain, the method MUST:
1. Skip (log DEBUG) if `_is_configured(config)` returns `False`
2. Attempt `_create_model(config, temperature)`
3. On success: update `self._current_model` and return `(model, config)`
4. On exception: log WARNING with the error and continue to the next config

**REQ-2.3** If all configs are exhausted without a successful model, `get_model()`
MUST raise `RuntimeError` with a message that includes the last error and
guidance to check provider API keys.

**REQ-2.4** The return type MUST remain `tuple[BaseChatModel, ModelConfig]`.
Callers MUST NOT be modified.

---

### REQ-3 — Behaviour unchanged when chain[0] is available

**REQ-3.1** When `chain[0]` is configured and `_create_model` succeeds,
`get_model()` MUST return that model — same as today.

**REQ-3.2** Performance: the walk MUST stop at the first success. No unnecessary
model instantiation.

---

## Scenarios

### Scenario 1 — First provider configured, returned immediately

```
Given  chain = [gpt-4.1 (openai), gpt-4o (openai)]
 And   settings.has_openai is True
When   get_model() is called
Then   returns gpt-4.1 model without attempting gpt-4o
```

### Scenario 2 — First provider not configured, second is

```
Given  chain = [gpt-4.1 (openai), claude-sonnet (anthropic)]
 And   settings.has_openai is False
 And   settings.has_anthropic is True
When   get_model() is called
Then   skips gpt-4.1 with DEBUG log
 And   returns claude-sonnet model
```

### Scenario 3 — First config raises, second succeeds

```
Given  chain = [gpt-4.1 (openai), gpt-4o (openai)]
 And   settings.has_openai is True
 And   _create_model(gpt-4.1) raises ValueError("model not found")
When   get_model() is called
Then   logs WARNING for gpt-4.1
 And   returns gpt-4o model
```

### Scenario 4 — All configs exhausted

```
Given  chain = [gpt-4.1 (openai)]
 And   settings.has_openai is False
When   get_model() is called
Then   raises RuntimeError containing guidance to check API keys
```

### Scenario 5 — Empty chain

```
Given  chain = []
When   get_model() is called
Then   raises RuntimeError immediately (existing behaviour)
```
