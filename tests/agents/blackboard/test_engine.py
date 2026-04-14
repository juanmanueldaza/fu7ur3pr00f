"""Tests for ConversationEngine graph-compile-once behaviour."""

from unittest.mock import MagicMock, PropertyMock, patch

from fu7ur3pr00f.container import container

_MOCK_PROFILE = MagicMock(
    name="Juan",
    location=None,
    current_role=None,
    years_experience=0,
    technical_skills=[],
    target_roles=[],
    goals=[],
    github_username=None,
    gitlab_username=None,
)

_BUILD_TARGET = (
    "fu7ur3pr00f.agents.blackboard.conversation_graph.build_conversation_graph"
)


def _fake_turn_state():
    return {
        "synthesis": {"narrative": "ok"},
        "routed_specialists": ["coach"],
        "suggested_next": [],
        "cumulative_findings": {},
        "current_blackboard": {},
        "turns": [],
        "user_profile": {},
        "current_query": "",
        "active_goals": [],
    }


class TestGraphCompileOnce:
    def setup_method(self):
        """Populate the global factory with real specialists."""
        from fu7ur3pr00f.agents.specialists.coach import CoachAgent
        from fu7ur3pr00f.agents.specialists.code import CodeAgent
        from fu7ur3pr00f.agents.specialists.founder import FounderAgent
        from fu7ur3pr00f.agents.specialists.jobs import JobsAgent
        from fu7ur3pr00f.agents.specialists.learning import LearningAgent
        from fu7ur3pr00f.container import container

        container.reset_services()
        factory = container.blackboard_factory
        factory.clear()
        factory.register_specialist("coach", CoachAgent())
        factory.register_specialist("learning", LearningAgent())
        factory.register_specialist("jobs", JobsAgent())
        factory.register_specialist("code", CodeAgent())
        factory.register_specialist("founder", FounderAgent())

    def test_graph_compiled_once_on_init(self):
        mock_graph = MagicMock()
        mock_graph.get_state.return_value = None
        mock_graph.invoke.return_value = _fake_turn_state()
        mock_build = MagicMock(return_value=mock_graph)

        with (
            patch.object(container, "get_checkpointer", return_value=MagicMock()),
            patch(_BUILD_TARGET, mock_build),
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=_MOCK_PROFILE,
            ),
        ):
            from fu7ur3pr00f.agents.blackboard.engine import ConversationEngine

            engine = ConversationEngine()
            assert mock_build.call_count == 1

            for _ in range(3):
                engine.invoke_turn("hello", thread_id="t1", user_profile={"name": "J"})

            assert mock_build.call_count == 1

    def test_callbacks_updated_per_turn(self):
        mock_graph = MagicMock()
        mock_graph.get_state.return_value = None

        captured: list[dict] = []

        def fake_invoke(state, config):  # noqa: ARG001
            captured.append(dict(engine._callbacks))
            return _fake_turn_state()

        mock_graph.invoke.side_effect = fake_invoke

        with (
            patch.object(container, "get_checkpointer", return_value=MagicMock()),
            patch(_BUILD_TARGET, return_value=mock_graph),
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=_MOCK_PROFILE,
            ),
        ):
            from fu7ur3pr00f.agents.blackboard.engine import ConversationEngine

            engine = ConversationEngine()
            spy1 = MagicMock(name="spy1")
            spy2 = MagicMock(name="spy2")

            engine.invoke_turn(
                "q1",
                thread_id="t1",
                user_profile={"name": "J"},
                on_specialist_start=spy1,
            )
            engine.invoke_turn(
                "q2",
                thread_id="t1",
                user_profile={"name": "J"},
                on_specialist_start=spy2,
            )

        assert captured[0]["on_specialist_start"] is spy1
        assert captured[1]["on_specialist_start"] is spy2

    def test_none_callbacks_dont_raise(self):
        mock_graph = MagicMock()
        mock_graph.get_state.return_value = None
        mock_graph.invoke.return_value = _fake_turn_state()

        with (
            patch.object(container, "get_checkpointer", return_value=MagicMock()),
            patch(_BUILD_TARGET, return_value=mock_graph),
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=_MOCK_PROFILE,
            ),
        ):
            from fu7ur3pr00f.agents.blackboard.engine import ConversationEngine

            engine = ConversationEngine()
            result = engine.invoke_turn(
                "hello",
                thread_id="t1",
                user_profile={"name": "J"},
                on_specialist_start=None,
                on_specialist_complete=None,
                on_tool_start=None,
                on_tool_result=None,
                confirm_fn=None,
            )

        from fu7ur3pr00f.agents.blackboard.engine import TurnResult

        assert isinstance(result, TurnResult)

    def test_reset_triggers_fresh_compile(self):
        """After reset, get_conversation_engine() must trigger a fresh compile."""
        mock_graph = MagicMock()
        mock_graph.get_state.return_value = None
        mock_graph.invoke.return_value = _fake_turn_state()
        mock_build = MagicMock(return_value=mock_graph)

        with (
            patch.object(container, "get_checkpointer", return_value=MagicMock()),
            patch(_BUILD_TARGET, mock_build),
            patch(
                "fu7ur3pr00f.container.Container.profile",
                new_callable=PropertyMock,
                return_value=_MOCK_PROFILE,
            ),
        ):
            from fu7ur3pr00f.agents.blackboard.engine import (
                get_conversation_engine,
                reset_conversation_engine,
            )

            reset_conversation_engine()
            e1 = get_conversation_engine()
            assert mock_build.call_count == 1

            reset_conversation_engine()
            e2 = get_conversation_engine()
            assert mock_build.call_count == 2  # second compile after reset

        assert e1 is not e2
