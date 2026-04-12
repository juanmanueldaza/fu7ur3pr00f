"""LLM model selection with multi-provider support.

Selects a configured model for a given purpose. This module does not retry
or fail over across models during invocation; errors surface to the caller
with sanitized messages.
"""

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from fu7ur3pr00f.config import settings
from fu7ur3pr00f.utils.security import sanitize_error

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for a single model selection."""

    provider: str  # "fu7ur3pr00f", "openai", "anthropic", "google", "azure", "ollama"
    model: str
    description: str
    reasoning: bool = False  # Reasoning models don't support temperature


_REASONING_PREFIXES = ("o1", "o3", "o4")

_PROVIDER_MAP: dict[str, str] = {
    "fu7ur3pr00f": "openai",  # Proxy is OpenAI-compatible
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google_genai",
    "azure": "azure_openai",
    "ollama": "ollama",
}

_PROVIDER_CHAINS: dict[str, list[ModelConfig]] = {
    "fu7ur3pr00f": [
        ModelConfig("fu7ur3pr00f", "gpt-4.1", "fu7ur3pr00f GPT-4.1"),
        ModelConfig("fu7ur3pr00f", "gpt-5-mini", "fu7ur3pr00f GPT-5 Mini"),
        ModelConfig("fu7ur3pr00f", "gpt-4o", "fu7ur3pr00f GPT-4o"),
        ModelConfig("fu7ur3pr00f", "gpt-4o-mini", "fu7ur3pr00f GPT-4o Mini"),
    ],
    "openai": [
        ModelConfig("openai", "gpt-4.1", "OpenAI GPT-4.1"),
        ModelConfig("openai", "gpt-5-mini", "OpenAI GPT-5 Mini"),
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
    "azure": [
        ModelConfig("azure", "gpt-4.1", "Azure GPT-4.1"),
        ModelConfig("azure", "gpt-5-mini", "Azure GPT-5 Mini"),
        ModelConfig("azure", "gpt-4o", "Azure GPT-4o"),
        ModelConfig("azure", "gpt-4.1-mini", "Azure GPT-4.1 Mini"),
        ModelConfig("azure", "gpt-4o-mini", "Azure GPT-4o Mini"),
    ],
    "ollama": [
        ModelConfig("ollama", "qwen3", "Ollama Qwen3"),
    ],
}


_PROVIDER_CONFIGURED_MAP: dict[str, Callable[[], bool]] = {
    "fu7ur3pr00f": lambda: settings.has_proxy,
    "openai": lambda: settings.has_openai,
    "anthropic": lambda: settings.has_anthropic,
    "google": lambda: settings.has_google,
    "azure": lambda: settings.has_azure,
    "ollama": lambda: settings.has_ollama,
}


def _is_configured(config: ModelConfig) -> bool:
    """Return True if the provider's credentials are set in settings."""
    check = _PROVIDER_CONFIGURED_MAP.get(config.provider)
    return check() if check is not None else False


def build_default_chain() -> list[ModelConfig]:
    """Build the default provider model order from the active provider."""
    provider = settings.active_provider
    return list(_PROVIDER_CHAINS.get(provider, []))


def _build_provider_kwargs(config: ModelConfig) -> dict[str, Any]:
    """Build provider-specific kwargs for init_chat_model."""
    provider = config.provider
    kwargs: dict[str, Any] = {}

    if provider == "azure":
        kwargs["azure_deployment"] = config.model
        kwargs["azure_endpoint"] = settings.azure_openai_endpoint
        kwargs["api_version"] = settings.azure_openai_api_version
        kwargs["api_key"] = settings.azure_openai_api_key
    elif provider == "fu7ur3pr00f":
        kwargs["api_key"] = settings.fu7ur3pr00f_proxy_key
        kwargs["base_url"] = settings.fu7ur3pr00f_proxy_url
    elif provider == "openai":
        kwargs["api_key"] = settings.openai_api_key
    elif provider == "anthropic":
        kwargs["api_key"] = settings.anthropic_api_key
    elif provider == "google":
        kwargs["google_api_key"] = settings.google_api_key
    elif provider == "ollama":
        kwargs["base_url"] = settings.ollama_base_url

    return kwargs


class ModelSelectionManager:
    """Selects configured models for a provider and purpose."""

    def __init__(
        self,
        model_chain: list[ModelConfig] | None = None,
        temperature: float | None = None,
    ):
        self._chain = (
            build_default_chain() if model_chain is None else list(model_chain)
        )
        self._temperature = (
            temperature if temperature is not None else settings.llm_temperature
        )
        self._lock = threading.Lock()
        self._current_model: ModelConfig | None = None

    def _create_model(
        self, config: ModelConfig, temperature: float | None = None
    ) -> BaseChatModel:
        """Create a LangChain chat model from config using init_chat_model."""

        model_provider = _PROVIDER_MAP.get(config.provider)
        if not model_provider:
            raise ValueError(f"Unknown provider: {config.provider}")

        is_reasoning = config.reasoning or any(
            config.model.startswith(p) for p in _REASONING_PREFIXES
        )

        kwargs: dict[str, Any] = {"streaming": True}
        if not is_reasoning:
            effective_temperature = (
                temperature if temperature is not None else self._temperature
            )
            kwargs["temperature"] = effective_temperature
            kwargs["max_tokens"] = 4096

        kwargs.update(_build_provider_kwargs(config))

        try:
            return init_chat_model(
                model=config.model,
                model_provider=model_provider,
                **kwargs,
            )
        except Exception as e:
            raise type(e)(sanitize_error(str(e))) from e

    def get_available_models(self) -> list[ModelConfig]:
        """Get configured models for the current provider."""
        return list(self._chain)

    def get_model(
        self,
        temperature: float | None = None,
        chain: list[ModelConfig] | None = None,
    ) -> tuple[BaseChatModel, ModelConfig]:
        """Get the first available model by walking the chain."""
        effective_chain = chain or self._chain
        if not effective_chain:
            raise RuntimeError(
                "No LLM provider configured. Sign up for free tokens at "
                "https://fu7ur3pr00f.dev/signup, or set OPENAI_API_KEY, "
                "ANTHROPIC_API_KEY, or install Ollama for local models."
            )

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

    def get_status(self) -> dict[str, Any]:
        """Get current selection status."""
        return {
            "current_model": (
                self._current_model.description if self._current_model else None
            ),
            "available_models": [m.description for m in self.get_available_models()],
            "total_models": len(self._chain),
        }


_selection_manager: ModelSelectionManager | None = None
_manager_lock = threading.Lock()


def get_model_selection_manager() -> ModelSelectionManager:
    """Get the global model-selection manager instance."""
    global _selection_manager
    if _selection_manager is not None:
        return _selection_manager

    with _manager_lock:
        if _selection_manager is not None:
            return _selection_manager
        _selection_manager = ModelSelectionManager()
        return _selection_manager


def reset_model_selection_manager() -> None:
    """Reset the global model-selection manager after settings changes."""
    global _selection_manager
    _selection_manager = None


def _build_purpose_chain(
    model_name: str, provider: str, description: str
) -> list[ModelConfig]:
    """Build a provider model order with the purpose model first."""
    default_chain = build_default_chain()
    purpose_model = ModelConfig(provider, model_name, description)
    return [purpose_model] + [c for c in default_chain if c.model != model_name]


def get_model_for_purpose(
    purpose: str,
    temperature: float | None = None,
) -> tuple[BaseChatModel, ModelConfig]:
    """Get a model configured for a specific purpose."""
    purpose_map = {
        "agent": settings.agent_model,
        "analysis": settings.analysis_model,
        "summary": settings.summary_model,
        "synthesis": settings.synthesis_model,
    }

    azure_map = {
        "agent": settings.azure_agent_deployment,
        "analysis": settings.azure_analysis_deployment,
        "summary": settings.azure_summary_deployment,
        "synthesis": settings.azure_synthesis_deployment,
    }

    provider = settings.active_provider or "azure"
    model_name = purpose_map.get(purpose, "")
    if not model_name and provider == "azure":
        model_name = azure_map.get(purpose, "")
    if model_name:
        desc = f"{provider} {model_name}"
        chain = _build_purpose_chain(model_name, provider, desc)
    else:
        chain = None
    return get_model_selection_manager().get_model(
        temperature=temperature,
        chain=chain,
    )


def get_model(
    temperature: float | None = None,
    purpose: str | None = None,
) -> tuple[BaseChatModel, ModelConfig]:
    """Get the configured model for the active provider and optional purpose."""
    if purpose:
        return get_model_for_purpose(purpose, temperature)
    return get_model_selection_manager().get_model(temperature=temperature)
