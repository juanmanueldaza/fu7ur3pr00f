"""Project-wide constants.

Backwards-compatible facade that re-exports all constants from logical
sub-modules.  New code should import directly from the sub-module that
owns the constant (e.g. ``from fu7ur3pr00f.constants.urls import GITHUB_API_BASE``).

Existing import sites continue to work unchanged:
    from fu7ur3pr00f.constants import GITHUB_API_BASE, MAX_TOOL_ROUNDS
"""

from .chunking import CHUNK_MAX_TOKENS, CHUNK_MIN_TOKENS, TOKENS_PER_WORD
from .clifton import (
    CLIFTON_ALL_34_MAX_RANK,
    CLIFTON_TOP_5_MAX_RANK,
    CLIFTON_TOP_10_MAX_RANK,
)
from .errors import (
    ERROR_KNOWLEDGE_EMPTY,
    ERROR_KNOWLEDGE_NOT_FOUND,
    ERROR_PDFTOTEXT_MISSING,
    ERROR_PROFILE_NOT_CONFIGURED,
    ERROR_TOOL_EXECUTION,
    ERROR_TOOL_NOT_FOUND,
)
from .knowledge import (
    INDEX_BATCH_SIZE,
    MAX_EMBEDDING_CACHE_SIZE,
    SEARCH_FETCH_MULTIPLIER,
)
from .llm import ANALYSIS_MARKER, CAREER_CONTEXT_MAX_CHARS
from .status import STATUS_COMPLETE, STATUS_ERROR, STATUS_SUCCESS, STATUS_WORKING
from .timeouts import HTTP_TIMEOUT, HTTP_TIMEOUT_LONG
from .tools import (
    MAX_TOOL_ROUNDS,
    MAX_TOTAL_TOOL_CALLS,
    TOOL_RESULT_MAX_CHARS,
    TOOL_RESULT_PREVIEW_CHARS,
)
from .ui import COLOR_ACCENT, COLOR_ERROR, COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING
from .urls import (
    DEVTO_API_BASE,
    FOREX_API_BASE,
    GITHUB_API_BASE,
    HIMALAYAS_API_BASE,
    HN_API_BASE,
    HN_BASE_URL,
    JOBICY_API_BASE,
    JOBICY_RSS_URL,
    PPP_API_BASE,
    REMOTEOK_API_BASE,
    REMOTIVE_API_BASE,
    STACKOVERFLOW_API_BASE,
    TAVILY_API_BASE,
    WEREMOTE_BASE,
    WEREMOTE_FEEDS,
)

__all__ = [
    # tools
    "TOOL_RESULT_MAX_CHARS",
    "TOOL_RESULT_PREVIEW_CHARS",
    "MAX_TOOL_ROUNDS",
    "MAX_TOTAL_TOOL_CALLS",
    # llm
    "ANALYSIS_MARKER",
    "CAREER_CONTEXT_MAX_CHARS",
    # chunking
    "CHUNK_MAX_TOKENS",
    "CHUNK_MIN_TOKENS",
    "TOKENS_PER_WORD",
    # knowledge
    "INDEX_BATCH_SIZE",
    "SEARCH_FETCH_MULTIPLIER",
    "MAX_EMBEDDING_CACHE_SIZE",
    # timeouts
    "HTTP_TIMEOUT",
    "HTTP_TIMEOUT_LONG",
    # clifton
    "CLIFTON_TOP_5_MAX_RANK",
    "CLIFTON_TOP_10_MAX_RANK",
    "CLIFTON_ALL_34_MAX_RANK",
    # urls
    "GITHUB_API_BASE",
    "HN_API_BASE",
    "HN_BASE_URL",
    "DEVTO_API_BASE",
    "STACKOVERFLOW_API_BASE",
    "FOREX_API_BASE",
    "PPP_API_BASE",
    "TAVILY_API_BASE",
    "REMOTEOK_API_BASE",
    "HIMALAYAS_API_BASE",
    "REMOTIVE_API_BASE",
    "JOBICY_API_BASE",
    "JOBICY_RSS_URL",
    "WEREMOTE_BASE",
    "WEREMOTE_FEEDS",
    # errors
    "ERROR_TOOL_NOT_FOUND",
    "ERROR_TOOL_EXECUTION",
    "ERROR_KNOWLEDGE_NOT_FOUND",
    "ERROR_KNOWLEDGE_EMPTY",
    "ERROR_PROFILE_NOT_CONFIGURED",
    "ERROR_PDFTOTEXT_MISSING",
    # status
    "STATUS_SUCCESS",
    "STATUS_ERROR",
    "STATUS_WORKING",
    "STATUS_COMPLETE",
    # ui
    "COLOR_SUCCESS",
    "COLOR_WARNING",
    "COLOR_ERROR",
    "COLOR_INFO",
    "COLOR_ACCENT",
]
