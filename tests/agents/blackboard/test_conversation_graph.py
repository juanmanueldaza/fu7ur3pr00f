"""Tests for outer conversation graph helpers."""

from unittest.mock import MagicMock, patch

from fu7ur3pr00f.agents.blackboard.conversation_graph import suggest_next_node
from fu7ur3pr00f.agents.blackboard.turn_classifier import classify


class TestTurnClassifierHeuristics:
    def test_classifies_identity_question_as_factual_without_history(self):
        result = classify(
            "you know who am I?", conversation_history=None, active_goals=None
        )
        assert result == "factual"

    def test_classifies_role_question_as_factual_without_history(self):
        result = classify(
            "what is my current role?", conversation_history=None, active_goals=None
        )
        assert result == "factual"


_STATE_WITH_FINDINGS = {
    "turn_type": "new_query",
    "current_blackboard": {
        "query": "what should I do next?",
        "findings": {
            "coach": {
                "reasoning": "You have strong Python skills.",
                "action_items": ["Update LinkedIn profile", "Apply to senior roles"],
                "gaps": ["Missing cloud certifications"],
                "open_questions": ["Are you open to relocating?"],
            }
        },
    },
}


class TestFactualQueryReachesCoach:
    def test_factual_query_reaches_coach(self):
        """Factual query must reach executor (not short-circuited by deleted bypass)."""
        from langgraph.checkpoint.memory import MemorySaver

        from fu7ur3pr00f.agents.blackboard.conversation_graph import (
            build_conversation_graph,
        )
        from fu7ur3pr00f.agents.blackboard.session import make_initial_session

        on_specialist_start = MagicMock()

        # Mock executor that captures the on_specialist_start callback
        mock_executor = MagicMock()

        def fake_execute(**kwargs):
            kwargs["on_specialist_start"]("coach")
            return {
                "query": "who am i?",
                "findings": {"coach": {"reasoning": "You are Juan", "confidence": 1.0}},
                "synthesis": {"narrative": "You are Juan"},
                "errors": [],
            }

        mock_executor.execute.side_effect = fake_execute
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_executor.return_value = mock_executor

        with (
            patch(
                "fu7ur3pr00f.agents.specialists.orchestrator.get_orchestrator",
                return_value=mock_orchestrator,
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.get_model",
                side_effect=RuntimeError("no LLM in test"),
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.load_prompt",
                return_value=(
                    "{query}{findings_text}{gaps}"
                    "{action_items}{open_questions}{profile_status}"
                ),
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.load_profile",
                return_value=MagicMock(name=""),
            ),
        ):
            callbacks = {"on_specialist_start": on_specialist_start}
            graph = build_conversation_graph(
                checkpointer=MemorySaver(),
                callbacks=callbacks,
            )
            session_state = make_initial_session({"name": "Juan"})
            session_state["current_query"] = "who am i?"
            config = {"configurable": {"thread_id": "test-factual"}}
            graph.invoke(session_state, config)  # type: ignore[arg-type]

        on_specialist_start.assert_called_with("coach")


class TestSuggestNextNode:
    def test_suggest_next_returns_empty_on_llm_failure(self):
        with (
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.get_model",
                side_effect=RuntimeError("no model"),
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.load_prompt",
                return_value=(
                    "{query}{findings_text}{gaps}"
                    "{action_items}{open_questions}{profile_status}"
                ),
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.load_profile",
                return_value=MagicMock(name=""),
            ),
        ):
            result = suggest_next_node(_STATE_WITH_FINDINGS)

        assert result["suggested_next"] == []

    def test_suggest_next_returns_suggestions_on_success(self):
        mock_response = MagicMock()
        mock_response.content = (
            "- Update your LinkedIn\n- Apply to senior roles\n- Get AWS cert"
        )
        mock_model = MagicMock()
        mock_model.invoke.return_value = mock_response

        with (
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.get_model",
                return_value=(mock_model, MagicMock()),
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.load_prompt",
                return_value=(
                    "{query}{findings_text}{gaps}"
                    "{action_items}{open_questions}{profile_status}"
                ),
            ),
            patch(
                "fu7ur3pr00f.agents.blackboard.conversation_graph.load_profile",
                return_value=MagicMock(name="Juan"),
            ),
        ):
            result = suggest_next_node(_STATE_WITH_FINDINGS)

        assert len(result["suggested_next"]) > 0
        assert all(isinstance(s, str) for s in result["suggested_next"])
