"""Tests for synthesis token streaming ContextVar."""

from collections.abc import Callable
from contextvars import ContextVar
from unittest.mock import MagicMock, PropertyMock, patch

from fu7ur3pr00f.agents.blackboard.streaming import synthesis_token_callback
from fu7ur3pr00f.container import container


class TestSynthesisTokenCallback:
    def test_default_is_none(self) -> None:
        assert synthesis_token_callback.get() is None

    def test_set_and_reset(self) -> None:
        cb = MagicMock()
        token = synthesis_token_callback.set(cb)
        assert synthesis_token_callback.get() is cb
        synthesis_token_callback.reset(token)
        assert synthesis_token_callback.get() is None

    def test_is_contextvar(self) -> None:
        assert isinstance(synthesis_token_callback, ContextVar)

    def test_thread_isolation(self) -> None:
        """Verify the ContextVar value is isolated per thread."""
        import threading

        results: list[object] = []

        def reader() -> None:
            # In a new thread, the ContextVar should still have default=None
            results.append(synthesis_token_callback.get())

        cb = MagicMock()
        token = synthesis_token_callback.set(cb)
        t = threading.Thread(target=reader)
        t.start()
        t.join()
        synthesis_token_callback.reset(token)
        # Thread got None — ContextVars are thread-local by default
        assert results[0] is None


class TestSynthesizeNodeStreaming:
    """Test that _synthesize_node uses model.stream() and fires the callback."""

    def _make_chunks(self, tokens: list[str]) -> list[MagicMock]:
        chunks = []
        for t in tokens:
            chunk = MagicMock()
            chunk.content = t
            chunks.append(chunk)
        return chunks

    def _make_two_specialist_state(self, query: str = "test query") -> dict:
        """Return state with 2 specialists to trigger the multi-specialist path."""
        return {
            "findings": {
                "coach": {
                    "reasoning": "coaching reasoning",
                    "recommendations": ["Rec 1"],
                    "data": {},
                    "confidence": 0.9,
                },
                "jobs": {
                    "reasoning": "jobs reasoning",
                    "recommendations": ["Job 1"],
                    "data": {},
                    "confidence": 0.8,
                },
            },
            "current_query": query,
            "synthesis": {},
        }

    def test_streams_tokens_and_accumulates_narrative(self) -> None:
        from fu7ur3pr00f.agents.blackboard import graph as graph_module

        tokens = ["Hello", " world", "!"]
        chunks = self._make_chunks(tokens)
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)
        mock_config = MagicMock()

        received: list[str] = []
        cb: Callable[[str], None] = received.append

        state = self._make_two_specialist_state()

        cv_token = synthesis_token_callback.set(cb)
        try:
            with (
                patch.object(
                    container, "get_model", return_value=(mock_model, mock_config)
                ),
                patch.object(container, "load_prompt", return_value="prompt text"),
            ):
                result = graph_module._synthesize_node(state)  # type: ignore[arg-type]
        finally:
            synthesis_token_callback.reset(cv_token)

        assert result["synthesis"]["narrative"] == "Hello world!"
        assert received == ["Hello", " world", "!"]

    def test_empty_chunks_are_skipped(self) -> None:
        from fu7ur3pr00f.agents.blackboard import graph as graph_module

        tokens = ["Hello", "", " there"]
        chunks = self._make_chunks(tokens)
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)
        mock_config = MagicMock()

        received: list[str] = []

        state = self._make_two_specialist_state()

        cv_token = synthesis_token_callback.set(received.append)
        try:
            with (
                patch.object(
                    container, "get_model", return_value=(mock_model, mock_config)
                ),
                patch.object(container, "load_prompt", return_value="prompt text"),
            ):
                graph_module._synthesize_node(state)  # type: ignore[arg-type]
        finally:
            synthesis_token_callback.reset(cv_token)

        # Empty string not fired
        assert "" not in received
        assert received == ["Hello", " there"]

    def test_callback_none_is_safe(self) -> None:
        """No callback set — streaming must not crash."""
        from fu7ur3pr00f.agents.blackboard import graph as graph_module

        chunks = self._make_chunks(["token"])
        mock_model = MagicMock()
        mock_model.stream.return_value = iter(chunks)
        mock_config = MagicMock()

        state = self._make_two_specialist_state("q")

        # synthesis_token_callback is None by default — no crash expected
        with (
            patch.object(
                container, "get_model", return_value=(mock_model, mock_config)
            ),
            patch.object(container, "load_prompt", return_value="prompt text"),
        ):
            result = graph_module._synthesize_node(state)  # type: ignore[arg-type]

        assert result["synthesis"]["narrative"] == "token"

    def test_invoke_turn_sets_contextvar(self) -> None:
        """invoke_turn() must set synthesis_token_callback before calling graph."""
        from fu7ur3pr00f.agents.blackboard.engine import ConversationEngine

        captured: list[object] = []

        def fake_invoke(_state: dict, _config: dict) -> dict:
            captured.append(synthesis_token_callback.get())
            return {
                "synthesis": {"narrative": "done"},
                "routed_specialists": [],
                "suggested_next": [],
                "cumulative_findings": {},
            }

        cb = MagicMock()

        mock_graph = MagicMock()
        mock_graph.get_state.return_value = MagicMock(values={"current_query": ""})
        mock_graph.invoke.side_effect = fake_invoke

        engine = ConversationEngine.__new__(ConversationEngine)
        engine._callbacks = {}
        engine._graph = mock_graph

        with patch(
            "fu7ur3pr00f.container.Container.profile",
            new_callable=PropertyMock,
        ) as mock_profile:
            mock_profile.return_value = MagicMock(
                name="test",
                location="",
                current_role="",
                years_experience=0,
                technical_skills=[],
                target_roles=[],
                goals=[],
                github_username="",
                gitlab_username="",
            )
            engine.invoke_turn("hello", on_synthesis_token=cb)

        assert captured[0] is cb
