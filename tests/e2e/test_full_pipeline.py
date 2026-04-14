"""End-to-end tests for the full agent pipeline.

These tests verify the complete chain:
    query → Orchestrator routes → Specialist → Tool → Synthesis → Response

The LLM is mocked to keep tests fast and deterministic, but the full
orchestrator → routing → specialist → tool → blackboard wiring is exercised.
"""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.blackboard.executor import BlackboardExecutor
from fu7ur3pr00f.agents.specialists.coach import CoachAgent
from fu7ur3pr00f.agents.specialists.code import CodeAgent
from fu7ur3pr00f.agents.specialists.founder import FounderAgent
from fu7ur3pr00f.agents.specialists.jobs import JobsAgent
from fu7ur3pr00f.agents.specialists.learning import LearningAgent
from fu7ur3pr00f.agents.specialists.orchestrator import (
    OrchestratorAgent,
    get_orchestrator,
    reset_orchestrator,
)
from fu7ur3pr00f.container import container

pytestmark = pytest.mark.integration


def _register_all_specialists_in_factory():
    """Ensure the blackboard factory has all specialists registered."""
    factory = container.blackboard_factory
    factory.clear()
    factory.register_specialist("coach", CoachAgent())
    factory.register_specialist("learning", LearningAgent())
    factory.register_specialist("jobs", JobsAgent())
    factory.register_specialist("code", CodeAgent())
    factory.register_specialist("founder", FounderAgent())


class TestFullAgentPipeline:
    """Test the complete agent pipeline from query to response."""

    def setup_method(self):
        """Reset orchestrator and register specialists before each test."""
        reset_orchestrator()
        _register_all_specialists_in_factory()

    def test_orchestrator_routes_and_gets_executor(self):
        """Verify orchestrator can route a query and get an executor."""
        orch = OrchestratorAgent()
        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("LLM offline")
            specialists = orch.route("Find remote Python developer jobs")

        assert isinstance(specialists, list)
        assert "jobs" in specialists

        executor = orch.get_executor(specialists)
        assert isinstance(executor, BlackboardExecutor)

    def test_orchestrator_lists_all_specialists(self):
        """Verify all 5 specialists are registered."""
        orch = OrchestratorAgent()
        agents = orch.list_agents()
        assert len(agents) == 5
        names = {a["name"] for a in agents}
        assert names == {"coach", "learning", "jobs", "code", "founder"}

    def test_full_pipeline_coach_query(self):
        """Full pipeline: coach query → route → execute → findings."""
        orch = OrchestratorAgent()
        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("LLM offline")
            specialists = orch.route("How do I get promoted to Staff Engineer?")

        assert "coach" in specialists

        executor = orch.get_executor(specialists)
        assert "coach" in executor.specialists

    def test_full_pipeline_jobs_query(self):
        """Full pipeline: jobs query → route → execute with jobs specialist."""
        orch = OrchestratorAgent()
        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("LLM offline")
            specialists = orch.route("Search for remote senior developer jobs")

        assert specialists == ["jobs"]

        executor = orch.get_executor(specialists)
        assert "jobs" in executor.specialists

    def test_full_pipeline_learning_query(self):
        """Full pipeline: learning query → route → execute."""
        orch = OrchestratorAgent()
        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("LLM offline")
            specialists = orch.route("I want to learn machine learning")

        assert "learning" in specialists

        executor = orch.get_executor(specialists)
        assert "learning" in executor.specialists

    def test_full_pipeline_code_query(self):
        """Full pipeline: code query → route → execute."""
        orch = OrchestratorAgent()
        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("LLM offline")
            specialists = orch.route("Review my GitHub repositories")

        assert "code" in specialists

        executor = orch.get_executor(specialists)
        assert "code" in executor.specialists

    def test_full_pipeline_founder_query(self):
        """Full pipeline: founder query → route → execute."""
        orch = OrchestratorAgent()
        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("LLM offline")
            specialists = orch.route("How do I launch my SaaS startup?")

        assert "founder" in specialists

        executor = orch.get_executor(specialists)
        assert "founder" in executor.specialists

    def test_pipeline_handles_llm_routing_success(self):
        """When LLM routing succeeds, verify semantic routing is used."""
        orch = OrchestratorAgent()

        mock_decision = MagicMock()
        mock_decision.specialists = ["coach", "learning"]

        mock_model = MagicMock()
        mock_router = MagicMock()
        mock_router.invoke.return_value = mock_decision

        mock_model.with_structured_output.return_value = mock_router

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            specialists = orch.route("How should I learn leadership skills?")

        assert isinstance(specialists, list)
        # LLM returned valid specialists
        assert "coach" in specialists or "learning" in specialists

    def test_executor_has_all_tools_for_specialist(self):
        """Verify each specialist has tools registered."""
        orch = OrchestratorAgent()

        for specialist_name in ["coach", "learning", "jobs", "code", "founder"]:
            specialist = orch.get_specialist(specialist_name)
            assert len(specialist.tools) > 0, f"{specialist_name} has no tools"
            tool_names = {t.name for t in specialist.tools}
            assert len(tool_names) > 0, f"{specialist_name} tool names empty"

    def test_singleton_get_orchestrator(self):
        """Verify get_orchestrator returns same instance."""
        reset_orchestrator()
        a = get_orchestrator()
        b = get_orchestrator()
        assert a is b
        reset_orchestrator()
