import logging

from a2a.server.request_handlers.request_handler import RequestHandler
from a2a.types import Message, Part, Role, TextPart, UnsupportedOperationError
from a2a.utils.errors import ServerError

from fu7ur3pr00f.agents.blackboard.engine import get_conversation_engine

logger = logging.getLogger(__name__)


class A2AHandler(RequestHandler):
    """A2A request handler that bridges external JSON-RPC calls to the internal engine.

    Implements the RequestHandler interface; we only need the non-streaming
    message send handler for local integration tests.
    """

    async def on_message_send(self, params, context=None):
        # Attempt to extract text from either a SendMessageParams structure or a
        # simplified request shape. Be permissive because different client
        # wrappers may present slightly different objects in tests.
        text = None
        try:
            # params.message.parts -> list[Part], where Part.root may be TextPart
            if hasattr(params, "message") and params.message and params.message.parts:
                first = params.message.parts[0]
                # Use utility to handle both RootModel-wrapped Part and
                # concrete TextPart instances.
                from fu7ur3pr00f.agents.specialists.a2a_utils import (
                    extract_text_from_part,
                )

                text = extract_text_from_part(first)
        except Exception:
            text = None

        if not text:
            return Message(
                parts=[Part(root=TextPart(text="No input"))],
                role=Role.agent,
                message_id="",
                task_id=None,
            )

        try:
            engine = get_conversation_engine()
            result = engine.invoke_turn(
                query=text,
                thread_id=(
                    context
                    and getattr(context, "state", {}).get("blackboard_id")
                    or "default"
                ),
            )
            return Message(
                # SDK Part is a discriminated RootModel; construct as
                # Part(root=TextPart(...))
                parts=[Part(root=TextPart(text=str(result.synthesis)))],
                role=Role.agent,
                message_id="1",
                task_id=None,
            )
        except Exception as e:
            logger.exception("A2A handler error: %s", e)
            return Message(
                parts=[Part(root=TextPart(text=str(e)))],
                role=Role.agent,
                message_id="",
                task_id=None,
            )

    # --- Minimal implementations for other abstract methods ---
    async def on_get_task(self, params, context=None):
        return None

    async def on_cancel_task(self, params, context=None):
        return None

    def on_message_send_stream(self, params, context=None):
        # Streaming not implemented. Return an async-generator that raises
        # ServerError when iterated to indicate the operation is unsupported.
        async def _unsupported_gen():
            if False:  # pragma: no cover - generator stub
                yield None
            raise ServerError(error=UnsupportedOperationError())

        return _unsupported_gen()

    async def on_set_task_push_notification_config(self, params, context=None):
        raise ServerError(error=UnsupportedOperationError())

    async def on_get_task_push_notification_config(self, params, context=None):
        raise ServerError(error=UnsupportedOperationError())

    def on_resubscribe_to_task(self, params, context=None):
        async def _unsupported_gen():
            if False:  # pragma: no cover - generator stub
                yield None
            raise ServerError(error=UnsupportedOperationError())

        return _unsupported_gen()

    async def on_list_task_push_notification_config(self, params, context=None):
        raise ServerError(error=UnsupportedOperationError())

    async def on_delete_task_push_notification_config(self, params, context=None):
        raise ServerError(error=UnsupportedOperationError())
