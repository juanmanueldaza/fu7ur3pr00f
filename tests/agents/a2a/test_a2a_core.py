from unittest.mock import AsyncMock, MagicMock

import pytest

from fu7ur3pr00f.agents.specialists.a2a_interceptors import PreaAuthInterceptor
from fu7ur3pr00f.agents.specialists.a2a_proxy import A2AProxyAgent
from fu7ur3pr00f.container import container


@pytest.mark.unit
def test_prea_auth_interceptor():
    """Verify that the auth interceptor injects the API key."""
    # preserve/restore global setting to avoid leaking into other tests
    original_key = container.settings.a2a_agent_key
    container.settings.a2a_agent_key = "test-key-123"
    interceptor = PreaAuthInterceptor()

    mock_request = MagicMock()
    mock_request.headers = {}

    # We need mock for the other arguments required by intercept()
    mock_method = "message/send"
    mock_payload = {}
    mock_http_kwargs = {"headers": {}}
    mock_card = MagicMock()
    mock_context = MagicMock()

    # Using a sync wrapper for the async method for a simple unit test
    import asyncio

    try:
        result_payload, result_http_kwargs = asyncio.run(
            interceptor.intercept(
                mock_method, mock_payload, mock_http_kwargs, mock_card, mock_context
            )
        )

        assert result_http_kwargs["headers"]["X-API-Key"] == "test-key-123"
    finally:
        container.settings.a2a_agent_key = original_key


@pytest.mark.unit
@pytest.mark.parametrize("awaitable_return", [True, False])
def test_a2a_proxy_contribute(awaitable_return):
    """Verify that the A2A proxy correctly calls the remote client.

    Tests both shapes for client.send_message:
    - awaitable coroutine that returns an async iterator
    - direct (synchronous) function that returns an async iterator
    """
    # Importing client factory module later to allow test to monkeypatch connect

    mock_client = MagicMock()

    class AsyncIteratorMock:
        async def __aiter__(self):
            from a2a.types import Message, Part, Role, TextPart

            yield Message(
                parts=[Part(root=TextPart(text="Hello from PREA!"))],
                role=Role.agent,
                message_id="1",
                task_id="1",
            )

    async def mock_send_message_coroutine(*args, **kwargs):
        return AsyncIteratorMock()

    if awaitable_return:
        # send_message is an async function/coroutine that returns an async iterator
        mock_client.send_message = AsyncMock(side_effect=mock_send_message_coroutine)
    else:
        # send_message returns an async iterator directly (synchronous function)
        mock_client.send_message = MagicMock(return_value=AsyncIteratorMock())

    import a2a.client.client_factory as cf

    mock_connect = AsyncMock(return_value=mock_client)
    cf.ClientFactory.connect = mock_connect

    proxy = A2AProxyAgent()

    import asyncio

    result = asyncio.run(proxy._send_a2a_message("Test query", MagicMock()))

    assert result == "Hello from PREA!"
    cf.ClientFactory.connect.assert_called_once()
