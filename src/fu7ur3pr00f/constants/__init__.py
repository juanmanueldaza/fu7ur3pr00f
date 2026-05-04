"""Project-wide constants — chunking, knowledge, and CliftonStrengths."""

from .chunking import CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS, TOKENS_PER_WORD
from .clifton import (
    CLIFTON_ALL_34_MAX_RANK,
    CLIFTON_TOP_5_MAX_RANK,
    CLIFTON_TOP_10_MAX_RANK,
)
from .knowledge import (
    INDEX_BATCH_SIZE,
    MAX_EMBEDDING_CACHE_SIZE,
    SEARCH_FETCH_MULTIPLIER,
)

# HTTP timeouts (was in timeouts.py — now inline)
HTTP_TIMEOUT = 30
HTTP_TIMEOUT_LONG = 120

__all__ = [
    "CHUNK_MAX_TOKENS",
    "CHUNK_MIN_TOKENS",
    "TOKENS_PER_WORD",
    "INDEX_BATCH_SIZE",
    "SEARCH_FETCH_MULTIPLIER",
    "MAX_EMBEDDING_CACHE_SIZE",
    "CLIFTON_TOP_5_MAX_RANK",
    "CLIFTON_TOP_10_MAX_RANK",
    "CLIFTON_ALL_34_MAX_RANK",
    "HTTP_TIMEOUT",
    "HTTP_TIMEOUT_LONG",
]
