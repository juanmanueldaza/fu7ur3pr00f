"""Tests for settings management tools."""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.tools.settings import get_current_config, update_setting

pytestmark = pytest.mark.unit


class TestGetCurrentConfig:
    """Test get_current_config tool."""

    def test_returns_config_summary(self) -> None:
        mock_settings = MagicMock()
        mock_settings.active_provider = "openai"
        mock_settings.has_proxy = False
        mock_settings.has_azure = False
        mock_settings.has_openai = True
        mock_settings.has_anthropic = False
        mock_settings.has_google = False
        mock_settings.has_ollama = False
        mock_settings.agent_model = ""
        mock_settings.analysis_model = "gpt-4.1"
        mock_settings.summary_model = ""
        mock_settings.synthesis_model = ""
        mock_settings.embedding_model = ""
        mock_settings.llm_temperature = 0.3
        mock_settings.cv_temperature = 0.2
        mock_settings.jobspy_enabled = True
        mock_settings.hn_mcp_enabled = True
        mock_settings.has_github_mcp = False
        mock_settings.has_tavily_mcp = False
        mock_settings.market_cache_hours = 24
        mock_settings.job_cache_hours = 12
        mock_settings.content_cache_hours = 12
        mock_settings.forex_cache_hours = 4
        mock_settings.knowledge_auto_index = True
        mock_settings.knowledge_chunk_max_tokens = 500
        mock_settings.knowledge_chunk_min_tokens = 50

        with patch("fu7ur3pr00f.agents.tools.settings.settings", mock_settings):
            result = get_current_config.invoke({})

        assert "Active LLM provider: openai" in result
        assert "Configured providers: openai" in result
        assert "llm_temperature: 0.3" in result
        assert "jobspy_enabled: True" in result

    def test_shows_no_provider_when_none_configured(self) -> None:
        mock_settings = MagicMock()
        mock_settings.active_provider = ""
        mock_settings.has_proxy = False
        mock_settings.has_azure = False
        mock_settings.has_openai = False
        mock_settings.has_anthropic = False
        mock_settings.has_google = False
        mock_settings.has_ollama = False
        mock_settings.has_github_mcp = False
        mock_settings.has_tavily_mcp = False
        mock_settings.agent_model = ""
        mock_settings.analysis_model = ""
        mock_settings.summary_model = ""
        mock_settings.synthesis_model = ""
        mock_settings.embedding_model = ""
        mock_settings.llm_temperature = 0.3
        mock_settings.cv_temperature = 0.2
        mock_settings.jobspy_enabled = True
        mock_settings.hn_mcp_enabled = True
        mock_settings.market_cache_hours = 24
        mock_settings.job_cache_hours = 12
        mock_settings.content_cache_hours = 12
        mock_settings.forex_cache_hours = 4
        mock_settings.knowledge_auto_index = True
        mock_settings.knowledge_chunk_max_tokens = 500
        mock_settings.knowledge_chunk_min_tokens = 50

        with patch("fu7ur3pr00f.agents.tools.settings.settings", mock_settings):
            result = get_current_config.invoke({})

        assert "Active LLM provider: none" in result
        assert "Configured providers: none" in result


class TestUpdateSetting:
    """Test update_setting tool."""

    def test_rejects_sensitive_key(self) -> None:
        result = update_setting.invoke({"key": "openai_api_key", "value": "sk-123"})

        assert "sensitive setting" in result
        assert "/setup" in result

    def test_rejects_unknown_key(self) -> None:
        result = update_setting.invoke({"key": "unknown_setting", "value": "test"})

        assert "Unknown setting" in result

    def test_validates_temperature_range(self) -> None:
        result = update_setting.invoke({"key": "llm_temperature", "value": "5.0"})

        assert "must be between 0.0 and 2.0" in result

    def test_validates_cache_hours_minimum(self) -> None:
        result = update_setting.invoke({"key": "market_cache_hours", "value": "0"})

        assert "must be >= 1" in result

    def test_validates_boolean_values(self) -> None:
        result = update_setting.invoke({"key": "jobspy_enabled", "value": "maybe"})

        assert "must be true or false" in result

    def test_validates_provider_value(self) -> None:
        result = update_setting.invoke(
            {"key": "llm_provider", "value": "unknown_provider"}
        )

        assert "Unknown provider" in result

    def test_updates_valid_setting(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.settings.write_user_setting"
        ) as mock_write:
            with patch(
                "fu7ur3pr00f.agents.tools.settings.reload_settings"
            ) as mock_reload:
                result = update_setting.invoke(
                    {"key": "llm_temperature", "value": "0.5"}
                )

        assert "Updated llm_temperature = 0.5" in result
        mock_write.assert_called_once_with("LLM_TEMPERATURE", "0.5")
        mock_reload.assert_called_once()

    def test_triggers_restart_for_model_keys(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.settings.write_user_setting"):
            with patch("fu7ur3pr00f.agents.tools.settings.reload_settings"):
                with patch(
                    "fu7ur3pr00f.agents.specialists.orchestrator.reset_orchestrator"
                ) as mock_reset_orch:
                    with patch(
                        "fu7ur3pr00f.llm.model_selection.reset_model_selection_manager"
                    ) as mock_reset_model:
                        result = update_setting.invoke(
                            {"key": "agent_model", "value": "gpt-5-mini"}
                        )

        assert "next message" in result
        mock_reset_model.assert_called_once()
        mock_reset_orch.assert_called_once()

    def test_accepts_valid_boolean_true(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.settings.write_user_setting"):
            with patch("fu7ur3pr00f.agents.tools.settings.reload_settings"):
                result = update_setting.invoke(
                    {"key": "jobspy_enabled", "value": "true"}
                )

        assert "Updated jobspy_enabled = true" in result

    def test_accepts_valid_boolean_yes(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.settings.write_user_setting"):
            with patch("fu7ur3pr00f.agents.tools.settings.reload_settings"):
                result = update_setting.invoke(
                    {"key": "hn_mcp_enabled", "value": "yes"}
                )

        assert "Updated hn_mcp_enabled = yes" in result

    def test_accepts_valid_provider(self) -> None:
        with patch("fu7ur3pr00f.agents.tools.settings.write_user_setting"):
            with patch("fu7ur3pr00f.agents.tools.settings.reload_settings"):
                with patch(
                    "fu7ur3pr00f.llm.model_selection.reset_model_selection_manager"
                ):
                    with patch(
                        "fu7ur3pr00f.agents.specialists.orchestrator.reset_orchestrator"
                    ):
                        result = update_setting.invoke(
                            {"key": "llm_provider", "value": "anthropic"}
                        )

        assert "Updated llm_provider = anthropic" in result
