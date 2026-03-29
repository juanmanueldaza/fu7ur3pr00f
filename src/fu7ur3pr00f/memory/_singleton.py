"""Singleton pattern helper for memory stores."""

import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def create_singleton(  # noqa: UP047
    factory: Callable[[], T],
    lock: threading.Lock | None = None,
) -> Callable[[], T]:
    """Create a thread-safe singleton getter.

    Args:
        factory: Function that creates the singleton instance
        lock: Optional lock for thread safety (created if not provided)

    Returns:
        Function that returns the singleton instance

    Usage:
        _store_lock = threading.Lock()
        get_store = create_singleton(lambda: MyStore(), _store_lock)
    """
    _instance: T | None = None
    _lock = lock or threading.Lock()

    def getter() -> T:
        nonlocal _instance
        if _instance is not None:
            return _instance

        with _lock:
            if _instance is not None:
                return _instance
            _instance = factory()
            return _instance

    return getter
