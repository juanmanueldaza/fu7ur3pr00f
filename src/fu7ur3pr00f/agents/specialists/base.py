"""Base class for specialist agents.

Each specialist agent is a compiled LangGraph agent (via create_agent())
with a curated tool subset and a focused system prompt.

The base class handles:
- Compiling and caching the per-specialist LangGraph graph
- Keyword-based intent routing
- Shared plumbing (model, checkpointer, middleware)
- Two modes of operation:
  * stream(): Direct streaming to user (original mode)
  * contribute(): Blackboard pattern collaboration (new mode)
"""

import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from fu7ur3pr00f.agents.blackboard.blackboard import CareerBlackboard, SpecialistFinding

logger = logging.getLogger(__name__)

# Module-level cache: specialist class name → compiled agent graph
_compiled_agents: dict[str, Any] = {}
_agents_lock = threading.Lock()


@dataclass
class KnowledgeResult:
    """A search result from the career knowledge base."""

    content: str
    metadata: dict[str, Any]
    score: float | None = None


@dataclass
class MemoryResult:
    """A recalled episodic memory."""

    content: str
    event_type: str
    timestamp: float | None = None
    score: float | None = None


class BaseAgent(ABC):
    """Abstract base for specialist agents.

    Subclasses must implement:
    - name           : str — agent identifier
    - description    : str — human-readable description
    - system_prompt  : str — specialist persona and instructions
    - tools          : list — curated subset of the 41 career tools
    - can_handle()   : bool — keyword-based intent matching
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent identifier (e.g., 'coach')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Specialist persona and focused instructions.

        Appended to the base system prompt (which already contains the
        user profile and live knowledge base stats) via make_specialist_prompt().
        """
        ...

    @property
    @abstractmethod
    def tools(self) -> list:
        """Curated tool subset for this specialist."""
        ...

    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        """Keyword-based intent matching for routing."""
        ...

    # ── Blackboard pattern ───────────────────────────────────────────────

    def contribute(self, blackboard: CareerBlackboard) -> SpecialistFinding:
        """Contribute analysis to the shared blackboard.

        This is the new blackboard pattern mode where specialists:
        1. Read findings from previous specialists
        2. Analyze the user's query in context of those findings
        3. Return their own findings (no streaming to user)

        The orchestrator will collect all findings and synthesize them.

        Args:
            blackboard: Shared state with user profile, query, and previous findings

        Returns:
            Dict of {key: value} findings to record on the blackboard.
            Example:
                {
                    "gaps": ["agentic_ai_projects", "formal_education"],
                    "target_role": "Staff Engineer",
                    "confidence": 0.85,
                    ...
                }

        Note:
            Subclasses can override this to provide custom blackboard logic.
            Default implementation will use self._build_agent() to run the agent
            with a context-aware prompt that includes previous findings.
        """
        # Default implementation: use the compiled agent with context
        return self._contribute_via_agent(blackboard)

    def _contribute_via_agent(self, blackboard: CareerBlackboard) -> SpecialistFinding:
        """Default contribution implementation using direct LLM call.

        Builds a context-aware prompt that includes:
        - The original user query
        - Findings from previous specialists (for context)

        Then calls the LLM and extracts structured findings.
        """
        from langchain_core.messages import HumanMessage, SystemMessage

        from fu7ur3pr00f.llm.fallback import get_model_with_fallback

        query = blackboard.get("query", "")
        previous_findings = blackboard.get("findings", {})

        # Build context from previous specialists
        context_msg = self._format_previous_findings(previous_findings)

        # Build full prompt with context
        full_prompt = query
        if context_msg:
            full_prompt = f"{query}\n\nContext from other specialists:\n{context_msg}"

        try:
            model, _ = get_model_with_fallback(purpose="analysis")
            result = model.invoke(
                [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=full_prompt),
                ]
            )

            return self._extract_findings({"messages": [result]}, query)

        except Exception as e:
            logger.error("Error in %s.contribute(): %s", self.name, e)
            return {
                "reasoning": f"Failed to contribute: {e}",
                "confidence": 0.0,
            }

    def _format_previous_findings(
        self, previous_findings: dict[str, SpecialistFinding]
    ) -> str:
        """Format findings from previous specialists for context (with truncation).

        Args:
            previous_findings: Dict of specialist findings

        Returns:
            Formatted string of previous findings, truncated to 4000 chars
        """
        context_parts = []

        if previous_findings:
            context_parts.append("Other specialists have found:")
            for specialist, finding in previous_findings.items():
                context_parts.append(f"\n{specialist.upper()}:")
                for key, value in finding.items():
                    if key not in ("confidence", "iteration_contributed"):
                        context_parts.append(f"  - {key}: {value}")

        context_msg = "\n".join(context_parts) if context_parts else ""
        # Truncate to 4000 chars to keep context manageable
        return context_msg[:4000]

    def _extract_findings(
        self,
        agent_result: dict[str, Any],
        query: str,
    ) -> SpecialistFinding:
        """Extract structured findings from agent response via Pydantic.

        Makes a separate, structured LLM call to extract findings in a
        reliable, typed format instead of parsing free-text output.

        Args:
            agent_result: Result dict from agent.invoke()
            query: Original user query

        Returns:
            Structured findings dict
        """
        from langchain_core.messages import HumanMessage

        from fu7ur3pr00f.agents.blackboard.findings_schema import (
            SpecialistFindingsModel,
        )
        from fu7ur3pr00f.llm.fallback import get_model_with_fallback

        # Extract the agent's final message text
        messages = agent_result.get("messages", [])
        if not messages:
            return {"reasoning": "No output from agent", "confidence": 0.50}

        last_msg = messages[-1]
        agent_text = str(getattr(last_msg, "content", str(last_msg)))[:4000]

        # Make a separate extraction call using structured output
        try:
            model, _ = get_model_with_fallback(purpose="analysis")
            extractor = model.with_structured_output(SpecialistFindingsModel)

            extraction_prompt = (
                f"Extract career findings from this specialist analysis.\n\n"
                f"Query: {query}\n\n"
                f"Specialist output:\n{agent_text}"
            )

            result: SpecialistFindingsModel = extractor.invoke(
                [HumanMessage(content=extraction_prompt)]
            )
            return result.model_dump(exclude_none=True)

        except Exception as e:
            logger.warning(
                "%s._extract_findings structured extraction failed: %s",
                self.name,
                e,
            )
            # Graceful fallback: return raw text as reasoning
            return {
                "reasoning": agent_text[:2000],
                "confidence": 0.60,
            }

    def get_compiled_agent(self) -> Any:
        """Get the compiled LangGraph agent for this specialist (cached).

        Builds on first call using:
        - create_agent() from LangChain
        - This specialist's tools and system_prompt
        - The standard middleware stack (dynamic prompt, tool repair,
          analysis synthesis, summarization)
        - Shared SqliteSaver checkpointer

        Returns:
            Compiled CompiledStateGraph ready for .stream() / .invoke()
        """
        key = type(self).__name__

        if key in _compiled_agents:
            return _compiled_agents[key]

        with _agents_lock:
            if key in _compiled_agents:
                return _compiled_agents[key]

            agent = self._build_agent()
            _compiled_agents[key] = agent
            logger.info(
                "Compiled %s specialist agent (%d tools)", self.name, len(self.tools)
            )
            return agent

    def _build_agent(self) -> Any:
        """Build the compiled LangGraph agent."""
        from langchain.agents import create_agent
        from langchain.agents.middleware.summarization import SummarizationMiddleware

        from fu7ur3pr00f.agents.middleware import (
            AnalysisSynthesisMiddleware,
            ToolCallRepairMiddleware,
            make_specialist_prompt,
        )
        from fu7ur3pr00f.llm.fallback import get_model_with_fallback
        from fu7ur3pr00f.memory.checkpointer import get_checkpointer

        model, config = get_model_with_fallback(purpose="agent")
        logger.info("%s agent using: %s", self.name, config.description)

        summary_model, _ = get_model_with_fallback(purpose="summary")

        return create_agent(
            model=model,
            tools=self.tools,
            middleware=[
                make_specialist_prompt(self.system_prompt),
                ToolCallRepairMiddleware(),
                AnalysisSynthesisMiddleware(),
                SummarizationMiddleware(
                    model=summary_model,
                    trigger=("tokens", 16000),
                    keep=("messages", 20),
                ),
            ],
            checkpointer=get_checkpointer(),
        )


def reset_all_specialists() -> None:
    """Clear all cached compiled specialist agents.

    Call after a model fallback or provider change to force recompilation
    with the new model on the next invocation.
    """
    with _agents_lock:
        _compiled_agents.clear()
    logger.info("All specialist agent caches cleared")
