"""Analysis synthesis middleware — masks analysis results and synthesizes responses.

Two-pass middleware that prevents the agent from rewriting analysis tool results
into generic advice, and instead produces focused synthesis from actual tool data.

Usage:
    from fu7ur3pr00f.agents.middleware.analysis_synthesis import (
        AnalysisSynthesisMiddleware,
    )
"""

import logging
from collections.abc import Callable
from typing import Any

from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from fu7ur3pr00f.agents.blackboard.streaming import synthesis_token_callback
from fu7ur3pr00f.constants import ANALYSIS_MARKER as _ANALYSIS_MARKER
from fu7ur3pr00f.container import container
from fu7ur3pr00f.utils.security import anonymize_career_data, sanitize_for_prompt

logger = logging.getLogger(__name__)

# Analysis tools whose results are displayed directly to the user in Rich panels.
_ANALYSIS_TOOLS = frozenset(
    {
        "analyze_skill_gaps",
        "analyze_career_alignment",
        "get_career_advice",
    }
)


class AnalysisSynthesisMiddleware(AgentMiddleware[Any, Any, Any]):
    """Two-pass middleware: masks analysis results, then synthesizes the final response.

    Pass 1 (before model): Replaces analysis tool results with short markers so
    the agent model can't rewrite them into generic advice. The user already
    sees full results in Rich UI panels during streaming.

    Pass 2 (after model): When the agent produces its final response (no more
    tool_calls) and analysis tools were used, the generic response is DISCARDED
    and replaced with a focused synthesis from a separate LLM call.

    Uses wrap_model_call so modifications are ephemeral — the persisted state
    keeps the original analysis results and the synthesized response.
    """

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest[Any]], ModelResponse[Any]],
    ) -> ModelResponse[Any]:
        # Find the last HumanMessage index — only consider analysis tools
        # from the current turn (after the last user message)
        last_human_idx = -1
        for i in range(len(request.messages) - 1, -1, -1):
            if isinstance(request.messages[i], HumanMessage):
                last_human_idx = i
                break

        # Phase 1: Mask analysis tool results with markers
        modified: list[AnyMessage] = []
        analysis_results: dict[str, str] = {}  # tool_name → original content
        for idx, msg in enumerate(request.messages):
            if (
                isinstance(msg, ToolMessage)
                and msg.name in _ANALYSIS_TOOLS
                and idx > last_human_idx
            ):
                analysis_results[msg.name] = str(msg.content)
                modified.append(
                    ToolMessage(
                        content=_ANALYSIS_MARKER,
                        name=msg.name,
                        tool_call_id=msg.tool_call_id,
                    )
                )
            else:
                modified.append(msg)

        if analysis_results:
            logger.info("Masked %d analysis tool result(s)", len(analysis_results))
            response = handler(request.override(messages=modified))
        else:
            return handler(request)

        # Phase 2: If this is the final response (no tool_calls), synthesize
        if not response.result:
            return response

        ai_msg = response.result[0]
        if not isinstance(ai_msg, AIMessage) or ai_msg.tool_calls:
            # Agent wants to call more tools — let it continue
            return response

        # Final response detected — replace with synthesis
        logger.info("Synthesizing final response (replacing generic agent text)")
        return self._synthesize(
            request.messages,
            analysis_results,
            last_human_idx,
        )

    def _synthesize(
        self,
        messages: list[AnyMessage],
        analysis_results: dict[str, str],
        last_human_idx: int,
    ) -> ModelResponse:
        """Build a focused synthesis from tool results via a separate LLM call."""

        # Extract the user's question (last HumanMessage)
        user_question = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                raw = msg.content
                user_question = raw if isinstance(raw, str) else str(raw)
                break

        # Only collect tool results from current turn (after last user msg)
        other_results: list[str] = []
        for msg in messages[last_human_idx:]:
            if (
                isinstance(msg, ToolMessage)
                and msg.name not in _ANALYSIS_TOOLS
                and msg.content
            ):
                other_results.append(f"**{msg.name}:**\n{msg.content}")

        # Build the tool results context
        parts: list[str] = []
        for name, content in analysis_results.items():
            parts.append(f"**{name}:**\n{content}")
        parts.extend(other_results)
        tool_results = "\n\n---\n\n".join(parts)

        # Anonymize PII and escape XML boundaries in tool results
        tool_results = sanitize_for_prompt(
            anonymize_career_data(tool_results, preserve_professional_emails=True)
        )

        # Load synthesis prompt and format
        prompt_template = container.load_prompt("synthesis")
        prompt = prompt_template.format(
            user_question=user_question,
            tool_results=tool_results,
        )

        # Call synthesis model with streaming
        model, config = container.get_model(purpose="synthesis")
        logger.info("Synthesis model: %s", config.description)

        narrative = ""
        callback = synthesis_token_callback.get()
        # Google Gemini requires HumanMessage for synthesis
        # Other providers use SystemMessage for proper behavioral context
        if config.provider == "google":
            chunks = model.stream([HumanMessage(content=prompt)])
        else:
            chunks = model.stream(
                [SystemMessage(content=prompt), HumanMessage(content=prompt)]
            )
        for chunk in chunks:
            token = str(getattr(chunk, "content", "") or "")
            if token:
                narrative += token
                if callback:
                    callback(token)

        return ModelResponse(result=[AIMessage(content=narrative)])


__all__ = ["AnalysisSynthesisMiddleware"]
