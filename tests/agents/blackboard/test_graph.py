"""Tests for the LangGraph StateGraph implementation."""

from unittest.mock import Mock

from fu7ur3pr00f.agents.blackboard.blackboard import make_initial_blackboard
from fu7ur3pr00f.agents.blackboard.graph import (
    _increment_iteration_node,
    _make_route_fn,
    _make_specialist_node,
    _synthesize_node,
    build_blackboard_graph,
)
from fu7ur3pr00f.agents.blackboard.scheduler import BlackboardScheduler


class TestSpecialistNode:
    """Test the specialist node factory."""

    def test_specialist_node_success(self):
        """Specialist node should call contribute and record findings."""
        # Create a mock specialist
        specialist = Mock()
        specialist.name = "coach"
        specialist.contribute = Mock(
            return_value={
                "gaps": ["AI"],
                "confidence": 0.85,
            }
        )

        # Create the node
        node_fn = _make_specialist_node(specialist)

        # Create initial state
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )

        # Execute node
        result = node_fn(state)

        # Verify specialist was called
        specialist.contribute.assert_called_once_with(state)

        # Verify result includes findings and current_specialist
        assert "findings" in result
        assert "coach" in result["findings"]
        assert result["findings"]["coach"]["gaps"] == ["AI"]
        assert result["current_specialist"] == "coach"

    def test_specialist_node_error_handling(self):
        """Specialist node should catch errors and record them."""
        specialist = Mock()
        specialist.name = "coach"
        specialist.contribute = Mock(side_effect=ValueError("test error"))

        node_fn = _make_specialist_node(specialist)
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )
        state["errors"] = []

        result = node_fn(state)

        # Verify error was recorded
        assert "errors" in result
        assert len(result["errors"]) == 1
        assert result["errors"][0]["specialist"] == "coach"
        assert "test error" in result["errors"][0]["error"]
        assert result["current_specialist"] == "coach"


class TestRouteFunction:
    """Test the routing function factory."""

    def test_route_to_first_specialist_from_start(self):
        """From START, should route to first specialist."""
        scheduler = BlackboardScheduler(strategy="linear_iterative")
        route_fn = _make_route_fn(scheduler)

        # Create initial state
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )

        # From start, current_specialist is None
        result = route_fn(state)

        # Should route to first specialist (coach)
        assert result == scheduler.DEFAULT_ORDER[0]

    def test_route_to_next_specialist(self):
        """Should route to next specialist in sequence."""
        scheduler = BlackboardScheduler(strategy="linear_iterative")
        route_fn = _make_route_fn(scheduler)

        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )
        state["current_specialist"] = "coach"

        result = route_fn(state)

        # Should route to next specialist (learning)
        assert result == "learning"

    def test_route_to_synthesize_when_done(self):
        """Should route to synthesize when no more specialists."""
        scheduler = BlackboardScheduler(strategy="linear_iterative", max_iterations=5)
        route_fn = _make_route_fn(scheduler)

        # At max iterations, wrapping back should go to synthesis
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
            max_iterations=5,
        )
        state["current_specialist"] = "founder"  # last specialist
        state["findings"] = {
            "coach": {},
            "learning": {},
            "code": {},
            "jobs": {},
            "founder": {},
        }
        state["iteration"] = 5  # at max iterations

        result = route_fn(state)

        # Scheduler returns None when at max, so route goes to synthesize
        assert result == "synthesize"

    def test_route_to_increment_when_wrapping(self):
        """Should increment iteration when wrapping back to first specialist."""
        scheduler = BlackboardScheduler(strategy="linear_iterative")
        route_fn = _make_route_fn(scheduler)

        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )
        state["current_specialist"] = "founder"  # last specialist
        state["iteration"] = 0  # not at max yet

        result = route_fn(state)

        # Should route to increment_iteration (not directly to coach)
        assert result == "increment_iteration"


class TestIncrementIterationNode:
    """Test the iteration increment node."""

    def test_increment_iteration(self):
        """Should increment iteration counter."""
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )
        state["iteration"] = 0

        result = _increment_iteration_node(state)

        assert result["iteration"] == 1

    def test_increment_from_higher_iteration(self):
        """Should increment from any iteration value."""
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )
        state["iteration"] = 3

        result = _increment_iteration_node(state)

        assert result["iteration"] == 4


class TestSynthesizeNode:
    """Test the synthesis node."""

    def test_synthesize_with_findings(self):
        """Should synthesize findings into integrated advice."""
        state = make_initial_blackboard(
            query="5-year prediction",
            user_profile={"role": "developer"},
        )
        state["findings"] = {
            "coach": {
                "target_role": "Staff Engineer",
                "timeline": "2-3 years",
                "gaps": ["Leadership"],
            },
            "learning": {
                "skills": ["System Design", "Management"],
            },
            "code": {
                "portfolio_items": ["OSS contributions"],
            },
            "jobs": {
                "opportunities": ["FAANG companies"],
            },
            "founder": {
                "recommended_path": ["Build portfolio"],
            },
        }
        state["iteration"] = 1

        result = _synthesize_node(state)

        assert "synthesis" in result
        synthesis = result["synthesis"]
        assert synthesis["query"] == "5-year prediction"
        assert synthesis["num_iterations"] == 2
        assert synthesis["specialists_contributed"] == [
            "coach",
            "learning",
            "code",
            "jobs",
            "founder",
        ]

        # Check integrated advice
        advice = synthesis["integrated_advice"]
        assert advice["target_role"] == "Staff Engineer"
        assert advice["timeline"] == "2-3 years"
        assert "Leadership" in advice["key_gaps"]
        assert "System Design" in advice["learning_plan"]

    def test_synthesize_with_missing_specialists(self):
        """Should handle missing specialist findings."""
        state = make_initial_blackboard(
            query="test",
            user_profile={"role": "developer"},
        )
        # Only one specialist contributed
        state["findings"] = {
            "coach": {
                "target_role": "Senior Developer",
            },
        }
        state["iteration"] = 0

        result = _synthesize_node(state)

        synthesis = result["synthesis"]
        advice = synthesis["integrated_advice"]
        assert advice["target_role"] == "Senior Developer"
        # Missing specialists should have empty defaults
        assert advice["learning_plan"] == []
        assert advice["opportunities"] == []


class TestBuildBlackboardGraph:
    """Test graph construction."""

    def test_build_graph_with_mock_specialists(self):
        """Should build a valid StateGraph."""
        # Create mock specialists
        specialists = {}
        for name in ["coach", "learning"]:
            specialist = Mock()
            specialist.name = name
            specialist.contribute = Mock(return_value={"confidence": 0.8})
            specialists[name] = specialist

        # Build graph
        graph = build_blackboard_graph(specialists)

        # Verify graph is compiled
        assert graph is not None
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")

    def test_build_graph_with_default_scheduler(self):
        """Should use default scheduler if not provided."""
        specialists = {
            "coach": Mock(name="coach", contribute=Mock()),
        }

        graph = build_blackboard_graph(specialists)

        assert graph is not None

    def test_build_graph_with_custom_scheduler(self):
        """Should accept custom scheduler."""
        specialists = {
            "coach": Mock(name="coach", contribute=Mock()),
        }
        custom_scheduler = BlackboardScheduler(strategy="linear", max_iterations=3)

        graph = build_blackboard_graph(specialists, scheduler=custom_scheduler)

        assert graph is not None
