from typing import Any

from a2a.types import TextPart


def extract_text_from_part(part: Any) -> str | None:
    """Extract text from an a2a.types.Part or TextPart-like object.

    The A2A SDK sometimes wraps concrete parts inside a RootModel with a
    .root attribute. Accept both shapes and return the contained text or None.
    """
    if part is None:
        return None

    # Direct TextPart instance
    if isinstance(part, TextPart):
        return getattr(part, "text", None)

    # Wrapped Part with .root
    root = getattr(part, "root", None)
    if root is not None and isinstance(root, TextPart):
        return getattr(root, "text", None)

    # Fallback: try common attribute names
    return getattr(part, "text", None)
