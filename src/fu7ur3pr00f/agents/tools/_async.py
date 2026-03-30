"""Shared async helper for running coroutines from sync tool contexts."""

import asyncio
import concurrent.futures
from collections.abc import Callable
from typing import Any


def run_async(coro: Any) -> Any:
    """Run an async coroutine from a sync context (ToolNode thread pool).

    Handles the case where an event loop is already running by spawning
    a new thread with its own loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def run_async_call(factory: Callable[..., Any], /, *args: Any, **kwargs: Any) -> Any:
    """Create and run a coroutine lazily.

    Avoids leaking unawaited coroutine objects when callers patch or stub the
    async runner in tests or short-circuit execution before awaiting.
    """
    return run_async(factory(*args, **kwargs))
