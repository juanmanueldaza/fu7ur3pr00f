"""Outer conversation graph — persistent session-scoped orchestration.

Wraps the per-turn blackboard graph, managing conversation history,
cumulative findings, and proactive suggestions across turns.
"""

import logging
from collections.abc import Callable
from typing import Any, cast, TYPE_CHECKING

if TYPE_CHECKING:
    from fu7ur3pr00f.agents.specialists.orchestrator import OrchestratorAgent

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from fu7ur3pr00f.container import container

from fu7ur3pr00f.agents.blackboard.session import (
    SessionState,
    format_cumulative_context,
    summarize_turn,
)
from fu7ur3pr00f.agents.blackboard.turn_classifier import classify
from fu7ur3pr00f.services.exceptions import AnalysisError

logger = logging.getLogger(__name__)


def suggest_next_node(state: SessionState) -> SessionState:
    """Generate proactive follow-up suggestions using LLM.

    Skipped for factual queries. Uses action_items, gaps, open_questions
    extracted by specialists to produce contextual next-step suggestions.
    """
    turn_type = state.get("turn_type", "new_query")

    # Skip suggestions for simple factual queries
    if turn_type == "factual":
        return {**state, "suggested_next": []}

    blackboard = state.get("current_blackboard", {})
    findings = blackboard.get("findings", {})
    if not findings:
        return {**state, "suggested_next": []}

    # Collect the richest signals from all specialists
    gaps: list[str] = []
    action_items: list[str] = []
    open_questions: list[str] = []
    for finding in findings.values():
        gaps.extend(finding.get("gaps", [])[:2])
        action_items.extend(finding.get("action_items", [])[:2])
        open_questions.extend(finding.get("open_questions", [])[:1])

    # Use LLM to generate contextual suggestions
    try:
        prompt_template = container.load_prompt("suggest_next")
        findings_text = _format_findings_for_prompt(findings)
        profile = container.profile
        profile_status = "empty" if not profile.name else f"has data ({profile.name})"
        prompt = prompt_template.format(
            query=blackboard.get("query", ""),
            findings_text=findings_text,
            gaps=", ".join(gaps[:3]) or "none",
            action_items=", ".join(action_items[:3]) or "none",
            open_questions=", ".join(open_questions[:2]) or "none",
            profile_status=profile_status,
        )
        model, _ = container.get_model(purpose="analysis")
        response = model.invoke([HumanMessage(content=prompt)])
        raw = response.content if hasattr(response, "content") else str(response)
        suggestions = _parse_suggestions(str(raw))
        logger.debug("Generated %d suggestions", len(suggestions))
    except Exception as e:
        raise AnalysisError("Suggest LLM failed") from e

    return {**state, "suggested_next": suggestions[:3]}


def build_conversation_graph(  # noqa: C901
    checkpointer: Any = None,
    callbacks: dict | None = None,
) -> Any:
    """Build the outer conversation StateGraph.

    This graph manages session-level state (turns, cumulative findings,
    active goals) and orchestrates per-turn blackboard executions.

    Args:
        checkpointer: LangGraph checkpointer for persistence across turns
        callbacks: Mutable dict holding per-turn callbacks. Keys:
            on_specialist_start, on_specialist_complete, on_tool_start,
            on_tool_result, confirm_fn. Update the dict before each
            invoke_turn() call — nodes read it at execution time.
    """
    _cb = callbacks if callbacks is not None else {}

    graph = StateGraph(SessionState)

    # ── Nodes ────────────────────────────────────────────────────────────

    def classify_turn_node(state: SessionState) -> SessionState:
        """Classify the current query's turn type."""
        query = state.get("current_query", "")
        turns = state.get("turns", [])
        active_goals = state.get("active_goals", [])

        turn_type = classify(query, turns, active_goals)
        logger.info(
            "Turn %d: query=%r → classified as %r",
            len(turns) + 1,
            query[:80],
            turn_type,
        )

        return {**state, "turn_type": turn_type}

    def route_turn_node(state: SessionState) -> SessionState:
        """Route the current query to appropriate specialists."""
        query = state.get("current_query", "")
        turn_type = state.get("turn_type", "new_query")
        turns = state.get("turns", [])
        orchestrator = container.orchestrator

        # Build conversation history for routing
        conversation_history = turns[-3:] if turns else []

        # Route based on turn type
        if turn_type == "factual":
            routed = ["coach"]  # Fast path for factual
        elif turn_type == "follow_up" and turns:
            # Reuse previous turn's specialists
            routed = turns[-1].get("specialist_names", ["coach"])
        else:
            # new_query, steer, workflow_step → standard routing
            routed = orchestrator.route(query, conversation_history, turn_type)

        logger.info(
            "Routed: query=%r, turn_type=%s → %s",
            query[:60],
            turn_type,
            routed,
        )
        return {**state, "routed_specialists": routed}

    def execute_inner_node(state: SessionState) -> SessionState:
        """Execute the inner blackboard graph for this turn."""
        query = state.get("current_query", "")
        user_profile = state.get("user_profile", {})
        routed = state.get("routed_specialists", ["coach"])
        cumulative = state.get("cumulative_findings", {})
        turn_type = state.get("turn_type", "new_query")

        # Prepare constraints with cross-turn context for follow-ups/steers
        constraints = []
        if turn_type in ("follow_up", "steer") and cumulative:
            turns = state.get("turns", [])
            context = format_cumulative_context(turns, cumulative)
            if context:
                constraints.append(context)

        # Get executor and run inner graph, passing through all callbacks
        orchestrator = container.orchestrator
        executor = orchestrator.get_executor(routed)

        logger.info(
            "execute_inner: query=%r, routed=%s, turn_type=%s, constraints=%d",
            query[:80],
            routed,
            turn_type,
            len(constraints),
        )

        try:
            blackboard = dict(
                executor.execute(
                    query=query,
                    user_profile=user_profile,
                    constraints=constraints,
                    on_specialist_start=cast(
                        Callable[[str], None] | None, _cb.get("on_specialist_start")
                    ),
                    on_specialist_complete=cast(
                        Callable[[str, Any], None] | None, _cb.get("on_specialist_complete")
                    ),
                    on_tool_start=cast(
                        Callable[[str, str, dict], None] | None, _cb.get("on_tool_start")
                    ),
                    on_tool_result=cast(
                        Callable[[str, str, str], None] | None, _cb.get("on_tool_result")
                    ),
                    confirm_fn=cast(Callable[[str, str], bool] | None, _cb.get("confirm_fn")),
                )
            )
            findings = blackboard.get("findings", {})
            logger.info(
                "Inner blackboard completed: findings=%s",
                list(findings) if isinstance(findings, dict) else [],
            )
        except Exception as e:
            logger.error(
                "Inner blackboard failed: %s",
                e,
                exc_info=True,
            )
            blackboard = {
                "query": query,
                "findings": {},
                "synthesis": {"narrative": f"Analysis failed: {e}"},
                "errors": [{"error": str(e)}],
            }

        return {**state, "current_blackboard": blackboard}

    def accumulate_node(state: SessionState) -> SessionState:
        """Merge current turn's findings into cumulative state."""
        blackboard = state.get("current_blackboard", {})
        cumulative = dict(state.get("cumulative_findings", {}))
        turns = list(state.get("turns", []))

        # Merge findings (latest per specialist overwrites)
        for specialist, finding in blackboard.get("findings", {}).items():
            cumulative[specialist] = finding

        # Summarize and append turn record
        turn_record = summarize_turn(blackboard)
        turn_record["query"] = state.get("current_query", "")
        turns.append(turn_record)

        logger.debug("Accumulated turn %d", len(turns))
        return {**state, "cumulative_findings": cumulative, "turns": turns}

    def synthesize_turn_node(state: SessionState) -> SessionState:
        """Pass through synthesis from the inner blackboard graph.

        The inner graph (build_blackboard_graph) already synthesizes using LLM.
        The outer graph enriches with cross-turn context when available.
        """
        blackboard = state.get("current_blackboard", {})
        synthesis = dict(blackboard.get("synthesis", {}))

        # Inner graph already produced a narrative — pass through
        if synthesis.get("narrative", "").strip():
            return {**state, "synthesis": synthesis}

        # Fallback: build narrative from all specialist findings
        findings = blackboard.get("findings", {})
        if findings:
            reasoning_parts = []
            for _, finding in findings.items():
                reasoning = finding.get("reasoning", "").strip()
                if reasoning:
                    reasoning_parts.append(reasoning)
            if reasoning_parts:
                synthesis["narrative"] = "\n\n".join(reasoning_parts)
                return {**state, "synthesis": synthesis}

        raise AnalysisError("Synthesis produced no narrative and no specialist reasoning")

    # ── Graph construction ────────────────────────────────────────────────

    graph.add_node("classify_turn", classify_turn_node)
    graph.add_node("route_turn", route_turn_node)
    graph.add_node("execute_inner", execute_inner_node)
    graph.add_node("accumulate", accumulate_node)
    graph.add_node("synthesize_turn", synthesize_turn_node)
    graph.add_node("suggest_next", suggest_next_node)

    # Edges: linear flow
    graph.add_edge("classify_turn", "route_turn")
    graph.add_edge("route_turn", "execute_inner")
    graph.add_edge("execute_inner", "accumulate")
    graph.add_edge("accumulate", "synthesize_turn")
    graph.add_edge("synthesize_turn", "suggest_next")
    graph.add_edge("suggest_next", END)

    graph.set_entry_point("classify_turn")

    return graph.compile(checkpointer=checkpointer)


def _format_findings_for_prompt(findings: dict[str, Any]) -> str:
    """Format specialist findings as readable text for prompts."""
    parts = []
    for specialist, finding in findings.items():
        parts.append(f"**{specialist.upper()}**: {finding.get('reasoning', '')[:200]}")
    return "\n".join(parts) if parts else "No findings"


def _parse_suggestions(text: str) -> list[str]:
    """Parse LLM-generated suggestions from bullet-point text."""
    suggestions = []
    for line in text.strip().splitlines():
        line = line.strip().lstrip("-•*123. ").strip()
        if line and len(line) > 5:
            suggestions.append(line)
    return suggestions[:3]


__all__ = ["build_conversation_graph", "suggest_next_node"]
