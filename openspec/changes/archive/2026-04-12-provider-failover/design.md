# Design: provider-failover

## Architecture Decisions

### ADR-1: Creation-time chain walk only (not invocation-time)

**Decision**: Walk the chain in `get_model()` at model CREATION time. Do not
use `with_fallbacks()` for invocation-time failover.

**Rationale** (validated against LangChain docs):
- `init_chat_model` already has `max_retries=6` with exponential backoff that
  handles transient 429s, 5xx errors, and network failures — the common case.
- `with_fallbacks()` returns `RunnableWithFallbacks`, which does NOT have
  `bind_tools()` or `with_structured_output()`. Both are called on models
  returned by `get_model()` in `base.py:151` and `routing.py:191`.
  Using `with_fallbacks()` would require type-breaking changes to all callers.
- Creation-time chain walk handles: wrong model name, provider SDK not installed,
  invalid model config. These are real failure modes in multi-provider setups.

**Deferred**: Invocation-time failover via `with_fallbacks()`. Requires:
a) Separate callers that need `bind_tools` from invoke-only callers, OR
b) Add `bind_tools` / `with_structured_output` to a wrapper around
   `RunnableWithFallbacks`.

---

### ADR-2: Reuse settings.has_* properties

**Decision**: `_is_configured()` maps `ModelConfig.provider` to the existing
`settings.has_proxy`, `settings.has_openai`, etc. properties.

**Rationale**: `settings.has_openai` already checks the key format
(`sk-` prefix), not just presence. Duplicating that logic in model_selection
would violate DRY and risk drift. The properties are the single source of truth
for provider availability.

---

## Code Changes

### `llm/model_selection.py`

**Add** `_is_configured` (module-level, after `_PROVIDER_CHAINS`):

```python
_PROVIDER_CONFIGURED_MAP: dict[str, Callable[[], bool]] = {
    "fu7ur3pr00f": lambda: settings.has_proxy,
    "openai":      lambda: settings.has_openai,
    "anthropic":   lambda: settings.has_anthropic,
    "google":      lambda: settings.has_google,
    "azure":       lambda: settings.has_azure,
    "ollama":      lambda: settings.has_ollama,
}


def _is_configured(config: ModelConfig) -> bool:
    """Return True if the provider's credentials are set in settings."""
    check = _PROVIDER_CONFIGURED_MAP.get(config.provider)
    return check() if check is not None else False
```

**Replace** `ModelSelectionManager.get_model()`:

```python
def get_model(
    self,
    temperature: float | None = None,
    chain: list[ModelConfig] | None = None,
) -> tuple[BaseChatModel, ModelConfig]:
    effective_chain = chain or self._chain
    if not effective_chain:
        raise RuntimeError(
            "No LLM provider configured. Sign up at https://fu7ur3pr00f.dev/signup, "
            "or set OPENAI_API_KEY, ANTHROPIC_API_KEY, or install Ollama."
        )

    last_error: Exception | None = None
    for config in effective_chain:
        if not _is_configured(config):
            logger.debug(
                "Skipping %s: provider not configured", config.description
            )
            continue
        try:
            model = self._create_model(config, temperature=temperature)
            with self._lock:
                self._current_model = config
            logger.info("Using model: %s", config.description)
            return model, config
        except Exception as e:
            logger.warning(
                "Model %s failed to initialise: %s — trying next",
                config.description,
                sanitize_error(str(e)),
            )
            last_error = e

    raise RuntimeError(
        "No model available in the configured chain. "
        f"Last error: {sanitize_error(str(last_error))}. "
        "Check provider API keys and model availability."
    )
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `_is_configured` incorrectly skips a configured provider | Low | High | Unit test each provider mapping against mock settings |
| Chain walk masks a real misconfiguration | Low | Medium | WARNING log on each skip; user can check logs |
| `sanitize_error` imported (already in scope) | Certain | None | Already used in `_create_model` |
| Invocation-time failures still unhandled | Certain | Low | Documented; `max_retries=6` already covers transient failures |
