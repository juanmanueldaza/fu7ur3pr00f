"""Pydantic schema for LLM-based specialist routing decisions."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

_VALID_SPECIALISTS = frozenset({"coach", "jobs", "learning", "code", "founder"})


class RoutingDecision(BaseModel):
    """Structured routing output from the LLM router."""

    model_config = ConfigDict(extra="forbid")

    specialists: list[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description=(
            "Specialist names to handle this query. "
            "Valid values: coach, jobs, learning, code, founder."
        ),
    )
    reasoning: str = Field(
        default="",
        max_length=200,
        description="Brief explanation of routing decision",
    )

    @field_validator("specialists")
    @classmethod
    def validate_specialist_names(cls, v: list[str]) -> list[str]:
        """Reject any name not in the known specialist set."""
        invalid = [name for name in v if name not in _VALID_SPECIALISTS]
        if invalid:
            raise ValueError(f"Unknown specialist(s): {invalid}")
        return v


__all__ = ["RoutingDecision"]
