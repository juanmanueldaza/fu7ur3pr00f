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
            scheduler: Optional custom scheduler (default: linear_iterative)
        """
        self.specialists = specialists
        self.scheduler = scheduler or BlackboardScheduler(
            strategy="linear_iterative", max_iterations=5
        )

    def execute(
        self,
        query: str,
        user_profile: dict[str, Any],
        constraints: list[str] | None = None,
        on_specialist_start: Callable[[str], None] | None = None,
        on_specialist_complete: Callable[[str, SpecialistFinding], None] | None = None,
    ) -> CareerBlackboard:
        """Execute blackboard-based multi-specialist analysis via LangGraph.

        Args:
            query: User's question (e.g., "5-year prediction")
            user_profile: User's career data
            constraints: Optional constraints for the analysis
            on_specialist_start: Callback when specialist starts
                Called with (specialist_name)
            on_specialist_complete: Callback when specialist finishes
                Called with (specialist_name, findings)

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

        config = {"configurable": {"thread_id": f"bb_{int(time.time() * 1000)}"}}

        # Stream updates from the graph with custom events for real-time progress
        final_state: CareerBlackboard = initial
        started_specialists: set[str] = set()

        for chunk in graph.stream(
            initial, config, stream_mode=["updates", "custom"]
        ):
            mode, data = chunk  # Unpack tuple (always a 2-tuple)

            if mode == "updates":
                for node_name, node_output in data.items():
                    if not isinstance(node_output, dict):
                        continue

                    # Fire start callback once per specialist
                    if (
                        node_name in self.specialists
                        and node_name not in started_specialists
                    ):
                        started_specialists.add(node_name)
                        if on_specialist_start:
                            on_specialist_start(node_name)

                    # Fire complete callback when specialist produces findings
                    if node_name in self.specialists:
                        finding = node_output.get("findings", {}).get(node_name)
                        if finding and on_specialist_complete:
                            on_specialist_complete(node_name, finding)

            # "custom" events are for UI progress — no state update needed

        # Get final state from graph (checkpointer is authoritative)
        snap = graph.get_state(config)
        if snap:
            final_state = dict(snap.values)  # type: ignore

        execution_time = time.time() - execution_start

        logger.info(
            "Blackboard execution complete: %d specialists, "
            "%d iterations, %.2fs total",
            len(final_state.get("findings", {})),
            final_state.get("iteration", 0) + 1,
            execution_time,
        )

        return final_state


__all__ = [
    "BlackboardExecutor",
]
