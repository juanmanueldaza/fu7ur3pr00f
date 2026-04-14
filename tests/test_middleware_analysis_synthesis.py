"""Tests for AnalysisSynthesisMiddleware."""

from typing import Any, cast
from unittest.mock import MagicMock, patch

from langchain.agents.middleware.types import AgentState, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from fu7ur3pr00f.agents.middleware import _ANALYSIS_MARKER, AnalysisSynthesisMiddleware
from fu7ur3pr00f.container import container

pytestmark = __import__("pytest").mark.unit


def _make_state(messages: list[Any]) -> AgentState[Any]:
    """Build a minimal AgentState dict."""
    return cast(AgentState[Any], {"messages": messages})


class TestAnalysisSynthesisMiddleware:
    """Tests for AnalysisSynthesisMiddleware (wrap_model_call)."""

    def setup_method(self):
        self.middleware = AnalysisSynthesisMiddleware()

    def _make_handler(self, response_msg=None):
        """Build a handler that captures messages and returns a configurable
        response."""
        captured = {}

        if response_msg is None:
            # Default: final response (no tool_calls)
            response_msg = AIMessage(content="Generic advice here...")

        def handler(req):
            captured["messages"] = req.messages
            return ModelResponse(result=[response_msg])

        return handler, captured

    def _call_masking(self, messages):
        """Invoke wrap_model_call and return the messages the handler received."""
        handler, captured = self._make_handler()
        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )
        # Patch synthesis to avoid real LLM call
        synth_response = ModelResponse(result=[AIMessage(content="synth")])
        with patch.object(self.middleware, "_synthesize", return_value=synth_response):
            self.middleware.wrap_model_call(request, handler)
        return captured["messages"]

    # =========================================================================
    # Phase 1: Masking tests
    # =========================================================================

    def test_no_analysis_tools_passthrough(self):
        """Handler receives original messages when no analysis tools present."""
        messages = [
            HumanMessage(content="hello"),
            AIMessage(
                content="",
                tool_calls=[{"id": "call_1", "name": "get_user_profile", "args": {}}],
            ),
            ToolMessage(
                content="Name: Juan", tool_call_id="call_1", name="get_user_profile"
            ),
        ]
        handler, captured = self._make_handler()
        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )
        self.middleware.wrap_model_call(request, handler)
        # Messages unchanged — same objects
        assert captured["messages"][2].content == "Name: Juan"

    def test_replaces_analysis_content(self):
        """Replaces content of analysis tool results with marker."""
        messages = [
            HumanMessage(content="analyze me"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_1", "name": "analyze_career_alignment", "args": {}}
                ],
            ),
            ToolMessage(
                content=(
                    "### Professional Identity\n- Senior Engineer at Accenture\n..."
                ),
                tool_call_id="call_1",
                name="analyze_career_alignment",
            ),
        ]
        result = self._call_masking(messages)
        tool_msg = result[2]
        assert isinstance(tool_msg, ToolMessage)
        assert tool_msg.content == _ANALYSIS_MARKER
        assert tool_msg.tool_call_id == "call_1"
        assert tool_msg.name == "analyze_career_alignment"

    def test_preserves_non_analysis_tools(self):
        """Non-analysis tools (salary, profile) remain untouched."""
        messages = [
            HumanMessage(content="money"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_1", "name": "get_salary_insights", "args": {}},
                    {"id": "call_2", "name": "analyze_skill_gaps", "args": {}},
                ],
            ),
            ToolMessage(
                content="Salary: $150K-$200K",
                tool_call_id="call_1",
                name="get_salary_insights",
            ),
            ToolMessage(
                content="### Alignment Score: 85/100\n...",
                tool_call_id="call_2",
                name="analyze_skill_gaps",
            ),
        ]
        result = self._call_masking(messages)
        # Salary tool untouched
        assert result[2].content == "Salary: $150K-$200K"
        # Analysis tool replaced
        assert result[3].content == _ANALYSIS_MARKER

    def test_preserves_tool_call_id(self):
        """tool_call_id is preserved after replacement."""
        messages = [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "tc_abc123", "name": "get_career_advice", "args": {}}
                ],
            ),
            ToolMessage(
                content="Long advice text...",
                tool_call_id="tc_abc123",
                name="get_career_advice",
            ),
        ]
        result = self._call_masking(messages)
        tool_msg = result[1]
        assert tool_msg.tool_call_id == "tc_abc123"
        assert tool_msg.name == "get_career_advice"

    def test_multiple_analysis_tools(self):
        """All analysis tools in a mixed set are replaced."""
        messages = [
            HumanMessage(content="full analysis"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "get_user_profile", "args": {}},
                    {"id": "c2", "name": "analyze_career_alignment", "args": {}},
                    {"id": "c3", "name": "analyze_skill_gaps", "args": {}},
                    {"id": "c4", "name": "get_salary_insights", "args": {}},
                ],
            ),
            ToolMessage(
                content="Profile data", tool_call_id="c1", name="get_user_profile"
            ),
            ToolMessage(
                content="Career analysis...",
                tool_call_id="c2",
                name="analyze_career_alignment",
            ),
            ToolMessage(
                content="Skill gaps...", tool_call_id="c3", name="analyze_skill_gaps"
            ),
            ToolMessage(
                content="Salary data...", tool_call_id="c4", name="get_salary_insights"
            ),
        ]
        result = self._call_masking(messages)
        # Profile (index 2) and salary (index 5) untouched
        assert result[2].content == "Profile data"
        assert result[5].content == "Salary data..."
        # Analysis tools (index 3, 4) replaced
        assert result[3].content == _ANALYSIS_MARKER
        assert result[4].content == _ANALYSIS_MARKER

    def test_empty_messages(self):
        """Handler receives empty list when no messages."""
        handler, captured = self._make_handler()
        request = ModelRequest(
            model=MagicMock(),
            messages=[],
            system_message=SystemMessage(content="system"),
        )
        self.middleware.wrap_model_call(request, handler)
        assert captured["messages"] == []

    # =========================================================================
    # Phase 2: Synthesis tests
    # =========================================================================

    def test_synthesis_called_on_final_response(self):
        """When analysis tools present and response has no tool_calls, synthesis is
        triggered."""
        messages = [
            HumanMessage(content="how to earn more?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "analyze_career_alignment", "args": {}}
                ],
            ),
            ToolMessage(
                content="Career alignment: 85/100...",
                tool_call_id="c1",
                name="analyze_career_alignment",
            ),
        ]
        # Handler returns final response (no tool_calls)
        handler, _ = self._make_handler(AIMessage(content="Generic advice..."))
        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        synthesis_result = AIMessage(content="Target $180K-$200K at Google...")
        with patch.object(
            self.middleware,
            "_synthesize",
            return_value=ModelResponse(result=[synthesis_result]),
        ) as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_called_once()
        # The synthesis result replaces the generic response
        assert response.result[0].content == "Target $180K-$200K at Google..."

    def test_no_synthesis_when_agent_calls_more_tools(self):
        """When response has tool_calls, no synthesis — agent continues."""
        messages = [
            HumanMessage(content="how to earn more?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "analyze_career_alignment", "args": {}}
                ],
            ),
            ToolMessage(
                content="Career alignment: 85/100...",
                tool_call_id="c1",
                name="analyze_career_alignment",
            ),
        ]
        # Handler returns response WITH tool_calls (agent wants to call more tools)
        tool_call_response = AIMessage(
            content="",
            tool_calls=[{"id": "c2", "name": "get_salary_insights", "args": {}}],
        )
        handler, _ = self._make_handler(tool_call_response)
        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        with patch.object(self.middleware, "_synthesize") as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_not_called()
        # Original response with tool_calls is returned
        assert isinstance(response.result[0], AIMessage)
        assert response.result[0].tool_calls[0]["name"] == "get_salary_insights"

    def test_no_synthesis_without_analysis_tools(self):
        """No synthesis when no analysis tools were in the conversation."""
        messages = [
            HumanMessage(content="what's my profile?"),
            AIMessage(
                content="",
                tool_calls=[{"id": "c1", "name": "get_user_profile", "args": {}}],
            ),
            ToolMessage(
                content="Name: Juan", tool_call_id="c1", name="get_user_profile"
            ),
        ]
        handler, _ = self._make_handler(AIMessage(content="Your name is Juan."))
        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        with patch.object(self.middleware, "_synthesize") as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_not_called()
        assert response.result[0].content == "Your name is Juan."

    def test_no_synthesis_for_previous_turn_analysis(self):
        """Analysis tools from a previous turn should NOT trigger synthesis."""
        messages = [
            # --- Previous turn: user asked about money, analysis ran ---
            HumanMessage(content="how to earn more?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "analyze_career_alignment", "args": {}}
                ],
            ),
            ToolMessage(
                content="Career alignment: 92/100...",
                tool_call_id="c1",
                name="analyze_career_alignment",
            ),
            AIMessage(content="Target $150K-$190K..."),
            # --- Current turn: user asks about LinkedIn profile ---
            HumanMessage(content="what do you think about my linkedin profile?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c2", "name": "search_career_knowledge", "args": {}}
                ],
            ),
            ToolMessage(
                content="Profile: Juan...",
                tool_call_id="c2",
                name="search_career_knowledge",
            ),
        ]
        handler, _ = self._make_handler(
            AIMessage(content="Your LinkedIn looks strong.")
        )
        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        with patch.object(self.middleware, "_synthesize") as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        # Analysis was from a previous turn — should NOT synthesize
        mock_synth.assert_not_called()
        assert response.result[0].content == "Your LinkedIn looks strong."

    def test_synthesize_extracts_user_question(self):
        """_synthesize extracts the last HumanMessage as the user question."""
        mock_chunk = MagicMock()
        mock_chunk.content = "Synthesis result"
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([mock_chunk])

        messages = [
            HumanMessage(content="first question"),
            HumanMessage(content="how to leverage my skills?"),
            AIMessage(
                content="",
                tool_calls=[{"id": "c1", "name": "analyze_skill_gaps", "args": {}}],
            ),
            ToolMessage(
                content="Gaps found...", tool_call_id="c1", name="analyze_skill_gaps"
            ),
        ]
        analysis_results = {"analyze_skill_gaps": "Gaps found..."}

        with (
            patch.object(
                container,
                "get_model",
                return_value=(
                    mock_model,
                    MagicMock(description="test-model", provider="openai"),
                ),
            ),
            patch.object(
                container,
                "load_prompt",
                return_value="Q: {user_question}\nR: {tool_results}",
            ),
        ):
            result = self.middleware._synthesize(messages, analysis_results, 1)

        # Verify the synthesis model was called via stream
        mock_model.stream.assert_called_once()
        call_args = mock_model.stream.call_args[0][0]
        prompt_content = call_args[0].content
        # Should contain the LAST human message
        assert "how to leverage my skills?" in prompt_content
        assert result.result[0].content == "Synthesis result"

    def test_synthesize_includes_other_tool_results(self):
        """_synthesize includes non-analysis tool results (salary, profile)."""
        mock_chunk = MagicMock()
        mock_chunk.content = "Synthesis"
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([mock_chunk])

        messages = [
            HumanMessage(content="money"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "get_salary_insights", "args": {}},
                    {"id": "c2", "name": "analyze_career_alignment", "args": {}},
                ],
            ),
            ToolMessage(
                content="Salary: $150K-$200K",
                tool_call_id="c1",
                name="get_salary_insights",
            ),
            ToolMessage(
                content="Alignment: 85/100",
                tool_call_id="c2",
                name="analyze_career_alignment",
            ),
        ]
        analysis_results = {"analyze_career_alignment": "Alignment: 85/100"}

        with (
            patch.object(
                container,
                "get_model",
                return_value=(
                    mock_model,
                    MagicMock(description="test-model", provider="openai"),
                ),
            ),
            patch.object(
                container,
                "load_prompt",
                return_value="Q: {user_question}\nR: {tool_results}",
            ),
        ):
            self.middleware._synthesize(messages, analysis_results, 0)

        call_args = mock_model.stream.call_args[0][0]
        prompt_content = call_args[0].content
        # Should contain both analysis AND salary data
        assert "Alignment: 85/100" in prompt_content
        assert "Salary: $150K-$200K" in prompt_content

    def test_synthesize_empty_response_passthrough(self):
        """When handler returns empty result, no synthesis attempted."""
        messages = [
            HumanMessage(content="analyze"),
            AIMessage(
                content="",
                tool_calls=[{"id": "c1", "name": "analyze_skill_gaps", "args": {}}],
            ),
            ToolMessage(
                content="Gaps...", tool_call_id="c1", name="analyze_skill_gaps"
            ),
        ]

        def handler(req):
            return ModelResponse(result=[])

        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        with patch.object(self.middleware, "_synthesize") as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_not_called()
        assert response.result == []
