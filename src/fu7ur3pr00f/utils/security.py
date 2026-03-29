"""Security utilities for PII protection and secure file operations.

This module provides career data anonymization before sending data to external LLMs,
secure file I/O (no TOCTOU), and prompt boundary sanitization.

PII Patterns Covered:
- Emails (personal and professional)
- Phone numbers (US + international formats)
- Physical addresses (US and international)
- SSN, IBAN, bank accounts
- Passport and driver's license numbers
- Social media profile URLs
- Dates of birth
"""

import contextlib
import os
import re
from collections.abc import Generator
from pathlib import Path
from typing import IO, Any

# =============================================================================
# File Validation
# =============================================================================


def validate_file_size(
    path: Path | str,
    max_size: int,
    label: str = "File",
) -> int:
    """Validate file size against limit.

    Args:
        path: File path to validate
        max_size: Maximum allowed size in bytes
        label: Human-readable label for error messages

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If file exceeds maximum size
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{label} not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"{label} is not a regular file: {file_path}")

    file_size = file_path.stat().st_size
    if file_size > max_size:
        raise ValueError(
            f"{label} too large: {file_size / 1024 / 1024:.1f}MB "
            f"(max {max_size / 1024 / 1024:.0f}MB)"
        )
    return file_size

# =============================================================================
# PII Detection Patterns
# =============================================================================

# Email patterns
_EMAIL_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b"
)

# Phone patterns - comprehensive international coverage
# US/Canada: +1 (555) 123-4567, 555-123-4567, 5551234567
# International: +XX XXX XXXXXXXX, +XX-XXX-XXXXXXX
# European: +XX XXXX XXXXXX, XX/XXXX/XXXXXX
_PHONE_PATTERNS = [
    # US/Canada formats
    re.compile(r"\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
    # International with country code (2-3 digits)
    re.compile(r"\+?[0-9]{1,3}[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{2,4}\b"),
    # European format with slashes
    re.compile(r"\+?[0-9]{1,3}/[0-9]{2,4}/[0-9]{3,6}\b"),
    # Simple international (10+ digits with optional +)
    re.compile(r"\+?[0-9]{10,15}\b"),
]

# Physical address patterns
_ADDRESS_WITH_UNIT = re.compile(
    r"\b\d{1,5}\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)\.?(?:\s*,?\s*(?:Apt|Suite|Unit|#)\.?\s*\w+)\b",  # noqa: E501
    flags=re.IGNORECASE,
)

_ADDRESS_WITHOUT_UNIT = re.compile(
    r"\b\d{1,5}\s+[\w\s]{1,40}"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl)"  # noqa: E501
    r"\.?(?!\s*,?\s*(?:Apt|Suite|Unit|#))",
    flags=re.IGNORECASE,
)

# Social media profile URLs
_SOCIAL_MEDIA_PATTERN = re.compile(
    r"(https?://(?:www\.)?(?:linkedin|github|gitlab|twitter|x)\.com/(?:in/)?)[a-zA-Z0-9._-]+",  # noqa: E501
    flags=re.IGNORECASE,
)

# SSN (US Social Security Number)
_SSN_PATTERN = re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b")

# Date of birth (labeled only)
_DOB_PATTERN = re.compile(
    r"\b(?:DOB|Date of Birth|Born|Birthday)[:\s]+\S+(?:[,\s]+\d{1,2}[,\s]+\d{4})?",
    flags=re.IGNORECASE,
)

# IBAN (International Bank Account Number) - up to 34 alphanumeric chars
_IBAN_PATTERN = re.compile(
    r"\b[A-Z]{2}\d{2}\s?[A-Z0-9]{4}\s?[A-Z0-9]{4}\s?[A-Z0-9]{4}\s?[A-Z0-9]{4}\s?[A-Z0-9]{0,14}\b"  # noqa: E501
)

# Bank account numbers (US routing + account)
_BANK_ACCOUNT_PATTERN = re.compile(
    r"\b\d{9}[-\s]?\d{4,17}\b"  # 9-digit routing + 4-17 digit account
)

# Passport numbers (various formats)
_PASSPORT_PATTERNS = [
    re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"),  # US-style: 1-2 letters + 6-9 digits
    re.compile(r"\b\d[A-Z0-9]{7,9}\b"),  # International: letter + 7-9 alphanumeric
]

# Driver's license patterns (US states vary widely)
_DRIVERS_LICENSE_PATTERNS = [
    re.compile(r"\b[A-Z]{1,2}\d{5,7}\b"),  # Common format
    re.compile(r"\b\d{8,10}\b"),  # Numeric-only states
]


def anonymize_career_data(data: str, preserve_professional_emails: bool = False) -> str:
    """Anonymize career data while preserving professional context.

    This is a specialized anonymization for career/CV data that:
    - Removes personal contact info (phone, personal email)
    - Optionally preserves work email domains for context
    - Keeps professional information (company names, job titles, etc.)
    - Removes bank account info, IBAN, passport, driver's license numbers

    Args:
        data: Career data text (markdown or plain text)
        preserve_professional_emails: If True, replaces only the local part
                                     of work emails (e.g., [USER]@company.com)

    Returns:
        Anonymized career data
    """
    result = data

    # Emails (personal or professional)
    if preserve_professional_emails:
        # Replace local part but keep domain for professional emails
        # e.g., john.doe@company.com -> [USER]@company.com
        result = _EMAIL_PATTERN.sub(r"[USER]@\2", result)
    else:
        # Full email anonymization
        result = _EMAIL_PATTERN.sub("[EMAIL]", result)

    # Phone numbers (all international formats)
    for pattern in _PHONE_PATTERNS:
        result = pattern.sub("[PHONE]", result)

    # Physical addresses with apartment/unit numbers
    result = _ADDRESS_WITH_UNIT.sub("[HOME_ADDRESS]", result)

    # Social media profile URLs with usernames (preserve platform name)
    result = _SOCIAL_MEDIA_PATTERN.sub(r"\1[USERNAME]", result)

    # SSN (US Social Security Number)
    result = _SSN_PATTERN.sub("[SSN]", result)

    # Date of birth (only labeled — bare dates preserved as they may be employment
    # dates)
    result = _DOB_PATTERN.sub("[DOB]", result)

    # Street addresses without apartment/unit
    result = _ADDRESS_WITHOUT_UNIT.sub("[ADDRESS]", result)

    # IBAN (International Bank Account Numbers)
    result = _IBAN_PATTERN.sub("[IBAN]", result)

    # Bank account numbers
    result = _BANK_ACCOUNT_PATTERN.sub("[BANK_ACCOUNT]", result)

    # Passport numbers
    for pattern in _PASSPORT_PATTERNS:
        result = pattern.sub("[PASSPORT]", result)

    # Driver's license numbers
    for pattern in _DRIVERS_LICENSE_PATTERNS:
        result = pattern.sub("[DRIVERS_LICENSE]", result)

    return result


@contextlib.contextmanager
def secure_open(
    path: str | Path,
    mode: str = "w",
    *,
    file_mode: int = 0o600,
) -> Generator[IO[Any]]:
    """Open file for writing with atomic restrictive permissions.

    Uses ``os.open()`` so the file is *never* world-readable, even for a
    microsecond (no TOCTOU window between create and chmod).

    Args:
        path: File path to open.
        mode: Python file mode (e.g. ``"w"``, ``"wb"``).
        file_mode: Unix permission bits (default ``0o600``).
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(path), flags, file_mode)
    os.fchmod(fd, file_mode)  # Also update perms on existing files
    try:
        with os.fdopen(fd, mode) as f:
            yield f
    except BaseException:
        # fd is already closed by fdopen on success; only close on error
        # if fdopen itself failed before taking ownership
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def secure_mkdir(path: str | Path, *, mode: int = 0o700) -> Path:
    """Create directory with restrictive permissions.

    Args:
        path: Directory to create (parents created as needed).
        mode: Unix permission bits (default ``0o700``).

    Returns:
        The directory path.
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    p.chmod(mode)
    return p


def sanitize_for_prompt(text: str) -> str:
    """Escape closing XML tags that could break prompt data boundaries.

    Prevents injected content from closing ``<career_data>``,
    ``<tool_results>``, or similar XML-style boundary markers used in
    system prompts.

    Args:
        text: Raw text to sanitize.

    Returns:
        Text with closing XML tags escaped (``</tag>`` → ``<\\/tag>``).
    """
    return re.sub(r"</([\w_]+)>", r"<\\/\1>", text)


# Patterns that might leak API keys or tokens in error messages
_SECRET_PATTERNS = [
    re.compile(r"(sk-(?:ant-)?[A-Za-z0-9]{8})[A-Za-z0-9-]+"),  # OpenAI/Anthropic
    re.compile(r"(AIza[A-Za-z0-9]{8})[A-Za-z0-9_-]+"),  # Google
    re.compile(r"(Bearer\s+)[^\s\"']+", re.IGNORECASE),  # Bearer tokens
]


def sanitize_error(msg: str) -> str:
    """Redact known secret patterns from error messages.

    Covers API keys from OpenAI, Anthropic, Google, and bearer tokens to
    prevent credential leakage in logs or user-facing error messages.

    Args:
        msg: Error message that may contain secrets.

    Returns:
        Error message with secrets redacted.
    """
    for pattern in _SECRET_PATTERNS:
        msg = pattern.sub(r"\1...", msg)
    return msg


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask a secret value, showing only leading/trailing characters.

    Args:
        value: The secret string to mask.
        visible_chars: Number of characters to keep visible at both ends.

    Returns:
        Masked string (e.g. "sk-a...5678").
    """
    if not value:
        return ""
    if len(value) <= (visible_chars * 2 + 2):
        return "*" * len(value)
    return value[:visible_chars] + "..." + value[-visible_chars:]
