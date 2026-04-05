"""Tests for episodic memory tools."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from fu7ur3pr00f.agents.tools.memory import (
    get_memory_stats,
    recall_memories,
    remember_decision,
    remember_job_application,
)


class TestRememberDecision:
    """Test remember_decision tool."""

    def test_stores_decision_successfully(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.memory._store_to_episodic",
            return_value="Remembered: accepted job at Google.",
        ):
            result = remember_decision.invoke(
                {
                    "decision": "accepted job at Google",
                    "context": "Better compensation and growth",
                }
            )

        assert "Remembered" in result

    def test_stores_with_outcome(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.memory._store_to_episodic",
            return_value="Remembered: declined startup offer.",
        ):
            result = remember_decision.invoke(
                {
                    "decision": "declined startup offer",
                    "context": "Too risky",
                    "outcome": "Stayed at current company",
                }
            )

        assert "Remembered" in result


class TestRememberJobApplication:
    """Test remember_job_application tool."""

    def test_records_application_successfully(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.memory._store_to_episodic",
            return_value="Recorded application to Acme for Senior Dev.",
        ):
            result = remember_job_application.invoke(
                {
                    "company": "Acme",
                    "role": "Senior Dev",
                    "status": "applied",
                }
            )

        assert "Recorded" in result
        assert "Acme" in result

    def test_records_with_notes(self) -> None:
        with patch(
            "fu7ur3pr00f.agents.tools.memory._store_to_episodic",
            return_value="Recorded application to TechCorp.",
        ):
            result = remember_job_application.invoke(
                {
                    "company": "TechCorp",
                    "role": "Staff Engineer",
                    "status": "interviewing",
                    "notes": "Technical round next week",
                }
            )

        assert "Recorded" in result


class TestRecallMemories:
    """Test recall_memories tool."""

    def test_returns_memories_when_found(self) -> None:
        mock_memory = MagicMock()
        mock_memory.memory_type.value = "decision"
        mock_memory.timestamp = datetime(2024, 6, 15)
        mock_memory.content = "Accepted job at Google"
        mock_memory.context = "Better compensation"

        mock_store = MagicMock()
        mock_store.recall.return_value = [mock_memory]

        with patch(
            "fu7ur3pr00f.agents.tools.memory.get_episodic_store",
            return_value=mock_store,
        ):
            result = recall_memories.invoke({"query": "job decisions"})

        assert "Found 1 relevant memories" in result
        assert "Accepted job at Google" in result
        assert "2024-06-15" in result

    def test_returns_no_memories_when_empty(self) -> None:
        mock_store = MagicMock()
        mock_store.recall.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.memory.get_episodic_store",
            return_value=mock_store,
        ):
            result = recall_memories.invoke({"query": "nothing"})

        assert "No relevant memories found" in result

    def test_returns_no_memories_on_error(self) -> None:
        mock_store = MagicMock()
        mock_store.recall.side_effect = RuntimeError("DB error")

        with patch(
            "fu7ur3pr00f.agents.tools.memory.get_episodic_store",
            return_value=mock_store,
        ):
            result = recall_memories.invoke({"query": "anything"})

        assert "No relevant memories found" in result

    def test_respects_limit_parameter(self) -> None:
        mock_store = MagicMock()
        mock_store.recall.return_value = []

        with patch(
            "fu7ur3pr00f.agents.tools.memory.get_episodic_store",
            return_value=mock_store,
        ):
            recall_memories.invoke({"query": "test", "limit": 10})

        mock_store.recall.assert_called_once_with("test", limit=10)


class TestGetMemoryStats:
    """Test get_memory_stats tool."""

    def test_returns_stats(self) -> None:
        mock_store = MagicMock()
        mock_store.stats.return_value = {
            "total_memories": 25,
            "by_type": {
                "decision": 10,
                "application": 15,
                "conversation": 0,
            },
        }

        with patch(
            "fu7ur3pr00f.agents.tools.memory.get_episodic_store",
            return_value=mock_store,
        ):
            result = get_memory_stats.invoke({})

        assert "Total memories: 25" in result
        assert "decision: 10" in result
        assert "application: 15" in result
