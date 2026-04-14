"""Integration wiring tests — blackboard → specialist → tool → blackboard round-trip.

These tests verify that the full blackboard contribution flow works:
1. Blackboard is created with a query and user profile
2. Specialist reads blackboard, builds context, contributes a finding
3. Finding is recorded back into the blackboard
4. Subsequent specialists can read previous findings
"""

from unittest.mock import MagicMock, patch

import pytest

from fu7ur3pr00f.agents.blackboard.blackboard import (
    get_previous_findings,
    get_specialist_finding,
    make_initial_blackboard,
    record_specialist_contribution,
)
from fu7ur3pr00f.agents.specialists.coach import CoachAgent
from fu7ur3pr00f.agents.specialists.code import CodeAgent
from fu7ur3pr00f.agents.specialists.jobs import JobsAgent
from fu7ur3pr00f.agents.specialists.learning import LearningAgent

pytestmark = pytest.mark.integration


class TestBlackboardSpecialistRoundTrip:
    """Test full round-trip: blackboard → specialist → finding → blackboard."""

    def _mock_agent_contribute(
        self, agent, blackboard, reasoning="Test finding.", confidence=0.8
    ):
        """Mock the LLM and return a structured finding."""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.tool_calls = []
        mock_response.content = reasoning
        mock_model.bind_tools.return_value = mock_model
        mock_model.invoke.return_value = mock_response

        mock_extractor = MagicMock()
        mock_finding = MagicMock()
        mock_finding.model_dump.return_value = {
            "reasoning": reasoning,
            "confidence": confidence,
            "gaps": ["ML"],
            "skills": ["Python"],
        }
        mock_extractor.invoke.return_value = mock_finding

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_get_model:
            mock_get_model.return_value = (mock_model, MagicMock())
            mock_model.with_structured_output.return_value = mock_extractor
            return agent.contribute(blackboard)

    def test_coach_finding_recorded_and_readable(self):
        """Coach contributes, finding is recorded and retrievable."""
        blackboard = make_initial_blackboard(
            query="How do I get promoted to Staff?",
            user_profile={
                "name": "Test User",
                "current_role": "Senior Engineer",
                "technical_skills": ["Python"],
            },
        )

        agent = CoachAgent()
        finding = self._mock_agent_contribute(agent, blackboard)

        record_specialist_contribution(blackboard, "coach", finding, confidence=0.8)

        retrieved = get_specialist_finding(blackboard, "coach")
        assert retrieved is not None
        assert retrieved["reasoning"] == "Test finding."
        assert retrieved["confidence"] == 0.8

    def test_learning_reads_coach_finding(self):
        """Learning specialist can read coach's gaps and build on them."""
        blackboard = make_initial_blackboard(
            query="How should I learn ML?",
            user_profile={"name": "Test User", "technical_skills": ["Python"]},
        )

        # Coach contributes first
        coach = CoachAgent()
        coach_finding = self._mock_agent_contribute(
            coach,
            blackboard,
            reasoning="Focus on ML fundamentals and leadership.",
            confidence=0.85,
        )
        record_specialist_contribution(blackboard, "coach", coach_finding, 0.85)

        # Learning reads coach's finding in context
        learning = LearningAgent()
        context = learning._build_context(blackboard)
        assert "coach" in context.lower()

    def test_multi_specialist_chain(self):
        """Full chain: coach → learning → code → all findings accumulate."""
        blackboard = make_initial_blackboard(
            query="Career growth plan for ML engineer",
            user_profile={
                "name": "Test User",
                "current_role": "Junior Engineer",
                "technical_skills": ["Python"],
            },
        )

        # Coach identifies gaps
        coach = CoachAgent()
        coach_finding = self._mock_agent_contribute(
            coach,
            blackboard,
            reasoning="Need ML skills and leadership experience.",
            confidence=0.85,
        )
        record_specialist_contribution(blackboard, "coach", coach_finding, 0.85)

        # Learning suggests skills
        learning = LearningAgent()
        learning_finding = self._mock_agent_contribute(
            learning,
            blackboard,
            reasoning="Study ML fundamentals and take leadership course.",
            confidence=0.80,
        )
        record_specialist_contribution(blackboard, "learning", learning_finding, 0.80)

        # Code suggests portfolio projects
        code = CodeAgent()
        code_finding = self._mock_agent_contribute(
            code,
            blackboard,
            reasoning="Build an ML project to demonstrate skills.",
            confidence=0.82,
        )
        record_specialist_contribution(blackboard, "code", code_finding, 0.82)

        # Verify all 3 findings accumulated
        assert len(blackboard["findings"]) == 3
        assert "coach" in blackboard["findings"]
        assert "learning" in blackboard["findings"]
        assert "code" in blackboard["findings"]

        # Verify change log has 3 entries
        assert len(blackboard["change_log"]) == 3

        # Code can read all previous findings
        previous = get_previous_findings(blackboard, exclude_specialist="code")
        assert "coach" in previous
        assert "learning" in previous
        assert "code" not in previous

    def test_jobs_finding_with_market_data(self):
        """Jobs specialist contributes market analysis finding."""
        blackboard = make_initial_blackboard(
            query="Find remote Python jobs",
            user_profile={
                "name": "Test User",
                "current_role": "Python Developer",
                "technical_skills": ["Python", "Django"],
            },
        )

        agent = JobsAgent()
        finding = self._mock_agent_contribute(
            agent,
            blackboard,
            reasoning="Strong demand for Python developers in remote market.",
            confidence=0.78,
        )

        record_specialist_contribution(blackboard, "jobs", finding, 0.78)
        retrieved = get_specialist_finding(blackboard, "jobs")
        assert retrieved is not None
        assert "Strong demand" in retrieved["reasoning"]


class TestBlackboardErrorHandling:
    """Test blackboard handles errors gracefully."""

    def test_contribute_returns_error_on_llm_failure(self):
        """When get_model fails, contribute() should return error finding."""
        agent = CoachAgent()
        blackboard = make_initial_blackboard(
            query="Help me",
            user_profile={"name": "Test User"},
        )

        with patch("fu7ur3pr00f.llm.model_selection.get_model") as mock_model:
            mock_model.side_effect = RuntimeError("No API key configured")
            finding = agent.contribute(blackboard)

        assert isinstance(finding, dict)
        assert "reasoning" in finding
        assert "Setup error" in finding["reasoning"]
        assert finding.get("confidence") == 0.0

    def test_record_contribution_with_none_finding(self):
        """Blackboard should handle empty finding gracefully."""
        blackboard = make_initial_blackboard("test", {})

        # Empty finding should still be recorded
        finding: dict = {"reasoning": "", "confidence": 0.0}
        record_specialist_contribution(blackboard, "coach", finding, 0.0)

        retrieved = get_specialist_finding(blackboard, "coach")
        assert retrieved is not None
        assert retrieved["confidence"] == 0.0
