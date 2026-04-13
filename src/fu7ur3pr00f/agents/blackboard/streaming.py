"""ContextVar for synthesis token streaming across thread boundaries."""

from collections.abc import Callable
from contextvars import ContextVar

synthesis_token_callback: ContextVar[Callable[[str], None] | None] = ContextVar(
    "synthesis_token_callback", default=None
)

__all__ = ["synthesis_token_callback"]
