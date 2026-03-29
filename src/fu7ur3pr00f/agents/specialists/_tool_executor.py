"""Tool execution engine for specialist agents.

Extracts tool execution logic from BaseAgent to improve testability
and reduce coupling.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import ToolMessage
from langgraph.errors import GraphInterrupt as _GraphInterrupt

from fu7ur3pr00f.constants import (
    ERROR_TOOL_EXECUTION,
    ERROR_TOOL_NOT_FOUND,
    TOOL_RESULT_MAX_CHARS,
    TOOL_RESULT_PREVIEW_CHARS,
)

logger = logging.getLogger(__name__)

_CACHEABLE_TOOLS: frozenset[str] = frozenset(
    {
        "get_user_profile",
        "search_career_knowledge",
        "get_github_profile",
        "search_github_repos",
        "search_gitlab_projects",
    }
)


@dataclass
class ToolExecutionResult:
    """Result of executing tool calls."""

    tool_call_count: int
    cache_updated: dict[str, str]


class ToolExecutor:
    """Executes tool calls and manages caching."""

    def __init__(self, specialist_name: str, tool_map: dict[str, Any]):
        self.specialist_name = specialist_name
        self.tool_map = tool_map

    def execute_calls(
        self,
        tool_calls: list,
        messages: list,
        tool_cache: dict[str, str],
        stream_writer: Any = None,
    ) -> ToolExecutionResult:
        """Execute a batch of tool calls.

        Args:
            tool_calls: List of tool call dicts from LLM response
            messages: Message list to append results to
            tool_cache: Cache for idempotent tool results
            stream_writer: Optional stream writer for events

        Returns:
            ToolExecutionResult with count and updated cache
        """
        count = len(tool_calls)
        for tc in tool_calls:
            self._execute_single(
                tc["name"],
                tc.get("args", {}),
                tc["id"],
                messages,
                tool_cache,
                stream_writer,
            )
        return ToolExecutionResult(count, tool_cache)

    def _execute_single(
        self,
        tool_name: str,
        tool_args: dict,
        tool_id: str,
        messages: list,
        tool_cache: dict[str, str],
        stream_writer: Any,
    ) -> None:
        """Execute a single tool call with caching."""
        cache_key = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"

        # Check cache
        if tool_name in _CACHEABLE_TOOLS and cache_key in tool_cache:
            logger.debug(
                "%s: cache hit for %s(%r), skipping re-fetch",
                self.specialist_name,
                tool_name,
                tool_args,
            )
            messages.append(
                ToolMessage(content=tool_cache[cache_key], tool_call_id=tool_id)
            )
            return

        if stream_writer:
            stream_writer(
                {
                    "type": "tool_start",
                    "specialist": self.specialist_name,
                    "tool": tool_name,
                    "args": tool_args,
                }
            )

        result_str = self._invoke_tool(tool_name, tool_args)

        if stream_writer:
            stream_writer(
                {
                    "type": "tool_result",
                    "specialist": self.specialist_name,
                    "tool": tool_name,
                    "result": result_str[:TOOL_RESULT_PREVIEW_CHARS],
                }
            )

        # Update cache
        if tool_name in _CACHEABLE_TOOLS:
            tool_cache[cache_key] = result_str

        messages.append(ToolMessage(content=result_str, tool_call_id=tool_id))

    def _invoke_tool(self, tool_name: str, tool_args: dict) -> str:
        """Invoke a tool and return result string."""
        tool_fn = self.tool_map.get(tool_name)
        if tool_fn is None:
            logger.warning("%s: tool not found: %s", self.specialist_name, tool_name)
            return ERROR_TOOL_NOT_FOUND.format(
                name=tool_name, agent=self.specialist_name
            )

        try:
            result = tool_fn.invoke(tool_args)
            return str(result)[:TOOL_RESULT_MAX_CHARS]
        except _GraphInterrupt:
            raise
        except Exception as e:
            logger.warning(
                "%s: tool error (%s): %s", self.specialist_name, tool_name, e
            )
            return ERROR_TOOL_EXECUTION.format(tool=tool_name, error=e)
