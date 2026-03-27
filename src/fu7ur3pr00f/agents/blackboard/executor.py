"""Blackboard executor — runs multi-specialist analysis using the blackboard pattern.

This is the orchestration engine that:
1. Creates initial blackboard state
2. Schedules specialists in order
3. Each specialist contributes to the blackboard
4. Loops until all specialists are satisfied or max iterations reached
5. Synthesizes final advice from all findings
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from fu7ur3pr00f.agents.blackboard.blackboard import (
    CareerBlackboard,
    SpecialistFinding,
    make_initial_blackboard,
)
from fu7ur3pr00f.agents.blackboard.scheduler import BlackboardScheduler

logger = logging.getLogger(__name__)


class BlackboardExecutor:
    """Executes multi-specialist analysis using the blackboard pattern."""

    def __init__(
        self,
        specialists: dict[str, Any],
        scheduler: BlackboardScheduler | None = None,
    ):
        """Initialize the executor.

        Args:
            specialists: Dict mapping specialist names to agent objects
            scheduler: Optional custom scheduler (default: linear, 1 iteration)
        """
        self.specialists = specialists
        self.scheduler = scheduler or BlackboardScheduler(
            strategy="linear",
            max_iterations=1,
            execution_order=list(specialists.keys()),
        )

    def execute(
        self,
        query: str,
        user_profile: dict[str, Any],
        constraints: list[str] | None = None,
        on_specialist_start: Callable[[str], None] | None = None,
        on_specialist_complete: Callable[[str, SpecialistFinding], None] | None = None,
        on_tool_start: Callable[[str, str, dict], None] | None = None,
        on_tool_result: Callable[[str, str, str], None] | None = None,
    ) -> CareerBlackboard:
        """Execute blackboard-based multi-specialist analysis via LangGraph.

        Args:
            query: User's question (e.g., "5-year prediction")
            user_profile: User's career data
            constraints: Optional constraints for the analysis
            on_specialist_start: Called with (specialist_name) when specialist starts
            on_specialist_complete: Called with (specialist_name, findings) when done
            on_tool_start: Called with (specialist_name, tool_name, args) on tool call
            on_tool_result: Called with (specialist_name, tool_name, result) on tool done

        Returns:
            Final blackboard state with all findings
        """
        from fu7ur3pr00f.agents.blackboard.graph import build_blackboard_graph
        from fu7ur3pr00f.memory.checkpointer import get_checkpointer

        # Initialize blackboard
        initial = make_initial_blackboard(
            query=query,
            user_profile=user_profile,
            constraints=constraints,
            max_iterations=self.scheduler.max_iterations,
        )

        logger.info(
            "Starting blackboard execution: %s (max_iterations=%d)",
            query[:60],
            self.scheduler.max_iterations,
        )

        execution_start = time.time()

        # Build and run the StateGraph
        checkpointer = get_checkpointer()
        graph = build_blackboard_graph(self.specialists, self.scheduler, checkpointer)

        config = {"configurable": {"thread_id": f"bb_{uuid.uuid4().hex[:12]}"}}

        # Stream updates from the graph with custom events for real-time progress
        final_state: CareerBlackboard = initial
        started_specialists: set[str] = set()

        for chunk in graph.stream(initial, config, stream_mode=["updates", "custom"]):
            mode, data = chunk  # Unpack tuple (always a 2-tuple)

            if mode == "updates":
                for node_name, node_output in data.items():
                    if not isinstance(node_output, dict):
                        continue

                    # Fire complete callback when specialist produces findings
                    if node_name in self.specialists:
                        finding = node_output.get("findings", {}).get(node_name)
                        if finding and on_specialist_complete:
                            on_specialist_complete(node_name, finding)

            elif mode == "custom":
                # Forward custom events from specialist nodes to callbacks
                if isinstance(data, dict):
                    event_type = data.get("type")
                    specialist = data.get("specialist")

                    if (
                        event_type == "specialist_start"
                        and specialist in self.specialists
                    ):
                        if specialist not in started_specialists:
                            started_specialists.add(specialist)
                            if on_specialist_start:
                                on_specialist_start(specialist)

                    elif (
                        event_type == "specialist_complete"
                        and specialist in self.specialists
                    ):
                        # on_specialist_complete already fired via updates mode;
                        # here we just use the reasoning from complete event if available
                        pass

                    elif event_type == "tool_start" and on_tool_start:
                        on_tool_start(
                            specialist or "",
                            data.get("tool", ""),
                            data.get("args", {}),
                        )

                    elif event_type == "tool_result" and on_tool_result:
                        on_tool_result(
                            specialist or "",
                            data.get("tool", ""),
                            data.get("result", ""),
                        )

        # Get final state from graph (checkpointer is authoritative)
        snap = graph.get_state(config)
        if snap:
            final_state = dict(snap.values)  # type: ignore

        execution_time = time.time() - execution_start

        logger.info(
            "Blackboard execution complete: %d specialists, %d iterations, %.2fs total",
            len(final_state.get("findings", {})),
            final_state.get("iteration", 0) + 1,
            execution_time,
        )

        return final_state


__all__ = [
    "BlackboardExecutor",
]
