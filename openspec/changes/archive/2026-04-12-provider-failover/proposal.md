# Proposal: provider-failover

## Intent

`ModelSelectionManager.get_model()` always uses `chain[0]` and never walks the
provider chain. The chain (e.g. `[gpt-4.1, gpt-5-mini, gpt-4o, gpt-4o-mini]`
for OpenAI) exists precisely to degrade gracefully when the preferred model is
unavailable, but the walk logic was never implemented.

### What was validated against LangChain docs

**`init_chat_model` already has `max_retries=6` by default** (exponential
backoff with jitter) that handles transient failures: network errors, rate
limits (429), server errors (5xx). This covers the "LLM is momentarily down"
case — no code change needed.

**`with_fallbacks()` is LangChain's native invocation-time failover**, but it
returns `RunnableWithFallbacks`, which does NOT have `bind_tools()` or
`with_structured_output()`. Both methods are called on models returned by
`get_model()` throughout the codebase (`base.py:151`, `routing.py:191`). Using
`with_fallbacks()` would require type-breaking API changes to all callers.

### What CAN be fixed now

The chain walk at **model creation time**. When `_create_model` raises (e.g.
a provider SDK is not installed, a required env var is missing, or a model name
is outright invalid), the current code surfaces the error immediately. With the
chain walk, it tries the next config in the chain.

Additionally, a `_is_configured(config)` check can skip providers whose API
key is not set in `settings`, before even attempting `_create_model`. This
prevents needless SDK calls when a provider is simply not set up.

### What is explicitly deferred

Invocation-time failover (when `.invoke()` fails after the model is created)
requires `with_fallbacks()`. This needs a companion change to:
- Restructure callers to not call `bind_tools()` directly on the returned model
- Or return `(BaseChatModel, ModelConfig)` for tool-binding callers and
  `RunnableWithFallbacks` for invoke-only callers

That is a separate, type-breaking change tracked separately.

## Scope

### In Scope
- Add `_is_configured(config: ModelConfig) -> bool` that checks whether the
  provider's required API key / endpoint is set in `settings`
- Walk the chain in `ModelSelectionManager.get_model()`: skip unconfigured
  providers first, then try `_create_model` for each remaining config, stopping
  at the first success
- Return the same `tuple[BaseChatModel, ModelConfig]` — no API change

### Out of Scope
- `with_fallbacks()` / invocation-time failover — deferred (see above)
- Changing `_PROVIDER_CHAINS` content (model names, ordering)
- Cross-provider chain restructuring

## Capabilities

| # | Capability | Acceptance Criteria |
|---|------------|---------------------|
| C1 | Unconfigured providers skipped | If `openai_api_key` is unset, OpenAI models not attempted |
| C2 | Chain walked on creation failure | If `_create_model(chain[0])` raises, `chain[1]` is tried |
| C3 | First successful model returned | `get_model()` returns the first creatable+configured model |
| C4 | Error raised only when chain exhausted | `RuntimeError` only if all configs fail or are unconfigured |
| C5 | Return type unchanged | `tuple[BaseChatModel, ModelConfig]` — callers unaffected |

## Approach

```python
def get_model(self, temperature=None, chain=None):
    effective_chain = chain or self._chain
    if not effective_chain:
        raise RuntimeError("No LLM provider configured...")

    last_error: Exception | None = None
    for config in effective_chain:
        if not _is_configured(config):
            logger.debug("Skipping %s: provider not configured", config.description)
            continue
        try:
            model = self._create_model(config, temperature=temperature)
            with self._lock:
                self._current_model = config
            logger.info("Using model: %s", config.description)
            return model, config
        except Exception as e:
            logger.warning("Model %s failed: %s", config.description, e)
            last_error = e

    raise RuntimeError(
        f"No model available. Last error: {last_error}. "
        "Check provider API keys and model availability."
    )
```

## Rollback Plan

Single file: `llm/model_selection.py`. No data migrations, no schema changes.

## Risks

- **`_is_configured` must be correct** — if it incorrectly skips a configured
  provider, `get_model()` will skip valid models. Must test each provider check
  against real settings field names.
- **Performance**: `_create_model` is cheap (object instantiation) so the chain
  walk adds negligible latency.
