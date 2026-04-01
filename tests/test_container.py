"""Tests for the Dependency Injection Container."""

from unittest.mock import MagicMock, patch

from fu7ur3pr00f.container import Container


class TestContainer:
    """Test Container singleton and service access."""

    def test_singleton_instance(self):
        """Container.get() returns the same instance."""
        c1 = Container.get()
        c2 = Container.get()
        assert c1 is c2

    def test_reset_creates_new_instance(self):
        """Container.reset() clears singleton, next get() returns new instance."""
        c1 = Container.get()
        Container.reset()
        c2 = Container.get()
        assert c1 is not c2

    def test_settings_access(self):
        """Container.settings returns Settings instance."""
        container = Container.get()
        settings = container.settings
        assert settings is not None
        # Verify it's the same as module-level settings
        from fu7ur3pr00f.config import settings as module_settings

        assert settings is module_settings

    @patch("fu7ur3pr00f.llm.model_selection.ModelSelectionManager")
    def test_model_manager_lazy_init(self, mock_manager_cls):
        """Model manager is lazily initialized."""
        mock_manager = MagicMock()
        mock_manager_cls.return_value = mock_manager

        container = Container.get()
        # Reset cached service
        container._model_manager = None

        manager = container.model_manager
        assert manager is mock_manager
        mock_manager_cls.assert_called_once()

    @patch("fu7ur3pr00f.services.knowledge_service.KnowledgeService")
    def test_knowledge_service_lazy_init(self, mock_service_cls):
        """Knowledge service is lazily initialized."""
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        container = Container.get()
        container._knowledge_service = None

        service = container.knowledge_service
        assert service is mock_service
        mock_service_cls.assert_called_once()

    @patch("fu7ur3pr00f.memory.profile.load_profile")
    def test_profile_lazy_init(self, mock_load):
        """Profile is lazily loaded."""
        mock_profile = MagicMock()
        mock_load.return_value = mock_profile

        container = Container.get()
        container._profile = None

        profile = container.profile
        assert profile is mock_profile
        mock_load.assert_called_once()

    @patch("fu7ur3pr00f.llm.model_selection.get_model")
    def test_get_model_convenience(self, mock_get_model):
        """get_model() delegates to module function."""
        mock_get_model.return_value = (MagicMock(), MagicMock())

        container = Container.get()
        result = container.get_model(temperature=0.5, purpose="agent")

        mock_get_model.assert_called_once_with(temperature=0.5, purpose="agent")
        assert result == mock_get_model.return_value

    def test_reset_services(self):
        """reset_services() clears cached services."""
        container = Container.get()
        # Populate caches
        _ = container.model_manager
        _ = container.knowledge_service
        _ = container.profile

        container.reset_services()

        assert container._model_manager is None
        assert container._knowledge_service is None
        assert container._profile is None

    @patch("fu7ur3pr00f.memory.profile.load_profile")
    def test_reload_profile(self, mock_load):
        """reload_profile() updates cached profile."""
        mock_profile1 = MagicMock()
        mock_profile2 = MagicMock()
        mock_load.side_effect = [mock_profile1, mock_profile2]

        container = Container.get()
        container._profile = None

        profile1 = container.profile
        assert profile1 is mock_profile1

        profile2 = container.reload_profile()
        assert profile2 is mock_profile2
        assert container._profile is mock_profile2
        assert mock_load.call_count == 2
