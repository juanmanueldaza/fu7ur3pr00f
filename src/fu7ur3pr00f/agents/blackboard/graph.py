"""LangGraph StateGraph for blackboard-based multi-specialist orchestration.

Converts the blackboard pattern into a native LangGraph StateGraph with
nodes for each specialist, iteration control, and synthesis.

Graph topology:
    START → coach → learning → code → jobs → founder → route_fn
                                                          ├→ next specialist
                                                          ├→ increment_iteration → coach
                                                          └→ synthesize → END

Each specialist node emits real-time progress events via get_stream_writer()
for integration with UI components.
"""

import logging
import time
from typing import Any

from langgraph.graph import StateGraph

from fu7ur3pr00f.agents.blackboard.blackboard import CareerBlackboard
from fu7ur3pr00f.agents.blackboard.scheduler import BlackboardScheduler

logger = logging.getLogger(__name__)


def _make_specialist_node(specialist: Any):
    """Factory to create a specialist node function.

    Args:
        specialist: The specialist agent (has a contribute() method)

    Returns:
        Node function that calls specialist.contribute() and records findings
    """

    def specialist_node(state: CareerBlackboard) -> dict[str, Any]:
        """Execute specialist contribution and record on blackboard.

        Emits real-time progress events via streaming for UI integration.
        """
        specialist_name = specialist.name
        logger.debug("Specialist %r contributing...", specialist_name)

        # Get stream writer for real-time progress (optional, safe if None)
        try:
            from langgraph.config import get_stream_writer

            stream_writer = get_stream_writer()
        except (ImportError, RuntimeError):
            stream_writer = None

        # Emit start event before contribution
        if stream_writer:
            stream_writer(
                {
                    "type": "specialist_start",
                    "specialist": specialist_name,
                    "iteration": state.get("iteration", 0),
                    "timestamp": time.time(),
                }
            )

        try:
            contrib_start = time.time()
            finding = specialist.contribute(state)
            contrib_time = time.time() - contrib_start

            # Set finding metadata
            confidence = finding.get("confidence", 0.75)
            finding["confidence"] = confidence
            finding["iteration_contributed"] = state.get("iteration", 0)

            # Create immutable state update (not mutating state in-place)
            change_entry = {
                "iteration": state.get("iteration", 0),
                "specialist": specialist_name,
                "timestamp": time.time(),
                "keys_modified": list(finding.keys()),
                "confidence": confidence,
            }

            logger.info(
                "Specialist %r contributed in %.2fs (confidence=%.2f)",
                specialist_name,
                contrib_time,
                confidence,
            )

            # Emit completion event
            if stream_writer:
                stream_writer(
                    {
                        "type": "specialist_complete",
                        "specialist": specialist_name,
                        "elapsed": contrib_time,
                        "confidence": confidence,
                    }
                )

            # Return immutable state updates (reducer handles change_log merging)
            return {
                "findings": state.get("findings", {}) | {specialist_name: finding},
                "change_log": [change_entry],
                "current_specialist": specialist_name,
            }

        except Exception as e:
            logger.exception("Error in specialist %r", specialist_name)

            # Emit error event
            if stream_writer:
                stream_writer(
                    {
                        "type": "specialist_error",
                        "specialist": specialist_name,
                        "error": str(e),
                    }
                )

            # Create new error entry
            error_entry = {
                "specialist": specialist_name,
                "error": str(e),
                "iteration": state.get("iteration", 0),
            }
            # Return immutable: new list with error appended
            return {
                "errors": [*state.get("errors", []), error_entry],
                "current_specialist": specialist_name,
            }

    return specialist_node


def _make_route_fn(scheduler: BlackboardScheduler):
    """Factory to create the routing function for conditional edges.

    Args:
        scheduler: The scheduler that determines next specialist

    Returns:
        Route function that returns next specialist name or special node
    """

    def route_fn(state: CareerBlackboard) -> str:
        """Determine next node based on scheduler."""
        current = state.get("current_specialist")
        next_specialist = scheduler.get_next_specialist(state, current)

        if not next_specialist:
            logger.debug("No more specialists scheduled, moving to synthesis")
            return "synthesize"

        # If wrapping back to first specialist, increment iteration
        if current is not None and next_specialist == scheduler.DEFAULT_ORDER[0]:
            logger.debug("Iteration complete, incrementing")
            return "increment_iteration"

        logger.debug("Next specialist: %r", next_specialist)
        return next_specialist

    return route_fn


def _increment_iteration_node(state: CareerBlackboard) -> dict[str, Any]:
    """Increment iteration counter.

    After this node, the edge routes back to the first specialist.
    """
    new_iteration = state.get("iteration", 0) + 1
    logger.debug("Iteration %d starting", new_iteration)
    return {"iteration": new_iteration}


def _synthesize_node(state: CareerBlackboard) -> dict[str, Any]:
    """Synthesize all specialist findings into integrated advice.

    Args:
        state: Final blackboard state with all findings

    Returns:
        Updated state with synthesis key populated
    """
    findings = state.get("findings", {})
    query = state.get("query", "")

    synthesis = {
        "query": query,
        "specialists_contributed": list(findings.keys()),
        "num_iterations": state.get("iteration", 0) + 1,
        "all_findings": findings,
    }

    # Extract key insights for synthesis
    coach = findings.get("coach", {})
    learning = findings.get("learning", {})
    code = findings.get("code", {})
    jobs = findings.get("jobs", {})
    founder = findings.get("founder", {})

    # Build integrated advice
    synthesis["integrated_advice"] = {
        "target_role": coach.get("target_role", "Not determined"),
        "timeline": coach.get("timeline", "2-3 years"),
        "key_gaps": coach.get("gaps", []),
        "learning_plan": learning.get("skills", []),
        "portfolio_strategy": code.get("portfolio_items", []),
        "opportunities": jobs.get("opportunities", []),
        "next_steps": founder.get("recommended_path", []),
    }

    logger.info(
        "Synthesis complete: %d specialists, %d iterations",
        len(findings),
        state.get("iteration", 0) + 1,
    )

    return {"synthesis": synthesis}


def build_blackboard_graph(
    specialists: dict[str, Any],
    scheduler: BlackboardScheduler | None = None,
    checkpointer: Any | None = None,
) -> Any:
    """Build a compiled LangGraph StateGraph for blackboard orchestration.

    Args:
        specialists: Dict mapping specialist names to agent objects
        scheduler: Optional custom scheduler (default: linear_iterative)
        checkpointer: Optional SqliteSaver checkpointer for persistence

    Returns:
        Compiled CompiledStateGraph ready for .stream() / .invoke()
    """
    if scheduler is None:
        scheduler = BlackboardScheduler(strategy="linear_iterative", max_iterations=5)

    graph = StateGraph(CareerBlackboard)

    # Add specialist nodes
    for spec_name, specialist in specialists.items():
        node_fn = _make_specialist_node(specialist)
        graph.add_node(spec_name, node_fn)

    # Add utility nodes
    graph.add_node("increment_iteration", _increment_iteration_node)
    graph.add_node("synthesize", _synthesize_node)

    # Routing: each specialist → route_fn → next specialist / synthesize
    route_fn = _make_route_fn(scheduler)
    for spec_name in specialists:
        graph.add_conditional_edges(
            spec_name,
            route_fn,
            {
                "synthesize": "synthesize",
                "increment_iteration": "increment_iteration",
                **{name: name for name in specialists},
            },
        )

    # Increment → first specialist (start new iteration)
    first_specialist = scheduler.DEFAULT_ORDER[0]
    graph.add_edge("increment_iteration", first_specialist)

    # Entry point → first specialist
    graph.add_edge("__start__", first_specialist)

    compiled = graph.compile(checkpointer=checkpointer)
    logger.info(
        "Built blackboard graph: %d specialists, strategy=%s, max_iterations=%d",
        len(specialists),
        scheduler.strategy,
        scheduler.max_iterations,
    )
    return compiled


__all__ = [
    "build_blackboard_graph",
]
