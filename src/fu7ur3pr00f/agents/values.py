"""FutureProof values enforcement for agent responses.

This module ensures all agent responses align with FutureProof's core values:
- Free software freedom
- Open source collaboration
- Developer sovereignty
- Ethical technology
- Work-life harmony

Example:
    >>> from fu7ur3pr00f.agents.values import apply_values_filter, VALUES_PROMPT
    >>> response = "Take the job, it pays 20% more!"
    >>> filtered = apply_values_filter(
    ...     response,
    ...     context={"company_uses_proprietary": True}
    ... )
    >>> print(filtered)
    'The salary is higher, but consider: this company uses proprietary software...'
"""

from dataclasses import dataclass
from typing import Any

from fu7ur3pr00f.prompts import load_prompt


@dataclass
class ValuesContext:
    """Context for values-based filtering.

    Attributes:
        company_uses_proprietary: Does company use proprietary software?
        company_contributes_to_oss: Does company contribute to open source?
        product_respects_freedom: Does product respect user freedom?
        work_is_ethical: Is the work ethical (no surveillance/manipulation)?
        has_work_life_balance: Does company respect work-life balance?
        is_remote_friendly: Is remote work available?
        fair_compensation: Is compensation fair?
        crunch_expected: Is crunch/overtime expected?

    Example:
        >>> ctx = ValuesContext(
        ...     company_uses_proprietary=True,
        ...     product_respects_freedom=False,
        ...     crunch_expected=True
        ... )
        >>> ctx.has_red_flags()
        True
    """

    company_uses_proprietary: bool = False
    company_contributes_to_oss: bool = False
    product_respects_freedom: bool = True
    work_is_ethical: bool = True
    has_work_life_balance: bool = True
    is_remote_friendly: bool = False
    fair_compensation: bool = True
    crunch_expected: bool = False

    def has_red_flags(self) -> bool:
        """Check if opportunity has ethical red flags.

        Returns:
            True if any critical red flags present

        Example:
            >>> ctx = ValuesContext(
            ...     work_is_ethical=False,
            ...     crunch_expected=True
            ... )
            >>> ctx.has_red_flags()
            True
        """
        return (
            not self.work_is_ethical
            or not self.product_respects_freedom
            or self.crunch_expected
        )

    def has_green_flags(self) -> bool:
        """Check if opportunity has ethical green flags.

        Returns:
            True if multiple green flags present

        Example:
            >>> ctx = ValuesContext(
            ...     company_contributes_to_oss=True,
            ...     is_remote_friendly=True,
            ...     has_work_life_balance=True
            ... )
            >>> ctx.has_green_flags()
            True
        """
        green_count = sum(
            [
                self.company_contributes_to_oss,
                self.product_respects_freedom,
                self.work_is_ethical,
                self.has_work_life_balance,
                self.is_remote_friendly,
                self.fair_compensation,
            ]
        )
        return green_count >= 4


# Core values prompt template for all agents
VALUES_PROMPT = load_prompt("values")

# Values-based response templates
RED_FLAG_RESPONSE = load_prompt("values_red_flag")
GREEN_FLAG_RESPONSE = load_prompt("values_green_flag")
MIXED_FLAG_RESPONSE = load_prompt("values_mixed_flag")


def apply_values_filter(  # noqa: C901 TODO: refactor
    response: str,
    context: ValuesContext | dict[str, bool] | None = None,
    include_values_reminder: bool = True,
) -> str:
    """Apply values-based filtering to agent response.

    Disabled by default. Enable via VALUES_FILTER_ENABLED=true in .env.

    Analyzes the context and modifies response to highlight ethical concerns
    or praise value-aligned opportunities.

    Args:
        response: Original agent response
        context: Values context (dict or ValuesContext)
        include_values_reminder: Whether to include values reminder

    Returns:
        Filtered response with values-aware messaging
    """
    # Opt-in: return unchanged unless explicitly enabled
    from fu7ur3pr00f.config import settings

    if not settings.values_filter_enabled:
        return response

    # Convert dict to ValuesContext if needed
    if isinstance(context, dict):
        ctx = ValuesContext(**context)
    elif context is None:
        ctx = ValuesContext()
    else:
        ctx = context

    # If no red flags and response doesn't need modification, return as-is
    if not ctx.has_red_flags() and not ctx.has_green_flags():
        return response

    # Build red flags list
    red_flags: list[str] = []
    if ctx.company_uses_proprietary:
        red_flags.append("❌ Company uses proprietary software (restricts user freedom)")
    if not ctx.product_respects_freedom:
        red_flags.append("❌ Product may not respect user freedom")
    if not ctx.work_is_ethical:
        red_flags.append("❌ Work may involve unethical practices")
    if ctx.crunch_expected:
        red_flags.append("❌ Crunch culture / long hours expected")

    # Build green flags list
    green_flags: list[str] = []
    if ctx.company_contributes_to_oss:
        green_flags.append("✅ Company contributes to open source")
    if ctx.product_respects_freedom:
        green_flags.append("✅ Product respects user freedom")
    if ctx.work_is_ethical:
        green_flags.append("✅ Ethical business model")
    if ctx.has_work_life_balance:
        green_flags.append("✅ Work-life balance respected")
    if ctx.is_remote_friendly:
        green_flags.append("✅ Remote-friendly")
    if ctx.fair_compensation:
        green_flags.append("✅ Fair compensation")

    # Choose appropriate template
    if red_flags and green_flags:
        template = MIXED_FLAG_RESPONSE
    elif red_flags:
        template = RED_FLAG_RESPONSE
    elif green_flags:
        template = GREEN_FLAG_RESPONSE
    else:
        return response

    # Format response
    filtered = template.format(
        red_flags="\n".join(red_flags) if red_flags else "None identified",
        green_flags="\n".join(green_flags) if green_flags else "None identified",
        alternatives=(
            "- Look for OSS-contributing companies\n"
            "- Seek remote-first, values-aligned startups"
        ),
    )

    # Append original response if it adds value
    if response.strip():
        filtered = f"{response}\n\n{filtered}"

    return filtered


def check_opportunity_alignment(
    company_name: str,
    job_description: str,
    user_values: list[str] | None = None,
) -> dict[str, Any]:
    """Check how well an opportunity aligns with user values.

    Args:
        company_name: Company name
        job_description: Job description text
        user_values: User's prioritized values (default: FutureProof defaults)

    Returns:
        Dict with alignment score and breakdown

    Example:
        >>> result = check_opportunity_alignment(
        ...     company_name="Red Hat",
        ...     job_description="Senior Python Developer...",
        ...     user_values=["open_source", "remote", "work_life_balance"]
        ... )
        >>> print(result["score"])
        85
        >>> print(result["breakdown"])
        {'open_source': 100, 'remote': 80, 'work_life_balance': 75}
    """
    # Default user values if not specified
    if user_values is None:
        user_values = [
            "free_software",
            "open_source",
            "remote_friendly",
            "work_life_balance",
            "ethical",
        ]

    # Keywords for each value
    value_keywords = {
        "free_software": ["free software", "gnu", "gpl", "freedom", "libre"],
        "open_source": [
            "open source",
            "oss",
            "github",
            "contributions",
            "apache",
            "mit",
        ],
        "remote_friendly": ["remote", "distributed", "work from home", "flexible"],
        "work_life_balance": ["work-life", "balance", "flexible hours", "no crunch"],
        "ethical": ["ethical", "privacy", "user-focused", "transparent"],
        "fair_compensation": ["equity", "stock options", "competitive", "fair"],
    }

    # Score each value
    breakdown: dict[str, int] = {}
    job_text = (company_name + " " + job_description).lower()

    for value, keywords in value_keywords.items():
        matches = sum(1 for kw in keywords if kw in job_text)
        score = min(100, matches * 25)  # Max 100 per value
        breakdown[value] = score

    # Calculate overall score (weighted by user priorities)
    total_score = 0
    weight_sum = 0

    for i, value in enumerate(user_values):
        weight = len(user_values) - i  # Higher weight for earlier values
        total_score += breakdown.get(value, 50) * weight
        weight_sum += weight

    overall_score = round(total_score / weight_sum) if weight_sum > 0 else 50

    return {
        "score": overall_score,
        "breakdown": breakdown,
        "recommendation": _get_recommendation(overall_score),
    }


def _get_recommendation(score: int) -> str:
    """Get recommendation based on alignment score.

    Args:
        score: Overall alignment score (0-100)

    Returns:
        Recommendation string
    """
    if score >= 80:
        return "Strong alignment with your values. Highly recommended."
    elif score >= 60:
        return "Good alignment with some trade-offs. Worth considering."
    elif score >= 40:
        return "Mixed alignment. Carefully weigh the trade-offs."
    else:
        return "Poor alignment. Consider alternatives that better match your values."


# Export public API
__all__ = [
    "ValuesContext",
    "VALUES_PROMPT",
    "apply_values_filter",
    "check_opportunity_alignment",
]
