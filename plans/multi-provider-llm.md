# Multi-Provider LLM Support: Implementation Plan

## Current State

FutureProof is locked to Azure OpenAI. Three files enforce this:

**`llm/fallback.py`** — The LLM engine
- `_create_model()` (line 108): `if config.provider != "azure": raise ValueError`
- `DEFAULT_FALLBACK_CHAIN` (line 33): hardcoded 5 Azure models
- `get_available_models()` (line 140): checks `settings.has_azure` only
- `get_model()` (line 167): same `has_azure` gate
- `_build_purpose_chain()` (line 252): hardcodes `ModelConfig("azure", ...)`
- `get_model_for_purpose()` (line 273): reads `settings.azure_*_deployment`
- Error message (line 183): "Please configure AZURE_OPENAI_API_KEY"

**`config.py`** — Settings
- Lines 17-28: All LLM settings are `azure_*` prefixed
- `has_azure` property (line 84): only provider availability check
- No settings for OpenAI, Anthropic, Google, Ollama, or proxy

**`memory/embeddings.py`** — Vector embeddings
- `AzureOpenAIEmbeddingFunction` (line 27): uses `openai.AzureOpenAI` client directly
- `get_embedding_function()` (line 170): checks `azure_openai_api_key` and `azure_embedding_deployment`

### Key Insight

LangChain's `init_chat_model()` (already used at line 106) supports `openai`, `anthropic`, `google_genai`, `azure_openai`, `ollama`, and any OpenAI-compatible endpoint out of the box. The refactor removes the Azure-only restriction — it doesn't build a new abstraction.

---

## Provider Configuration (`config.py`)

Add new settings alongside existing Azure ones (backward compatible):

```python
# LLM Provider (auto-detected if empty)
llm_provider: str = ""  # "futureproof", "openai", "anthropic", "google", "azure", "ollama"

# FutureProof Proxy (default — zero-config for new users)
futureproof_proxy_url: str = "https://llm.futureproof.dev"
futureproof_proxy_key: str = ""  # Issued at signup with free starter tokens

# OpenAI
openai_api_key: str = ""

# Anthropic
anthropic_api_key: str = ""

# Google Gemini
google_api_key: str = ""

# Ollama (local)
ollama_base_url: str = "http://localhost:11434"

# Provider-agnostic purpose routing (replaces azure_*_deployment)
agent_model: str = ""      # e.g. "gpt-5-mini", "claude-sonnet-4-20250514"
analysis_model: str = ""   # e.g. "gpt-4.1", "claude-sonnet-4-20250514"
summary_model: str = ""    # e.g. "gpt-4o-mini", "claude-haiku-4-5-20251001"
synthesis_model: str = ""  # e.g. "o4-mini"
embedding_model: str = ""  # e.g. "text-embedding-3-small"
```

Add availability properties (same pattern as `has_azure`, `has_github_mcp`):

```python
@property
def has_openai(self) -> bool:
    return bool(self.openai_api_key)

@property
def has_anthropic(self) -> bool:
    return bool(self.anthropic_api_key)

@property
def has_google(self) -> bool:
    return bool(self.google_api_key)

@property
def has_ollama(self) -> bool:
    # Check if Ollama is running — but don't block startup
    return bool(self.ollama_base_url)

@property
def has_proxy(self) -> bool:
    return bool(self.futureproof_proxy_key)
```

### Provider Detection Priority

```python
@property
def active_provider(self) -> str:
    """Determine the active LLM provider. Priority:
    1. Explicit LLM_PROVIDER setting
    2. FutureProof proxy (if key exists)
    3. Auto-detect from available API keys (Azure > OpenAI > Anthropic > Google)
    4. Ollama (if configured)
    """
    if self.llm_provider:
        return self.llm_provider
    if self.has_proxy:
        return "futureproof"
    if self.has_azure:
        return "azure"
    if self.has_openai:
        return "openai"
    if self.has_anthropic:
        return "anthropic"
    if self.has_google:
        return "google"
    if self.has_ollama:
        return "ollama"
    return ""  # No provider configured
```

Backward compatible: existing `AZURE_*` env vars work identically. If only Azure is configured, `active_provider` returns `"azure"` and behavior is unchanged.

---

## Multi-Provider Model Creation (`llm/fallback.py`)

### Provider-to-`init_chat_model` Mapping

Replace the Azure-only `_create_model()` with a provider-aware version:

```python
# Map FutureProof provider names to LangChain model_provider strings
_PROVIDER_MAP = {
    "futureproof": "openai",  # Proxy is OpenAI-compatible
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google_genai",
    "azure": "azure_openai",
    "ollama": "ollama",
}
```

New `_build_provider_kwargs()`:

| Provider | Required kwargs |
|----------|----------------|
| `azure` | `azure_deployment`, `azure_endpoint`, `api_version`, `api_key` |
| `openai` | `api_key` |
| `futureproof` | `api_key`, `base_url` (proxy URL) |
| `anthropic` | `api_key` |
| `google` | `google_api_key` |
| `ollama` | `base_url` |

The FutureProof proxy is OpenAI-compatible (it's LiteLLM), so it uses `model_provider="openai"` with a custom `base_url`.

### Dynamic Fallback Chain

Replace hardcoded `DEFAULT_FALLBACK_CHAIN` with a function:

```python
def build_default_chain() -> list[ModelConfig]:
    """Build fallback chain from configured providers."""
    provider = settings.active_provider
    if not provider:
        return []

    # Provider-specific default model chains
    chains = {
        "futureproof": [  # Proxy routes to best available
            ModelConfig("futureproof", "gpt-4.1", "FutureProof GPT-4.1"),
            ModelConfig("futureproof", "gpt-5-mini", "FutureProof GPT-5 Mini"),
            ModelConfig("futureproof", "gpt-4o-mini", "FutureProof GPT-4o Mini"),
        ],
        "openai": [
            ModelConfig("openai", "gpt-4.1", "OpenAI GPT-4.1"),
            ModelConfig("openai", "gpt-4o", "OpenAI GPT-4o"),
            ModelConfig("openai", "gpt-4o-mini", "OpenAI GPT-4o Mini"),
        ],
        "anthropic": [
            ModelConfig("anthropic", "claude-sonnet-4-20250514", "Claude Sonnet 4"),
            ModelConfig("anthropic", "claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
        ],
        "google": [
            ModelConfig("google", "gemini-2.5-flash", "Gemini 2.5 Flash"),
            ModelConfig("google", "gemini-2.5-pro", "Gemini 2.5 Pro"),
        ],
        "azure": DEFAULT_AZURE_CHAIN,  # Today's 5-model chain
        "ollama": [
            ModelConfig("ollama", "qwen3", "Ollama Qwen3"),
        ],
    }
    return chains.get(provider, [])
```

### Purpose-Based Routing

Generalize `get_model_for_purpose()` to work across providers:

```python
def get_model_for_purpose(purpose: str, temperature: float | None = None):
    # New provider-agnostic settings (preferred)
    purpose_map = {
        "agent": settings.agent_model,
        "analysis": settings.analysis_model,
        "summary": settings.summary_model,
        "synthesis": settings.synthesis_model,
    }

    # Fallback to Azure-specific settings (backward compat)
    azure_map = {
        "agent": settings.azure_agent_deployment,
        "analysis": settings.azure_analysis_deployment,
        "summary": settings.azure_summary_deployment,
        "synthesis": settings.azure_synthesis_deployment,
    }

    model_name = purpose_map.get(purpose, "") or azure_map.get(purpose, "")
    if model_name:
        provider = settings.active_provider
        config = ModelConfig(provider, model_name, f"{provider} {model_name}")
        chain = [config] + [c for c in build_default_chain() if c.model != model_name]
    else:
        chain = None
    return get_fallback_manager().get_model(temperature=temperature, chain=chain)
```

### `get_available_models()` Fix

Replace `settings.has_azure` gate with provider-agnostic check:

```python
def get_available_models(self) -> list[ModelConfig]:
    return [
        config for config in self._chain
        if self._model_key(config) not in self._failed_models
    ]
```

The chain itself is built from configured providers, so no need to double-check availability.

### Error Message

Replace "Please configure AZURE_OPENAI_API_KEY" (line 183) with:
```
"No LLM provider configured. Sign up for free tokens at https://futureproof.dev/signup, "
"or set OPENAI_API_KEY, ANTHROPIC_API_KEY, or install Ollama for local models."
```

---

## Multi-Provider Embeddings (`memory/embeddings.py`)

Update `get_embedding_function()` to support multiple providers:

| Provider | Embedding Approach |
|----------|-------------------|
| `azure` | Existing `AzureOpenAIEmbeddingFunction` (unchanged) |
| `openai` / `futureproof` | `openai.OpenAI` client with `text-embedding-3-small` |
| `anthropic` | Not supported (Anthropic has no embedding API) — fall back to OpenAI or local |
| `google` | `google.generativeai` with `text-embedding-004` |
| `ollama` | `ollama.embeddings()` with `nomic-embed-text` or similar |
| None | ChromaDB default (sentence-transformers, slow but works) |

Add an `OpenAIEmbeddingFunction` class (similar to `AzureOpenAIEmbeddingFunction` but using `openai.OpenAI` instead of `openai.AzureOpenAI`). Reuse `CachedEmbeddingFunction` wrapper — it's already provider-agnostic.

Update factory:

```python
def get_embedding_function():
    provider = settings.active_provider
    model = settings.embedding_model

    if provider == "azure" and settings.azure_embedding_deployment:
        base = AzureOpenAIEmbeddingFunction()
    elif provider in ("openai", "futureproof") and (settings.has_openai or settings.has_proxy):
        base = OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key or settings.futureproof_proxy_key,
            base_url=settings.futureproof_proxy_url if provider == "futureproof" else None,
            model=model or "text-embedding-3-small",
        )
    elif provider == "ollama":
        base = OllamaEmbeddingFunction(
            base_url=settings.ollama_base_url,
            model=model or "nomic-embed-text",
        )
    else:
        return None  # ChromaDB default (sentence-transformers)

    return CachedEmbeddingFunction(base)
```

---

## Dependency Changes (`pyproject.toml`)

Use optional extras so users only install what they need:

```toml
[project.optional-dependencies]
anthropic = ["langchain-anthropic>=0.3"]
google = ["langchain-google-genai>=2"]
ollama = ["langchain-ollama>=0.3"]
all-providers = [
    "futureproof[anthropic]",
    "futureproof[google]",
    "futureproof[ollama]",
]
```

`langchain-openai` is already a dependency (required for Azure too). OpenAI and FutureProof proxy work without additional packages.

`init_chat_model` raises a helpful `ImportError` if a provider package is missing — no need for custom error handling.

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/futureproof/config.py` | Add provider settings, availability properties, `active_provider` |
| `src/futureproof/llm/fallback.py` | Multi-provider `_create_model()`, dynamic fallback chain, provider-agnostic purpose routing |
| `src/futureproof/memory/embeddings.py` | Add `OpenAIEmbeddingFunction`, `OllamaEmbeddingFunction`, update factory |
| `pyproject.toml` | Add optional provider extras |

---

## Testing Strategy

- **Provider kwargs**: Mock `init_chat_model` for each provider, verify correct kwargs passed.
- **Provider detection**: Set different env var combinations, verify `active_provider` returns correctly.
- **Fallback chain**: Verify dynamic chain construction from each provider.
- **Backward compatibility**: With only `AZURE_*` vars set, verify behavior is identical to current.
- **No-provider error**: With no env vars, verify helpful error message.
- **Embedding fallback**: Verify correct embedding function selected per provider.

---

## Migration Path

**Phase 1**: Multi-provider `_create_model()` + config + FutureProof proxy as default. Azure behavior unchanged for existing users.

**Phase 2**: Multi-provider embeddings (OpenAI, Ollama local).

**Phase 3**: Free starter token flow (signup → API key → works immediately).
