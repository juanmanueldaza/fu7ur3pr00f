"""Pydantic schema for structured specialist findings."""

from typing import Any

from pydantic import BaseModel, Field


class SpecialistFindingsModel(BaseModel):
    """Structured extraction of specialist findings from agent output."""

    gaps: list[str] = Field(default_factory=list)
    """Skill or knowledge gaps identified."""

    opportunities: list[str] = Field(default_factory=list)
    """Career opportunities identified."""

    skills: list[str] = Field(default_factory=list)
    """Relevant skills identified or recommended."""

    roles: list[str] = Field(default_factory=list)
    """Target roles or career paths identified."""

    timeline: str = ""
    """Recommended timeline for goals or transitions."""

    reasoning: str = ""
    """Specialist's reasoning and analysis."""

    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    """Confidence score (0.0-1.0) for these findings."""

    extra: dict[str, Any] = Field(default_factory=dict)
    """Specialist-specific extra fields."""
