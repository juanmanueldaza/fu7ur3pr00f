"""LLM context limits and behaviour markers."""

ANALYSIS_MARKER = (
    "[Detailed analysis is displayed directly to the user. "
    "Do not repeat or summarize it. Instead: reference salary data, "
    "ask about current compensation if unknown, and suggest "
    "1-2 concrete next steps.]"
)
CAREER_CONTEXT_MAX_CHARS = 4000
