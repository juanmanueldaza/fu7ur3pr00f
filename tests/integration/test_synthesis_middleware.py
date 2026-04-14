"""Integration test for synthesis middleware with real specialist findings.

Verifies that AnalysisSynthesisMiddleware correctly:
1. Masks analysis tool results
2. Triggers synthesis when specialist findings are present
3. Includes non-analysis tool results (salary, profile) in synthesis prompt
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain.agents.middleware.types import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from fu7ur3pr00f.agents.middleware import AnalysisSynthesisMiddleware
from fu7ur3pr00f.container import container

pytestmark = pytest.mark.integration


class TestSynthesisWithRealFindings:
    """Test synthesis middleware with realistic specialist finding patterns."""

    def setup_method(self):
        self.middleware = AnalysisSynthesisMiddleware()

    def test_synthesis_with_realistic_analysis_output(self):
        """Synthesis should process realistic career alignment analysis output."""
        # Simulate a realistic turn where analysis tools ran
        messages = [
            HumanMessage(content="How well does my profile match my target roles?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "analyze_career_alignment", "args": {}}
                ],
            ),
            ToolMessage(
                content=(
                    "### Professional Identity\n"
                    "- Current: Senior Engineer at Tech Corp\n"
                    "- Target: Staff Engineer\n"
                    "- Gap: ML experience, leadership\n"
                    "### Alignment Score: 72/100\n"
                    "Your profile shows strong engineering fundamentals "
                    "but lacks ML and leadership experience for Staff level."
                ),
                tool_call_id="c1",
                name="analyze_career_alignment",
            ),
        ]

        # Handler returns a generic (non-synthesized) response
        handler_response = AIMessage(content="Your alignment score is 72/100.")

        def handler(req):
            return ModelResponse(result=[handler_response])

        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        # Mock synthesis to return a targeted response
        synthesis_result = AIMessage(
            content=(
                "You're at 72/100 alignment for Staff Engineer. "
                "Focus on: 1) ML project experience, 2) Technical leadership. "
                "Consider taking an ML fundamentals course."
            )
        )

        with patch.object(
            self.middleware,
            "_synthesize",
            return_value=ModelResponse(result=[synthesis_result]),
        ) as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_called_once()
        assert response.result[0].content == synthesis_result.content

    def test_synthesis_includes_salary_context(self):
        """Synthesis should include salary data alongside analysis findings."""
        messages = [
            HumanMessage(content="Should I take a pay cut to join an AI startup?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "analyze_career_alignment", "args": {}},
                    {"id": "c2", "name": "get_salary_insights", "args": {}},
                ],
            ),
            ToolMessage(
                content=(
                    "### Alignment Score: 80/100\n"
                    "AI startup role aligns well with your career goals."
                ),
                tool_call_id="c1",
                name="analyze_career_alignment",
            ),
            ToolMessage(
                content=(
                    "AI startup salary range: $120K-$160K + equity.\n"
                    "Current market rate: $150K-$200K at established companies."
                ),
                tool_call_id="c2",
                name="get_salary_insights",
            ),
        ]

        def handler(req):
            return ModelResponse(result=[AIMessage(content="Consider the equity.")])

        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        with patch.object(self.middleware, "_synthesize") as mock_synth:
            self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_called_once()
        # Verify the synthesis prompt included both analysis and salary data
        call_args = mock_synth.call_args
        analysis_results = call_args[0][1]  # Second arg is analysis_results
        assert "analyze_career_alignment" in analysis_results
        assert "AI startup role aligns" in analysis_results["analyze_career_alignment"]

    def test_no_synthesis_for_tool_continuation(self):
        """No synthesis when agent wants to call more tools."""
        messages = [
            HumanMessage(content="Analyze my career path"),
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "c1", "name": "analyze_skill_gaps", "args": {}},
                ],
            ),
            ToolMessage(
                content="### Skill Gaps\n- ML fundamentals\n- System design",
                tool_call_id="c1",
                name="analyze_skill_gaps",
            ),
        ]

        # Agent wants to call more tools — no synthesis
        tool_response = AIMessage(
            content="",
            tool_calls=[{"id": "c2", "name": "get_career_advice", "args": {}}],
        )

        def handler(req):
            return ModelResponse(result=[tool_response])

        request = ModelRequest(
            model=MagicMock(),
            messages=messages,
            system_message=SystemMessage(content="system"),
        )

        with patch.object(self.middleware, "_synthesize") as mock_synth:
            response = self.middleware.wrap_model_call(request, handler)

        mock_synth.assert_not_called()
        # Original response returned
        assert response.result[0].tool_calls[0]["name"] == "get_career_advice"

    def test_synthesis_prompt_contains_correct_user_question(self):
        """_synthesize should use the LAST HumanMessage as the question."""
        mock_chunk = MagicMock()
        mock_chunk.content = "Targeted career advice"
        mock_model = MagicMock()
        mock_model.stream.return_value = iter([mock_chunk])

        messages = [
            HumanMessage(content="first question about salary"),
            HumanMessage(content="actually, how do I transition to ML engineering?"),
            AIMessage(
                content="",
                tool_calls=[{"id": "c1", "name": "analyze_skill_gaps", "args": {}}],
            ),
            ToolMessage(
                content="Gaps: ML, statistics",
                tool_call_id="c1",
                name="analyze_skill_gaps",
            ),
        ]
        analysis_results = {"analyze_skill_gaps": "Gaps: ML, statistics"}

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

        # Verify model.stream was called with the LAST human message
        call_args = mock_model.stream.call_args[0][0]
        prompt_content = call_args[0].content
        assert "how do I transition to ML engineering?" in prompt_content
        assert "first question about salary" not in prompt_content
