from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class A2AMessageRequest(BaseModel):
    """A2A standardized request for sending a message to an agent."""

    jsonrpc: str = "2.0"
    method: str = "message/send"
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contains 'text' (the message) and optional 'context'.",
    )
    id: str


class A2AMessageResponse(BaseModel):
    """A2A standardized response from an agent."""

    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: str


class A2AContext(BaseModel):
    """Context passed between agents in an A2A session."""

    blackboard_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
