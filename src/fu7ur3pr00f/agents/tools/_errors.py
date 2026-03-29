"""Shared error handling for agent tools.

Provides standardized error handling patterns to eliminate
repeated try/except blocks across tool implementations.

Usage:
    from fu7ur3pr00f.agents.tools._errors import handle_tool_error

    @tool
    def my_tool(arg: str) -> str:
        return handle_tool_error(
            lambda: do_something(arg),
            error_noun="process data",
        )
"""

import logging
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def handle_tool_error(
    action_fn: Callable[[], T],
    error_noun: str,
    fallback: T | None = None,
) -> T | str:
    """Execute tool action with standardized error handling.

    Catches exceptions, logs them, and returns user-friendly error message.

    Args:
        action_fn: Callable that performs the tool action
        error_noun: Noun describing what failed (e.g., "analyze skill gaps")
        fallback: Optional fallback value on error (if None, returns error string)

    Returns:
        Tool result on success, error string or fallback on failure

    Example:
        >>> result = handle_tool_error(
        ...     lambda: analyze_something(data),
        ...     error_noun="analyze data"
        ... )
        >>> # On error: "Could not analyze data: ValueError. Check logs for details."
    """
    try:
        return action_fn()
    except Exception as e:
        logger.exception("Error during %s", error_noun)
        if fallback is not None:
            return fallback
        return (
            f"Could not {error_noun}: {type(e).__name__}. "
            f"Check logs for details."
        )


def handle_async_tool_error(
    action_fn: Callable[[], T],
    error_noun: str,
    fallback: T | None = None,
) -> Callable[[], T | str]:
    """Execute async tool action with standardized error handling.

    Wrapper for async functions — returns coroutine that handles errors.

    Args:
        action_fn: Async callable that performs the tool action
        error_noun: Noun describing what failed
        fallback: Optional fallback value on error

    Returns:
        Async function that resolves to tool result or error string

    Example:
        >>> result = await handle_async_tool_error(
        ...     lambda: fetch_something(url),
        ...     error_noun="fetch data"
        ... )
    """

    async def _wrapper() -> T | str:
        try:
            # Type ignore: action_fn returns T, but we know it's awaitable
            return await action_fn()  # type: ignore[misc]
        except Exception as e:
            logger.exception("Error during %s", error_noun)
            if fallback is not None:
                return fallback
            return (
                f"Could not {error_noun}: {type(e).__name__}. "
                f"Check logs for details."
            )

    return _wrapper()  # type: ignore[return-value]
