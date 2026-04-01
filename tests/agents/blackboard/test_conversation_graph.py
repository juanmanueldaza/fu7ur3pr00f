"""Tests for outer conversation graph helpers."""

from fu7ur3pr00f.agents.blackboard.conversation_graph import _direct_profile_answer
from fu7ur3pr00f.agents.blackboard.turn_classifier import classify


class TestDirectProfileAnswer:
    def test_answers_identity_question_from_profile(self):
        profile = {
            "name": "Juan Manuel Daza",
            "current_role": "Full Stack AI Engineer",
            "location": "Buenos Aires, Argentina",
            "technical_skills": ["Python", "React", "Node.js"],
        }

        answer = _direct_profile_answer("you know who am I?", profile)

        assert answer is not None
        assert "Juan Manuel Daza" in answer
        assert "Full Stack AI Engineer" in answer
        assert "Buenos Aires, Argentina" in answer

    def test_returns_none_for_non_profile_question(self):
        profile = {"name": "Juan"}
        assert _direct_profile_answer("what jobs should I apply for?", profile) is None


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
