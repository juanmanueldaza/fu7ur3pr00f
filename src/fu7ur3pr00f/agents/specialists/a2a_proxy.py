import asyncio
import logging
from typing import Any

from a2a.client.client_factory import ClientFactory
from a2a.client.middleware import ClientCallContext
from a2a.types import Message, Part, Role, TextPart

from fu7ur3pr00f.agents.blackboard.blackboard import SpecialistFinding
from fu7ur3pr00f.agents.specialists.a2a_interceptors import PreaAuthInterceptor
from fu7ur3pr00f.agents.specialists.base import BaseAgent

logger = logging.getLogger(__name__)


class A2AProxyAgent(BaseAgent):
    """Proxy specialist that routes queries to an external A2A agent (e.g. PREA)."""

    def __init__(
        self,
        endpoint: str = "https://prea.fu7ur3pr00f.dev/api/a2a",
    ) -> None:
        self._endpoint = endpoint

    @property
    def name(self) -> str:
        return "prea_proxy"

    @property
    def description(self) -> str:
        return "External A2A agent for specialized career intelligence"

    @property
    def system_prompt(self) -> str:
        return "Proxy to PREA A2A agent; route queries to the remote endpoint."

    @property
    def tools(self) -> list:
        """No local tools for the proxy agent."""
        return []

    def contribute(
        self,
        blackboard: Any,
        stream_writer: Any = None,
    ) -> SpecialistFinding:
        """Contribute to the blackboard by calling the remote A2A agent.

        Args:
            blackboard: Shared state with query and context.
            stream_writer: Optional stream writer for real-time events.

        Returns:
            SpecialistFinding containing the remote agent's synthesis.
        """
        query = blackboard.get("query", "")
        # A2A Context preparation
        context = ClientCallContext(
            state={
                "blackboard_id": blackboard.get("_session_id", "default"),
                "user_id": blackboard.get("user_profile", {}).get("user_id", "unknown"),
            },
        )

        try:
            # Run the async client call in a sync wrapper
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio

                nest_asyncio.apply()
                response_text = loop.run_until_complete(
                    self._send_a2a_message(query, context)
                )
            else:
                response_text = asyncio.run(self._send_a2a_message(query, context))

            return {
                "reasoning": response_text,
                "confidence": 0.9,
            }
        except Exception as e:
            logger.exception("A2A Proxy contribution failed: %s", e)
            return {
                "reasoning": f"External agent error: {e}",
                "confidence": 0.0,
            }

    async def _send_a2a_message(self, query: str, context: ClientCallContext) -> str:
        """Async helper to send the A2A message and aggregate the result."""
        client = await ClientFactory.connect(
            self._endpoint,
            interceptors=[PreaAuthInterceptor()],
        )

        # Use the Message type from a2a.types
        # Wrap TextPart in Part(root=...) to satisfy SDK typing (Part is a RootModel)
        request = Message(
            parts=[Part(root=TextPart(text=query))],
            role=Role.user,
            message_id=str(asyncio.get_event_loop().time()),  # Simple ID
            task_id=None,
        )

        response_text = ""
        # client.send_message may either be an async function that returns an
        # async iterator (test mocks do this) or return an async iterator
        # directly. Normalize both cases by awaiting only if the result is
        # awaitable, then iterate asynchronously.
        import inspect

        result = client.send_message(request, context=context)
        if inspect.isawaitable(result):
            result = await result

        from fu7ur3pr00f.agents.specialists.a2a_utils import extract_text_from_part

        async for event in result:
            if isinstance(event, Message):
                for part in event.parts:
                    text_val = extract_text_from_part(part)
                    if text_val:
                        response_text += text_val

        return response_text or "No response from external agent."
