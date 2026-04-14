"""Integration tests for blackboard specialist contribution flow."""

from typing import Any
from unittest.mock import patch

from fu7ur3pr00f.agents.blackboard.blackboard import CareerBlackboard, SpecialistFinding
from fu7ur3pr00f.agents.specialists.coach import CoachAgent
from fu7ur3pr00f.container import container


class TestBlackboardIntegration:
    """Test the full blackboard contribution flow."""

    def _create_blackboard(
        self,
        query: str = "How can I get promoted to Staff Engineer?",
        profile: dict[str, Any] | None = None,
        findings: dict[str, SpecialistFinding] | None = None,
    ) -> CareerBlackboard:
        """Create a blackboard with default test data."""
        if profile is None:
            profile = {
                "name": "Test User",
                "current_role": "Senior Engineer",
                "years_experience": 5,
                "technical_skills": ["Python", "Go", "React"],
            }
        if findings is None:
            findings = {}
        bb: CareerBlackboard = {}
        bb["query"] = query
        bb["user_profile"] = profile
        bb["findings"] = findings
        return bb

    def test_finding_returns_error_on_setup_failure(self) -> None:
        """Verify graceful error when get_model fails."""
        agent = CoachAgent()
        blackboard = self._create_blackboard()

        with patch.object(
            container,
            "get_model",
            side_effect=RuntimeError("No API key configured"),
        ):
            finding = agent.contribute(blackboard)

        assert "Setup error" in finding.get("reasoning", "")
        assert finding.get("confidence") == 0.0

    def test_blackboard_query_is_passed_to_context(self) -> None:
        """Verify blackboard query appears in the built context."""
        agent = CoachAgent()
        blackboard = self._create_blackboard(
            query="How can I improve my Python skills?",
            profile={
                "name": "Jane Doe",
                "current_role": "Developer",
                "technical_skills": ["Python", "JavaScript"],
            },
        )

        context = agent._build_context(blackboard)
        assert "How can I improve my Python skills" in context
        assert "Jane Doe" in context

    def test_previous_findings_format(self) -> None:
        """Verify that previous findings from other specialists are formatted."""
        agent = CoachAgent()
        blackboard = self._create_blackboard()
        blackboard["findings"] = {
            "jobs": SpecialistFinding(
                reasoning="Strong job market for your skills",
                confidence=0.85,
            )
        }

        context = agent._build_context(blackboard)
        assert "jobs" in context.lower()

    def test_profile_skills_in_context(self) -> None:
        """Verify profile technical skills appear in context."""
        agent = CoachAgent()
        blackboard = self._create_blackboard(
            profile={
                "name": "Test User",
                "technical_skills": ["Python", "Rust"],
            }
        )

        context = agent._build_context(blackboard)
        assert "Python" in context
        assert "Rust" in context

    def test_constraints_are_included(self) -> None:
        """Verify cross-turn context from constraints is included."""
        agent = CoachAgent()
        blackboard = self._create_blackboard()
        blackboard["constraints"] = ["PRIOR_TURNS:User previously asked about ML"]

        context = agent._build_context(blackboard)
        assert "User previously asked about ML" in context


class TestBlackboardCreation:
    """Test blackboard creation and manipulation."""

    def test_creates_empty_blackboard(self) -> None:
        bb: CareerBlackboard = {}
        bb["query"] = "test query"
        bb["user_profile"] = {}
        bb["findings"] = {}
        assert bb["query"] == "test query"

    def test_blackboard_supports_arbitrary_keys(self) -> None:
        bb: CareerBlackboard = {}
        bb["query"] = "test"
        bb["_tool_cache"] = {}
        bb["_kb_context"] = "test context"
        assert bb["_tool_cache"] == {}
        assert bb["_kb_context"] == "test context"

    def test_specialist_finding_structure(self) -> None:
        finding: SpecialistFinding = {
            "reasoning": "Focus on leadership skills",
            "confidence": 0.85,
            "gaps": ["public speaking", "team management"],
            "action_items": ["take a leadership course"],
        }
        assert finding["reasoning"] == "Focus on leadership skills"
        assert finding["confidence"] == 0.85
        assert "public speaking" in finding["gaps"]
