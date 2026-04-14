from typing import Any

from a2a.client.middleware import ClientCallContext, ClientCallInterceptor
from a2a.types import AgentCard

from fu7ur3pr00f.config import settings


class PreaAuthInterceptor(ClientCallInterceptor):
    """Auth interceptor for PREA agent requiring X-API-Key."""

    async def intercept(
        self,
        method_name: str,
        request_payload: dict[str, Any],
        http_kwargs: dict[str, Any],
        agent_card: AgentCard | None,
        context: ClientCallContext | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Inject the A2A agent key into the request headers."""
        api_key = settings.a2a_agent_key
        if api_key:
            headers = http_kwargs.get("headers", {})
            headers["X-API-Key"] = api_key
            http_kwargs["headers"] = headers
        return request_payload, http_kwargs
