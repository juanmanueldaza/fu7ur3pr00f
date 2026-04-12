# Tasks: provider-failover

## Phase 1 — _is_configured helper

**1.1** Add `_PROVIDER_CONFIGURED_MAP` dict to `llm/model_selection.py`
- Place after `_PROVIDER_CHAINS` dict.
- Maps provider name strings to lambdas reading `settings.has_*`.
- Include all 6 providers: `fu7ur3pr00f`, `openai`, `anthropic`, `google`,
  `azure`, `ollama`.

**1.2** Add `_is_configured(config: ModelConfig) -> bool` function
- Looks up `config.provider` in `_PROVIDER_CONFIGURED_MAP`.
- Returns `False` for unknown providers.
- Module-level, not a method.

## Phase 2 — Chain walk in get_model

**2.1** Replace `ModelSelectionManager.get_model()` body
- Remove: `config = effective_chain[0]` and the single `_create_model` call.
- Add: loop over `effective_chain`, skip unconfigured, try `_create_model`,
  catch exceptions, continue to next.
- Add: `last_error` tracker.
- Add: `RuntimeError` at end of loop if no model succeeded.
- Keep: `self._lock` update on success.
- Keep: `logger.info("Using model: %s", ...)` on success.

## Phase 3 — Tests

**3.1** Test `_is_configured` for each provider
- Mock `settings` with each `has_*` set to True/False.
- Assert correct True/False return for all 6 providers.
- Assert False for unknown provider string.

**3.2** Test chain walk: first config unconfigured, second used
- Mock `_is_configured` to return False for `chain[0]`, True for `chain[1]`.
- Mock `_create_model` to return a mock `BaseChatModel`.
- Assert `get_model()` returns config from `chain[1]`.

**3.3** Test chain walk: first config raises, second succeeds
- Mock `_is_configured` to return True for both.
- Mock `_create_model` to raise on `chain[0]`, succeed on `chain[1]`.
- Assert `get_model()` returns config from `chain[1]`.
- Assert WARNING was logged.

**3.4** Test chain exhausted → RuntimeError
- Mock `_is_configured` to return False for all configs.
- Assert `RuntimeError` is raised.
- Assert error message mentions "API keys".

**3.5** Test happy path unchanged
- Mock `_is_configured` to return True for `chain[0]`.
- Mock `_create_model` to succeed on `chain[0]`.
- Assert `get_model()` returns `chain[0]`'s model without touching `chain[1]`.

## Phase 4 — Verification

**4.1** Run full test suite
- `pytest tests/ -q` — all green.
- `ruff check .` — clean.
- `pyright src/fu7ur3pr00f` — clean.

## Completion Criteria

- [x] `_PROVIDER_CONFIGURED_MAP` and `_is_configured` added
- [x] `ModelSelectionManager.get_model()` walks chain
- [x] 5 new unit tests passing
- [x] `pytest tests/ -q` green
- [x] `ruff check .` clean
- [x] `pyright src/fu7ur3pr00f` clean
