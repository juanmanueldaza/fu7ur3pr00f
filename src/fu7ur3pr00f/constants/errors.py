"""Error message templates."""

ERROR_TOOL_NOT_FOUND = "Tool {name!r} not available to {agent} specialist."
ERROR_TOOL_EXECUTION = "Error running {tool}: {error}"
ERROR_KNOWLEDGE_NOT_FOUND = "No relevant career knowledge found for this query."
ERROR_KNOWLEDGE_EMPTY = "Knowledge base is empty — index career data first."
ERROR_PROFILE_NOT_CONFIGURED = (
    "No profile configured. Run /setup or /profile to add your information."
)
ERROR_PDFTOTEXT_MISSING = (
    "pdftotext is not installed. "
    "Install it with: apt install poppler-utils  /  brew install poppler"
)
