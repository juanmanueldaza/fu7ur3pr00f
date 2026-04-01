"""Tests for multi-provider model selection."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.llm.model_selection import (
    ModelConfig,
    ModelSelectionManager,
    _build_provider_kwargs,
    build_default_chain,
    get_model,
    get_model_selection_manager,
    reset_model_selection_manager,
)


class TestBuildDefaultChain:
    """Test dynamic model-chain construction."""

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_openai_chain(self, mock_settings) -> None:
        mock_settings.active_provider = "openai"
        chain = build_default_chain()
        assert len(chain) > 0
        assert all(c.provider == "openai" for c in chain)

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_anthropic_chain(self, mock_settings) -> None:
        mock_settings.active_provider = "anthropic"
        chain = build_default_chain()
        assert len(chain) > 0
        assert all(c.provider == "anthropic" for c in chain)

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_unknown_provider_returns_empty(self, mock_settings) -> None:
        mock_settings.active_provider = "unknown"
        assert build_default_chain() == []

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_empty_provider_returns_empty(self, mock_settings) -> None:
        mock_settings.active_provider = ""
        assert build_default_chain() == []


class TestBuildProviderKwargs:
    """Test provider-specific kwargs for init_chat_model."""

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_azure_kwargs(self, mock_settings) -> None:
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_api_version = "2024-12-01-preview"
        mock_settings.azure_openai_api_key = "az-key"
        config = ModelConfig("azure", "gpt-4.1", "Azure GPT-4.1")
        kwargs = _build_provider_kwargs(config)
        assert kwargs["azure_deployment"] == "gpt-4.1"
        assert kwargs["azure_endpoint"] == "https://test.openai.azure.com/"
        assert kwargs["api_key"] == "az-key"

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_openai_kwargs(self, mock_settings) -> None:
        mock_settings.openai_api_key = "sk-test"
        config = ModelConfig("openai", "gpt-4.1", "OpenAI GPT-4.1")
        kwargs = _build_provider_kwargs(config)
        assert kwargs["api_key"] == "sk-test"
        assert "base_url" not in kwargs

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_fu7ur3pr00f_proxy_kwargs(self, mock_settings) -> None:
        mock_settings.fu7ur3pr00f_proxy_key = "fp-key"
        mock_settings.fu7ur3pr00f_proxy_url = "https://llm.fu7ur3pr00f.dev"
        config = ModelConfig("fu7ur3pr00f", "gpt-4.1", "FP GPT-4.1")
        kwargs = _build_provider_kwargs(config)
        assert kwargs["api_key"] == "fp-key"
        assert kwargs["base_url"] == "https://llm.fu7ur3pr00f.dev"

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_anthropic_kwargs(self, mock_settings) -> None:
        mock_settings.anthropic_api_key = "sk-ant-test"
        config = ModelConfig("anthropic", "claude-sonnet-4-20250514", "Claude")
        kwargs = _build_provider_kwargs(config)
        assert kwargs["api_key"] == "sk-ant-test"

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_google_kwargs(self, mock_settings) -> None:
        mock_settings.google_api_key = "AIza-test"
        config = ModelConfig("google", "gemini-2.5-flash", "Gemini")
        kwargs = _build_provider_kwargs(config)
        assert kwargs["google_api_key"] == "AIza-test"

    @patch("fu7ur3pr00f.llm.model_selection.settings")
    def test_ollama_kwargs(self, mock_settings) -> None:
        mock_settings.ollama_base_url = "http://localhost:11434"
        config = ModelConfig("ollama", "qwen3", "Ollama Qwen3")
        kwargs = _build_provider_kwargs(config)
        assert kwargs["base_url"] == "http://localhost:11434"


class TestModelSelectionManager:
    """Test ModelSelectionManager behavior."""

    def test_returns_first_model(self) -> None:
        chain = [
            ModelConfig("openai", "gpt-4.1", "GPT-4.1"),
            ModelConfig("openai", "gpt-4o", "GPT-4o"),
        ]
        manager = ModelSelectionManager(model_chain=chain)
        with patch.object(manager, "_create_model") as mock_create:
            mock_create.return_value = MagicMock()
            _model, config = manager.get_model()
        assert config.model == "gpt-4.1"

    def test_empty_chain_raises(self) -> None:
        manager = ModelSelectionManager(model_chain=[])
        try:
            manager.get_model()
        except RuntimeError as exc:
            assert "No LLM provider configured" in str(exc)
        else:
            raise AssertionError("Expected RuntimeError")

    def test_get_status(self) -> None:
        chain = [
            ModelConfig("openai", "gpt-4.1", "GPT-4.1"),
            ModelConfig("openai", "gpt-4o", "GPT-4o"),
        ]
        manager = ModelSelectionManager(model_chain=chain)
        status = manager.get_status()
        assert status["total_models"] == 2
        assert len(status["available_models"]) == 2
        assert status["current_model"] is None


class TestModelConfigDataclass:
    """Test ModelConfig dataclass defaults."""

    def test_reasoning_defaults_false(self) -> None:
        config = ModelConfig("openai", "gpt-4", "GPT-4")
        assert config.reasoning is False

    def test_reasoning_can_be_set(self) -> None:
        config = ModelConfig("openai", "o4-mini", "O4 Mini", reasoning=True)
        assert config.reasoning is True


class TestCreateModel:
    """Test _create_model method."""

    def test_rejects_unknown_provider(self) -> None:
        chain = [ModelConfig("unknown", "model", "Unknown")]
        manager = ModelSelectionManager(model_chain=chain)
        with pytest.raises(ValueError, match="Unknown provider"):
            manager._create_model(chain[0])

    def test_skips_temperature_for_reasoning_models(self) -> None:
        mock_init = MagicMock()
        chain = [ModelConfig("openai", "o4-mini", "O4 Mini", reasoning=True)]

        with patch(
            "fu7ur3pr00f.llm.model_selection.init_chat_model",
            mock_init,
        ):
            manager = ModelSelectionManager(model_chain=chain)
            manager._create_model(chain[0])

        call_kwargs = mock_init.call_args.kwargs
        assert "temperature" not in call_kwargs
        assert "max_tokens" not in call_kwargs

    def test_skips_temperature_for_o_prefix_models(self) -> None:
        mock_init = MagicMock()
        chain = [ModelConfig("openai", "o3-mini", "O3 Mini")]

        with patch(
            "fu7ur3pr00f.llm.model_selection.init_chat_model",
            mock_init,
        ):
            manager = ModelSelectionManager(model_chain=chain)
            manager._create_model(chain[0])

        call_kwargs = mock_init.call_args.kwargs
        assert "temperature" not in call_kwargs

    def test_includes_temperature_for_non_reasoning_models(self) -> None:
        mock_init = MagicMock()
        chain = [ModelConfig("openai", "gpt-4", "GPT-4")]

        with patch(
            "fu7ur3pr00f.llm.model_selection.init_chat_model",
            mock_init,
        ):
            manager = ModelSelectionManager(model_chain=chain)
            manager._create_model(chain[0], temperature=0.5)

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 4096


class TestGlobalManager:
    """Test global singleton functions."""

    def test_get_manager_returns_instance(self) -> None:
        reset_model_selection_manager()
        manager = get_model_selection_manager()
        assert isinstance(manager, ModelSelectionManager)

    def test_get_manager_returns_same_instance(self) -> None:
        reset_model_selection_manager()
        m1 = get_model_selection_manager()
        m2 = get_model_selection_manager()
        assert m1 is m2

    def test_reset_clears_instance(self) -> None:
        reset_model_selection_manager()
        m1 = get_model_selection_manager()
        reset_model_selection_manager()
        m2 = get_model_selection_manager()
        assert m1 is not m2


class TestGetModel:
    """Test get_model convenience function."""

    def test_without_purpose(self) -> None:
        mock_model = MagicMock()
        mock_config = ModelConfig("openai", "gpt-4", "GPT-4")

        with patch(
            "fu7ur3pr00f.llm.model_selection.get_model_selection_manager"
        ) as mock_mgr:
            mock_mgr.return_value.get_model.return_value = (
                mock_model,
                mock_config,
            )
            model, config = get_model()

        assert model is mock_model
        assert config is mock_config

    def test_with_purpose(self) -> None:
        mock_model = MagicMock()
        mock_config = ModelConfig("openai", "gpt-4", "GPT-4")

        with patch(
            "fu7ur3pr00f.llm.model_selection.get_model_for_purpose"
        ) as mock_purpose:
            mock_purpose.return_value = (mock_model, mock_config)
            model, config = get_model(purpose="agent")

        assert model is mock_model
        mock_purpose.assert_called_once_with("agent", None)
